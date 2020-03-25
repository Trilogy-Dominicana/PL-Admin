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

# parser.add_argument('integers', metavar='N', type=int, nargs='+', default=max, help='an integer for the accumulator')
# parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')


db = Database(displayInfo=True)
files = Files(displayInfo=True)

# Table for wc2db and db2wc methods
info = PrettyTable(["Object", "Type", "Path", "Status", "Info"])
info.align = 'l'

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
    if not db.metadataTableExist():
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

            info.add_row([objectName, objectType, fileObject, 'Created', 'New object created on local repository'])
            
            continue

        # Check if the object really has changes
        if metaMd5 == dbMd5:
            continue
        
        #TODO: Add validation to validate the object path.
        wcMd5 = files.fileMD5(objectPath)

        # The the object has changes in local file and not --force option continue
        if wcMd5 != metaMd5 and not force:
            info.add_row([objectName, objectType, objectPath, 'Fail', 'The object has changes in the local repository'])
            continue
        
        if not dry_run:
            fileObject = files.createObject(objectName, objectType, dbContent)
        
            # Update metadata table
            obj.update(object_path=fileObject, md5=dbMd5)
            updated = db.createOrUpdateMetadata(obj)
            
        info.add_row([objectName, objectType, objectPath, 'Updated', 'The object has been updated in local repository'])


    # Remove deleted objects
    for dObj in deletedObjs:
        object_name= dObj['object_name']
        object_type= dObj['object_type']
        object_path= dObj['object_path']

        if not dry_run:
            db.metadataDelete(object_name, object_type)
            
            if os.path.exists(object_path):
                os.remove(object_path)

        info.add_row([object_name, object_type, object_path, 'Removed', 'The object has been removed from the repository'])
    
    dba.close()
    print(info)


def wc2db(dry_run, force):
    # Turn off loader bar
    db = Database(displayInfo=False)

    if dry_run:
        utils.dryRun()

    if not db.metadataTableExist():
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
            if not dry_run:
                db.createReplaceObject(object_name=name, object_type=objectType, md5=obj["md5"], object_path=objPath)

            info.add_row([name, objectType, objPath, 'Created', 'This package was added to the database'])

            continue

        # If the object exist, then validate if the hash is the same, if so, that means that the object does not has chenges, so, continue.
        if obj["md5"] == mObject["md5"]:
            continue

        # Before taking the object to the database, it must be verified that the object has not changed in the db
        # To do this, we draw the source, generate the MD5 and compare it with that of the metadata
        dbmd5 = db.getObjSource(object_name=name, object_type=objectType, md5=True)

        # If the object has database changes, avoid sending to database.
        if dbmd5 != mObject["md5"] and not force:
            info.add_row([name, objectType, objPath, 'Fail', 'The object has changes in the database'])
            continue

        # If not dry-run, create the object and update metadata table
        if not dry_run:
            db.createReplaceObject(object_name=name, object_type=objectType, md5=obj["md5"], object_path=obj["object_path"])

        info.add_row([name, objectType, objPath, 'Updated', 'The object was updated successfully!'])

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

            info.add_row([object_name, object_type, object_path, 'Removed', 'The object has been removed in the database'])
            continue
        
        # IF exist on metadata table and exist on the repo, restored it.
        if not dbDroped and wcDroped:
            if not dry_run:
                db.createReplaceObject(object_name=object_name, object_type=object_type, md5=wcDroped["md5"], object_path=wcDroped["object_path"])

            info.add_row([object_name, object_type, object_path, 'Restored', 'The object has been restored in the database'])

    print(info, '\n')


def main():
    parser = argparse.ArgumentParser(
        prog="PL-Admin",
        usage="%(prog)s [action] options",
        description="Process some integers.",
    )

    parser.add_argument("action", action="store", help="Push the method name")
    parser.add_argument("--dry-run", "-d", action="store_true")
    parser.add_argument("--force", "-f", action="store_true")
    parser.add_argument("--quantity", "-q", default=1, type=int)
    parser.add_argument("--basic_pl", "-pl", default="n", type=str)
    parser.add_argument("--script", "-s", type=str, choices=("ddl", "dml"))
    parser.add_argument(
        "--schedule", "-p", type=str, default=datetime.now().strftime("%Y%m%d")
    )

    args = parser.parse_args()
    action = args.action
    dry_run = args.dry_run
    force = args.force
    script = args.script
    quantity = args.quantity
    basicPL = args.basic_pl
    schedule = args.schedule

    # Create schema
    if action == "init":
        db = Database(displayInfo=True)
        db.initMetadata()

    if action == "newSchema":
        db = Database(displayInfo=True)

        # The create Scheme method returns the packages that are still invalid
        invalids = db.createSchema(force)

        if len(invalids):
            print("\nThis objects are invalids:")
            for inv in invalids:
                print(inv["object_type"], inv["object_name"])
        else:
            print("Schema created successfully!")

    if action == "compile":
        # Try to compile invalid objects
        db = Database(displayInfo=True)
        result = db.compileObjects()

        if len(result):
            print("\nThis objects are invalids: \n")
        for inv in result:
            print(inv["object_type"], inv["object_name"])

    if action == "errors":
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

    if action == "db2wc":
        db2wc(dry_run, force)

    if action == "wc2db":
        wc2db(dry_run, force)

    if action == "invalids":
        db = Database(displayInfo=True)
        invalids = db.getObjects(status="INVALID")
        objLen = len(invalids)

        for obj in invalids:
            print(obj["object_type"], "-", obj["object_name"])

    if action == "watch":
        watch(files.pl_path)

    if action == "make" and script:
        scriptMigration = Migrations()

        migration = scriptMigration.createScript(
            fileType=script, quantity=quantity, basicPl=basicPL
        )

        for i in migration:
            print(colored("script %s created", "green") % i)

    if action == "migrate" and script:
        scriptMigration = Migrations()

        # scriptRevision = scriptMigration.checkPlaceScript()
        # print(scriptRevision)

        allmigrations = scriptMigration.migrate(typeFile=script)
        # print(allmigrations)
        for script in allmigrations:
            print(script)
            # print(
            #     scriptMigration.executeMigration(FullName=script)
            # )


if __name__ == "__main__":
    sys.exit(main())
