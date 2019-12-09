#!/usr/local/bin/python
from __future__ import absolute_import
import sys, getopt, json, os, argparse, time

from datetime import datetime
from pladmin.database import Database
from pladmin.files import Files

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


def main():
    parser = argparse.ArgumentParser(
        prog="PL-Admin",
        usage="%(prog)s [action] options",
        description="Process some integers.",
    )

    parser.add_argument("action", action="store", help="Push the method name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")

    args = parser.parse_args()
    action = args.action
    dry_run = args.dry_run
    force = args.force
    # print(vars(args))

    # Update schema command
    if action == "updateSchema":

        # Get files has changed and are uncomited
        localChanges = files.localChanges()

        # Get changes comparing local branch with remote master branch
        remoteChanges = files.remoteChanges()

        # Remove duplicated key
        changes = list(dict.fromkeys(localChanges + remoteChanges))

        # Concat the path to each files
        data = [files.pl_path + "/" + x for x in changes]

        if data:
            invalids = db.createReplaceObject(path=data)
            # print(invalids)
        # If some objects are invalids, try to compile again
        # if len(invalids):
        db.compileObjects()

        # TODO List file removed and drop it from database

    # Create schema command
    if action == "newSchema":
        invalids = db.createSchema()

        if len(invalids):
            print("\nThis objects are invalids:")
            for inv in invalids:
                print(inv["object_name"], inv["object_type"])
        else:
            print("Schema created successfully!")

    if action == "compileInvalids":
        # Try to compile invalid objects
        result = db.compileObjects()

        print(result)

    if action == "watch":
        watch(files.pl_path)

    if action == "wc2db":
        """ Override complete schema """
        objs = files.listAllObjsFiles()
        db.createReplaceObject(objs)

    if action == "db2wc":
        """ Check objects that has been changed in the database and export it to working copy (local git repository)"""
        """ <TODO> Comprobar cuando hay un objecto nuevo y cuando fue eliminado """
        if dry_run:
            print(
                """
 _____  _______     __     _____  _    _ _   _ 
|  __ \|  __ \ \   / /    |  __ \| |  | | \ | |
| |  | | |__) \ \_/ /_____| |__) | |  | |  \| |
| |  | |  _  / \   /______|  _  /| |  | | . ` |
| |__| | | \ \  | |       | | \ \| |__| | |\  |
|_____/|_|  \_\ |_|       |_|  \_\\_____/|_| \_| 
-----------------------------------------------
         No change will take effect.
-----------------------------------------------\n """
            )

        uncommitedChanges = files.localChanges()
        if uncommitedChanges:
            print(
                "WARNING! You have uncommitted changes, commit it to avoid loss information"
            )
            # exit()
        deletedObjs = db.getDeletedObjects()

        # List all object with diferences
        dbObject = db.getObjectsDb2Wc()

        # List new objects
        newObjects = db.getNewObjects()

        # Check if object has change after commit store on the db
        for obj in newObjects + dbObject:
            lastCommit = obj["last_commit"]
            objectPath = obj["object_path"]
            objectName = obj["object_name"]
            objectType = obj["object_type"]
            objectTime = obj["last_ddl_time"]

            # Check if exist a hash commit before. This becouse new objects does not has commit hash
            if lastCommit:
                fi = files.diffByHash(lastCommit, True)

                # If the object has chadnges, do not export it
                # <TODO:> Agregar a option para poder hacer merge del archivo
                if any(objectPath in s for s in fi) and not force:
                    print("%s has local changed, fail!" % objectPath)
                    continue

            if not dry_run:
                objContend = db.getObjSource(objectName, objectType)
                fileObject = files.createObject(objectName, objectType, objContend)

                # Update metadata table
                obj.update(last_commit=files.head_commit, object_path=fileObject)
                updated = db.crateOrUpdateMetadata(obj)

            # This validation is to know if the object is new o not
            if not lastCommit and not objectPath:
                print("%s %s Added" % (objectType, objectName))
            else:
                print("%s exported successfully!" % objectPath)

        # Remove deleted objects
        for dObj in deletedObjs:
            objPath = dObj["object_path"]

            if not dry_run and os.path.exists(objPath):
                os.remove(objPath)

            print("%s Removed!" % objPath)

        # Now, remove objects from metadata
        if not dry_run:
            db.metadataDelete(deletedObjs)
        


    if action == "createMetadata":

        # print(files.files_to_timestamp())
        # Getting up object type, if it's package, package body, view, procedure, etc.
        db.createMetaTable()
        data = db.getObjects(withPath=True)
        db.metadataInsert(data)


if __name__ == "__main__":
    sys.exit(main())
