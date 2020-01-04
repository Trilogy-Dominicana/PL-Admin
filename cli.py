#!/usr/local/bin/python
from __future__ import absolute_import
import sys, getopt, json, os, argparse, time, hashlib, re

from datetime import datetime, timedelta
from pladmin.database import Database
from pladmin.files import Files
from pladmin.utils import utils
from pladmin.migrations import Migrations

# parser.add_argument('integers', metavar='N', type=int, nargs='+', default=max, help='an integer for the accumulator')
# parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')


"""
TODO:
[] Funcionalidad para compilar solo el archivo en el qué se está trabajando.
[] Funcionalidad para compilar todos los archivos que cambiaron a partir del ultimo commit.
[] Funcionalidad para compilar las diferencias entre el repositorio local y el remoto (master)
"""
db = Database(displayInfo=True)
files = Files(displayInfo=True)


# utils = Utils()


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
            db.createReplaceObject(path=modified)

        if added:
            print("Added: ", added)

        if removed:
            print("Removed: ", removed)

        before = after


def db2wc(dry_run, force):
    """ Check objects that has been changed in the database and export it to working copy (local git repository)"""
    if dry_run:
        utils.dryRun()

    if files.localChanges():
        print(
            "WARNING! You have uncommitted changes, commit it to avoid loss information"
        )
    deletedObjs = db.getDeletedObjects()

    # List all object with diferences
    dbObject = db.getObjectsDb2Wc()

    # List new objects
    newObjects = db.getNewObjects()

    # Concat all objects
    allObjects = newObjects + dbObject

    # Check if object has change after commit store on the db
    for obj in allObjects:
        lastCommit = obj["last_commit"]
        objectPath = obj["object_path"]
        objectName = obj["object_name"]
        objectType = obj["object_type"]
        objectTime = obj["last_ddl_time"]

        # Check if exist a hash commit before. This becouse new objects does not has commit hash
        if lastCommit:
            fi = files.diffByHash(lastCommit, True)

            # <TODO:> Agregar a option para poder hacer merge del archivo
            # If the object has chadnges, do not export it
            if any(objectPath in s for s in fi) and not force:
                print("%s has local changes, fail!" % objectPath)
                continue

        if not dry_run:
            objContend = db.getObjSource(objectName, objectType)
            fileObject = files.createObject(objectName, objectType, objContend)

            # Update metadata table
            obj.update(last_commit=files.head_commit, object_path=fileObject)
            updated = db.createOrUpdateMetadata(obj)

        # This validation is to know if the object is new o not
        if not lastCommit and not objectPath:
            print("%s %s Added" % (objectType, objectName))
        else:
            print("%s Created successfully!" % objectPath)

    # Remove deleted objects
    for dObj in deletedObjs:
        objPath = dObj["object_path"]

        if not dry_run and os.path.exists(objPath):
            os.remove(objPath)

            # If the file has been removed, drop it in the medatada table
            if not os.path.exists(objPath):
                db.metadataDelete([dObj])

        print("%s Removed!" % objPath)


def main():
    parser = argparse.ArgumentParser(
        prog="PL-Admin",
        usage="%(prog)s [action] options",
        description="Process some integers.",
    )

    parser.add_argument("action", action="store", help="Push the method name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--quantity", "-q", default=1, type=int)
    parser.add_argument("--basic_pl", "-pl", default='n', type=str)
    parser.add_argument("--script", "-s", type=str, choices=('as', 'ds'))
    parser.add_argument("--schedule", "-p", type=str, default=datetime.now().strftime("%Y%m%d"))
  
    args     = parser.parse_args()
    action   = args.action
    dry_run  = args.dry_run
    force    = args.force
    script   = args.script
    quantity = args.quantity
    basic_pl = args.basic_pl
    schedule = args.schedule

    # Create schema
    if action == "newSchema":
        invalids = db.createSchema()

        if len(invalids):
            print("\nThis objects are invalids:")
            for inv in invalids:
                print(inv["object_name"], inv["object_type"])
        else:
            print("Schema created successfully!")

    if action == "compile":
        # Try to compile invalid objects
        db = Database(displayInfo=True)
        result = db.compileObjects()

        print(result)

    if action == "db2wc":
        db2wc(dry_run, force)

    # Push changes from local repository to db
    if action == "wc2db":
        # Turn off bar loader
        db = Database(displayInfo=False)

        if dry_run:
            utils.dryRun()

        # Get the last updated commit
        lastCommit = db.getLastObjectsHash()
        if lastCommit:
            wcObjects = files.diffByHashWithStatus(lastCommit["last_commit"])

        # List object that could have changed
        dbObjects = db.getObjectsDb2Wc()

        # look for pendding objects or fail objects
        pendding = [o['object_path'] for o in db.metadataPendding()]

        # Local modifications
        objModified = list(set(wcObjects["modified"] + pendding))


        for mObj in objModified:

            name, ext = files.getFileName(mObj)
            objectType = files.objectsTypes(inverted=True, objKey="." + ext)

            # Verify was modified on the db
            isObj = utils.getObjectDict(dbObjects, name, objectType)
            # print(mObj)
            # exit()

            # Aquí debemos validar si el objecto en verdad tiene modificaciones, comparando el contenido del archivo la base de datos.
            # print(mObj)
            if isObj and not force:
                # objContend = db.getObjSource(name, objectType).encode("utf-8")
                # f = open(mObj, "rb")
                # fcontent = f.read()

                # print(hashlib.md5(objContend).hexdigest())
                # print(hashlib.md5(fcontent).hexdigest())
                # print(objContend)
                # f.close()
                # exit()

                # Read file and compered changes

                
                print(mObj, "Has changes in the database, Fail!")
                if not dry_run:
                    objFailToUpdate = db.getObjects(
                        objectTypes=[objectType], objectName=name, fetchOne=True
                    )

                    objFailToUpdate.update(meta_status=1)
                    del objFailToUpdate['last_ddl_time']
                    db.createOrUpdateMetadata(objFailToUpdate)

                continue

            # If everything ok, created or replace the object
            print(mObj, "Exported successfully!")
            if not dry_run:
                db.createReplaceObject([mObj])

                # Update metadata table
                objToUpdate = db.getObjects(
                    objectTypes=[objectType], objectName=name, fetchOne=True
                )

                objToUpdate.update(last_commit=files.head_commit, object_path=mObj, meta_status=0)
                updated = db.createOrUpdateMetadata(objToUpdate)

        # ¿Que pasa si se hace un wc2db y no se le hace commit a esos cambios?
        # TODO List file removed and drop it from database

    if action == "watch":
        watch(files.pl_path)
    
    if schedule:

        isValidDate = re.search(r"^(\d{4}[-]\d{2}[-]\d{2})|(\d{8,8})$", schedule)
        if not isValidDate:
            print('this command only accept dates in this format 0000-00-00 | 20001102')
            return False

        scriptSchedule = schedule.replace("-","")
        formatSchedule = datetime(year=int(scriptSchedule[:4]), month=int(scriptSchedule[4:6]), day=int(scriptSchedule[6::]))
        
        if formatSchedule.strftime('%Y%m%d') < datetime.now().strftime('%Y%m%d') or formatSchedule > (datetime.now() + timedelta(days=15)):
            print('the scheduling date of a script must be greater than or equal to today and should only be scheduled 15 days ahead')
            return False

        folderSchedule = "%s%s%s%s%s%s" % ("/", schedule[:4], "/", schedule[4:6], "/", schedule[6:])

        if action == "make" and script:
            scriptMigration = Migrations(folderSchedule=folderSchedule)

            migration = scriptMigration.createScript(
             fileType=script, quantity=quantity, basicPl=basic_pl
            )

            print(migration)
        
        if action == "migrate" and script:
            structureFolder = datetime.now().strftime('/%Y/%m/%d')
            scriptMigration = Migrations(folderSchedule=structureFolder)

            scriptRevision = scriptMigration.checkPlaceScript()
            print(scriptRevision)

            executeMigration = scriptMigration.migrate(type_files=script)
            print(executeMigration)



if __name__ == "__main__":
    sys.exit(main())
