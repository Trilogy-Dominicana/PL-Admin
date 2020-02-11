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


"""
TODO:
[] Funcionalidad para compilar solo el archivo en el qué se está trabajando.
[] Funcionalidad para compilar todos los archivos que cambiaron a partir del ultimo commit.
[] Funcionalidad para compilar las diferencias entre el repositorio local y el remoto (master)
"""
db = Database(displayInfo=True)
files = Files(displayInfo=True)


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
            # if not os.path.exists(objPath):
            #     db.metadataDelete([dObj])

        print("%s Removed!" % objPath)


def wc2db(dry_run, force):
    # Turn off loader bar
    db = Database(displayInfo=False)

    if dry_run:
        utils.dryRun()

    # Get the last updated commit
    lastCommit = db.getLastObjectsHash()
    if lastCommit:
        wcObjects = files.diffByHashWithStatus(lastCommit["last_commit"])

    # List object that could have changed
    dbObjects = db.getObjectsDb2Wc()

    # look for pending objects or fail objects
    pending = [o["object_path"] for o in db.metadataPending()]

    # Local modifications (Pending and modified objects)
    objModified = list(set(wcObjects["modified"] + pending))

    for mObj in objModified:

        name, ext = files.getFileName(mObj)
        objectType = files.objectsTypes(inverted=True, objKey="." + ext)

        if not objectType:
            continue

        # Verify was modified on the db
        isObj = utils.getObjectDict(dbObjects, name, objectType)

        # Aquí debemos validar si el objecto en verdad tiene modificaciones, comparando el contenido del archivo con el qué está en la base de datos.
        # Here we have to validate if the object really has change on the db, making a diff between content file and content on the database.
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
                del objFailToUpdate["last_ddl_time"]
                db.createOrUpdateMetadata(objFailToUpdate)

            continue

        # If everything is ok, created or replace the object
        if not dry_run:
            db.createReplaceObject([mObj])

            # Update metadata table
            objToUpdate = db.getObjects(
                objectTypes=[objectType], objectName=name, fetchOne=True
            )

            objToUpdate.update(
                last_commit=files.head_commit, object_path=mObj, meta_status=0
            )
            updated = db.createOrUpdateMetadata(objToUpdate)

        print(mObj, "Exported successfully!")

    # Remove objects that has been deleted on local repository
    db.dropObject(wcObjects["deleted"], dry_run)


def wc2db2(dry_run, force):
    # Turn off loader bar
    db = Database(displayInfo=False)

    if dry_run:
        utils.dryRun()

    wcObjects = files.listAllObjectFullData(md5=True)
    for obj in wcObjects:
        name, ext = files.getFileName(obj['object_path'])
        objectType = files.objectsTypes(inverted=True, objKey="." + ext)
        dbmd5 = db.getObjSource(object_name=name, object_type=objectType, md5=True)
        
        # print(obj['object_path'] + '\n')
        # print(name, '.', ext)
        print(obj["md5"], ' - ', dbmd5)
        # print(dbmd5)
        exit()

    # Get the last updated commit
    # lastCommit = db.getLastObjectsHash()
    # if lastCommit:
    #     wcObjects = files.diffByHashWithStatus(lastCommit["last_commit"])

    # List object that could have changed
    dbObjects = db.getObjectsDb2Wc()

    # look for pending objects or fail objects
    pending = [o["object_path"] for o in db.metadataPending()]

    # Local modifications (Pending and modified objects)
    objModified = list(set(wcObjects["modified"] + pending))

    for mObj in objModified:

        name, ext = files.getFileName(mObj)
        objectType = files.objectsTypes(inverted=True, objKey="." + ext)

        if not objectType:
            continue

        # Verify was modified on the db
        isObj = utils.getObjectDict(dbObjects, name, objectType)

        # Aquí debemos validar si el objecto en verdad tiene modificaciones, comparando el contenido del archivo con el qué está en la base de datos.
        # Here we have to validate if the object really has change on the db, making a diff between content file and content on the database.
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
                del objFailToUpdate["last_ddl_time"]
                db.createOrUpdateMetadata(objFailToUpdate)

            continue

        # If everything is ok, created or replace the object
        if not dry_run:
            db.createReplaceObject([mObj])

            # Update metadata table
            objToUpdate = db.getObjects(
                objectTypes=[objectType], objectName=name, fetchOne=True
            )

            objToUpdate.update(
                last_commit=files.head_commit, object_path=mObj, meta_status=0
            )
            updated = db.createOrUpdateMetadata(objToUpdate)

        print(mObj, "Exported successfully!")

    # Remove objects that has been deleted on local repository
    db.dropObject(wcObjects["deleted"], dry_run)


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
    if action == "newSchema":
        db = Database(displayInfo=True)

        # The create Scheme method returns the packages that are still invalid
        invalids = db.createSchema()

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

    if action == "t":
        wc2db2(dry_run, force)
        # obj = files.listAllObjectFullData(md5=True)
        # for o in obj:
        #     print(o["md5"])

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
