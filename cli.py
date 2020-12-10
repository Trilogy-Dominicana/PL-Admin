#!/usr/local/bin/python
from __future__ import absolute_import
import sys, getopt, json, os, argparse, time, hashlib, re
from termcolor import colored
from prettytable import PrettyTable

from datetime import datetime, timedelta
from pladmin.database import Database
from pladmin.files import Files
from pladmin.utils import utils
from pladmin.migrations import Migrations


db = Database(displayInfo=True)
files = Files(displayInfo=True)

# Table for wc2db and db2wc methods
info = PrettyTable(["Object", "Type", "Path", "Action", "Status", "Info"])
infoScript = PrettyTable(["Name", "GroupID", "Type", "Status", "Output"])
info.align = infoScript.align = 'l'


def watch(path_to_watch):
    """ Watch the provided path for changes in any of it's subdirectories """

    print("Watching " + path_to_watch)
    before = files.files_to_timestamp()

    while 1:
        time.sleep(0.5)
        after = files.files_to_timestamp()

        added = [f for f in after.keys() if not f in before.keys()]
        removed = [f for f in before.keys() if not f in after.keys()]
        modified = []

        for f in before.keys():
            if not f in removed:
                if os.path.getmtime(f) != before.get(f):
                    modified.append(f)

        if modified:
            print("Modified: ", modified)
            db.createReplaceDbObject(path=modified)

        if added:
            print("Added: ", added)

        if removed:
            print("Removed: ", removed)

        before = after


def db2wc(dry_run, force):
    """ Check objects that has been changed in the database and export it to working copy (local git repository)"""
    if dry_run:
        utils.dryRun()

    # Create metadata table if not exist
    init = False
    if not db.tableExist(table_name='PLADMIN_METADATA'):
        print('Initializing PL-Admin... This acction can take a couple minutes!')
        if dry_run:
            exit()
            
        db.createMetaTable()
        init = True
    
    # Connect as SYS
    dba = db.dbConnect(sysDBA=True)

    deletedObjs = db.getDeletedObjects(db=dba)

    # List all object with diferences
    dbObject = db.getObjectsDb2Wc(db=dba)

    # List new objects
    newObjects = db.getNewObjects(db=dba)

    # Concat all objects
    allObjects = newObjects + dbObject


    # Check if object has change after commit store on the db
    for obj in allObjects:
        objectPath = obj["object_path"]
        objectName = obj["object_name"]
        objectType = obj["object_type"]
        objectTime = obj["last_ddl_time"]
        metaMd5 = obj["md5"]
        
        dbContent = db.getObjSource(objectName, objectType)
        dbMd5 = hashlib.md5(dbContent.encode()).hexdigest()

        # Check if is a new object
        if not objectPath and not metaMd5:
            fileObject="-"
            # Si es nuevo en la db, se debe validar que el archivo que se va a crear, no exista y si existe, retornar la ruta en la que se encuentra
            # Si no existe, entonces se genera el nuevo objeto
            if not dry_run:
                # Create the file with de object
                fileObject = files.createObject(objectName, objectType, dbContent)
                
                # Update metadata
                obj.update(object_path=fileObject, md5=dbMd5)
                updated = db.createOrUpdateMetadata(obj)

            info.add_row([objectName, objectType, fileObject, 'Create','Success', 'New object created on local repository'])
            
            continue

        # Check if the object really has changes
        if metaMd5 == dbMd5:
            continue
        
        #TODO: Add validation to validate the object path.
        wcMd5 = files.fileMD5(objectPath)

        # The the object has changes in local file and not --force option continue
        if wcMd5 != metaMd5 and not force:
            info.add_row([objectName, objectType, objectPath, 'Update', 'Fail', 'The object has changes in the local repository'])
            continue
        
        if not dry_run:
            fileObject = files.createObject(objectName, objectType, dbContent)
        
            # Update metadata table
            obj.update(object_path=fileObject, md5=dbMd5)
            updated = db.createOrUpdateMetadata(obj)
            
        info.add_row([objectName, objectType, objectPath, 'Update', 'Success', 'The object has been updated in local repository'])


    # Remove deleted objects
    for dObj in deletedObjs:
        object_name= dObj['object_name']
        object_type= dObj['object_type']
        object_path= dObj['object_path']

        if not dry_run:
            db.metadataDelete(object_name, object_type)
            
            if os.path.exists(object_path):
                os.remove(object_path)

        info.add_row([object_name, object_type, object_path, 'Remove', 'Success', 'The object has been removed from the repository'])
    
    dba.close()
    print(info)


def wc2db(dry_run, force):
    # Turn off loader bar
    db = Database(displayInfo=False)

    if dry_run:
        utils.dryRun()

    if not db.tableExist(table_name='PLADMIN_METADATA'):
        print("You have not initialized PL-Admin in the current schema '%s'" % db.user)
        print('Excute db2wc command to initialize PL-Admin and get all objects to you file system')
        exit()

    # Objects in the loca repo
    wcObjects = files.listAllObjectFullData(md5=True)

    # Object on the metadata table
    metaObjects = db.metadataAllObjects()

    # Object in the database
    dbObjects = db.getObjects()


    for obj in wcObjects:
        objPath = obj["object_path"]

        # Get the name, extention and type of the object
        name, ext, objectType = files.getFileName(objPath)

        # Get the object from metatada
        mObject = utils.getObjectDict(metaObjects, name, objectType)

        # If the object do not exist, that means that is a new object
        if not mObject:
            action = 'Created'
            status = 'Success'
            msg = 'This package was added to the database'
            if not dry_run:
                error, _ = db.createReplaceObject(object_name=name, object_type=objectType, md5=obj["md5"], object_path=objPath)
                if error:
                    status = 'Error'
                    action = 'Create'
                    msg = error[0]

            info.add_row([name, objectType, objPath, action, status, msg])
            continue

        # If the object exist, then validate if the hash is the same, if so, that means that the object does not has chenges, so continue.
        if obj["md5"] == mObject["md5"]:
            continue
            
        # Before update the object, we need to validate if the object exist on the database
        exitOnDb = utils.getObjectDict(dbObjects, name, objectType)
        if exitOnDb:
            # Before push the object to the database, we have to verify that the object has not changed in the db
            # To do this, we draw the source, generate the MD5 and compare it with that of the metadata
            dbmd5 = db.getObjSource(object_name=name, object_type=objectType, md5=True)

            # If the object has database changes, avoid sending to database.
            if dbmd5 != mObject["md5"] and not force:
                info.add_row([name, objectType, objPath, 'Update', 'Fail', 'The object has changes in the database'])
                continue

            # If not dry-run, replace the object and update metadata table
            action = 'Updated'
            status = 'Success'
            msg = 'The object was updated successfully!'
            if not dry_run:
                error, _ = db.createReplaceObject(object_name=name, object_type=objectType, md5=obj["md5"], object_path=obj["object_path"])
                if error:
                    action = 'Update'
                    status = 'Error'
                    msg = error[0]

            info.add_row([name, objectType, objPath, action, status, msg])


    for metaObj in metaObjects:
        object_name = metaObj["object_name"]
        object_type = metaObj["object_type"]
        object_path = metaObj["object_path"]
        
        # Check if the meta object exist on the repo objects.
        wcDroped = utils.getObjectDict(wcObjects, object_name, object_type)
        
        # Check if the object exist on the database
        dbDroped = utils.getObjectDict(dbObjects, object_name, object_type)

        # If the object in metadata does not exist in local repo that means that the object has been detele in the local repo
        if not wcDroped and dbDroped:
            if not dry_run:
                # Remove objects that has been deleted on local repository
                db.dropObject(object_type, object_name)

            info.add_row([object_name, object_type, object_path, 'Remove', 'Success', 'The object has been removed in the database'])
            continue
        
        # IF exist on metadata table and exist on the repo, restored it.
        if not dbDroped and wcDroped:
            action = 'Restored'
            status = 'Success'
            msg = 'The object has been restored in the database'
            if not dry_run:
                error, _ = db.createReplaceObject(object_name=object_name, object_type=object_type, md5=wcDroped["md5"], object_path=wcDroped["object_path"])
                if error:
                    action = 'Restore'
                    status = 'Error'
                    msg = error[0]

            info.add_row([object_name, object_type, object_path, action, status, msg])

    print(info, '\n')


def migrate(dry_run, force, name=None, types=None):
    path = '/plsql/scripts/pendigns/T00001/AS_T00001_01_WDELACRUZ2_20201204092326.sql'
    words = ['ANALYZE', 'AUDIT', 'ALTER', 'DATABASE', 'DROP', 'FOR', 'UPDATE', 'GRANT', 'LINK', 'LOCK', 'PUBLIC', 'TRUNCATE', 'RENAME', 'USER']
    
    files.checkWordsInFile(wordList=words, path=path)
    exit()

    if dry_run:
        utils.dryRun()

    failedGroups = []
    dba = db.dbConnect(sysDBA=True)

    # Connection to insert migrations in migration table
    dbm = db.dbConnect(sysDBA=True) 
    
    # Check if migration table exist
    if not db.tableExist(table_name='PLADMIN_MIGRATIONS', user=db.db_main_schema):
        # Create it if not exist
        db.scriptsMigrationTable()

    
    fScripts = files.listAllScriptsFiles()
    # Execute scripts by groups 
    for groupID, group in sorted(fScripts.items()):
        
        # Apply type filter
        if types:
            group = list(filter(lambda d: d['type'] in [types.upper()], group))

        # Filter by name
        if name:
            group = list(filter(lambda d: d['name'] in [name], group))

        # For each script in group
        for item in group:
            # Is the object group exist on failed group, avoid it. 
            if groupID in failedGroups and not force:
                item['status'] = 'HOLD'
                db.insertOrUpdateMigration(item, db=dbm)
                infoScript.add_row([item['name'], groupID, item['type'], item['status'], item['output']])
                continue
            
            # Before excute the script, we have to checkout if special keywords exist


            dbScript = db.getMigration(scriptName=item['name'], db=dba)
            if dbScript:
                if dbScript[3] == 'OK': continue
                item['status']= dbScript[3]
                item['output']= str(dbScript[4])

            if not dry_run:
                # Run the script. This return status (OK or FAIL) and output.
                item['status'], item['output'] = db.RunSqlScript(item['path'], db=dba)
            
                if item['status'] == 'FAIL':
                    failedGroups.append(groupID)
            
                # Update status on the
                insert = db.insertOrUpdateMigration(item, db=dbm)
            
            infoScript.add_row([item['name'], groupID, item['type'], item['status'], item['output']])
            # print(item)

        # Add new line to split group table
        infoScript.add_row(['', '', '', '', ''])

    # print(failedGroups)
    print(" << MIGRATIONS >> \n", infoScript)


    # Close dbm connection
    dbm.commit()
    dbm.close()
    dba.close()

def make(name):
    if not name:
        print(colored("Please, add the --name parameter to with the type of script, group and the order. e.g: pladmin make --name AS_T00495_01", 'red'))
        exit(0)

    content = utils.scriptExample()
    filaName = files.createEmptyScript(name=name, user=db.user, content=content)

    if filaName == '0001':
        print(colored("Please, make sure that you are using the correct way to script name. e.g: AS_T00495_01 or DS_RQX9945_01", 'red'))
        exit(0)
    
    if filaName == '0002':
        print(colored("The script already exist", 'red'))
        exit(0)

    print(colored("Script %s has been created", "green") % filaName)

def main():
    parser = argparse.ArgumentParser(
        prog="PL-Admin",
        usage="%(prog)s [action] arguments",
        description="You need to specify the action name (make, wc2db, db2wc, etc.)",
    )

    parser.add_argument(
        "action", 
        action="store",
        choices=("newSchema", "compile", "errors", "db2wc", "wc2db", "invalids", "make", "migrate"),
        help="You need to specify the action name (make, wc2db, db2wc, etc.)"
        )

    parser.add_argument("--name", "-n", action="store", help="Indate the name of your script ORDER_ISSUE_TYPE")
    parser.add_argument("--type", "-t", action="store", choices=("as", "ds"), help="AS: DDL script types and DS: DML scripts types")
    parser.add_argument("--dry-run", "-d", action="store_true")
    parser.add_argument("--force", "-f", action="store_true")


    args = parser.parse_args()
    action = args.action 
    dry_run = args.dry_run
    force = args.force
    types = args.type
    name = args.name

    # Create schema
    if action == "init":
        db = Database(displayInfo=True)
        db.initMetadata()

    elif action == "newSchema":
        db = Database(displayInfo=True)

        # The create Scheme method returns the packages that are still invalid
        invalids = db.createSchema(force)

        if len(invalids):
            print("\nThis objects are invalids:")
            for inv in invalids:
                print(inv["object_type"], inv["object_name"])
        else:
            print("Schema created successfully!")

    elif action == "compile":
        # Try to compile invalid objects
        db = Database(displayInfo=True)
        result = db.compileObjects()

        if len(result):
            print("\nThis objects are invalids: \n")
        for inv in result:
            print(inv["object_type"], inv["object_name"])

    elif action == "errors":
        db = Database(displayInfo=True)
        result = db.compileObjects()

        t = PrettyTable(["Name", "Type", "Line", "Text"])

        # Get package errors
        for r in result:
            errors = db.getObjErrors(
                owner=db.user,
                object_name=r["object_name"],
                object_type=r["object_type"],
            )

            for e in errors:
                t.add_row([e["name"], e["type"], e["line"], e["text"]])

        print(t)

    elif action == "db2wc":
        db2wc(dry_run, force)

    elif action == "wc2db":
        wc2db(dry_run, force)

    elif action == "invalids":
        db = Database(displayInfo=True)
        invalids = db.getObjects(status="INVALID")
        objLen = len(invalids)

        for obj in invalids:
            print(obj["object_type"], "-", obj["object_name"])

    elif action == "watch":
        watch(files.pl_path)

    elif action == "make":
        make(name)

    elif action == "migrate":
        migrate(dry_run, force, name, types)


    # if action == "make" and script:
    #     print(colored("script created", "green"))
    #     scriptMigration = Migrations()

    #     migration = scriptMigration.createScript(
    #         fileType=script, quantity=quantity, basicPl=basicPL
    #     )

    #     for i in migration:
    #         print(colored("script %s created", "green") % i)
 
    # if action == "migrate" and script:

    #     scriptMigration = Migrations()

    #     # scriptRevision = scriptMigration.checkPlaceScript()
    #     # print(scriptRevision)

    #     allmigrations = scriptMigration.migrate(typeFile=script)
     
    #     for script in allmigrations:
    #         print(scriptMigration.executeMigration(FullName=script))


if __name__ == "__main__":
    sys.exit(main())
