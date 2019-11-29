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
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "action", metavar="action", type=str, help="Push the method name"
    )

    args = parser.parse_args()
    action = args.action

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
                print(inv['object_name'], inv['object_type'])
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

        # List all object with diferences
        objs = db.getObjectsDb2Wc()

        # Primero, validar que no hayan cambios sin comitear
        # La forma en la que veré si el archivo cambió realmente es ejecutando un  git diff <hash del commit en metadata> --name-only

        for obj in objs:
            objContend= db.getObjSource(obj['object_name'], obj['object_type'])
            files.createObject(obj['object_name'], obj['object_type'], objContend)
            break
        

        # Validate that 
        print(obj)
        exit(0)

        for obj in dbObj:
            # Get object path or check if file exist
            path = files.findObjFileByType(obj["object_type"], obj["object_name"])[0]

            # Get date object modification into db
            mb = obj["last_ddl_time"].timestamp()

            # If path exist, get modification date and validate that the date is less than database object
            if path:
                # Get file date modification
                mf = os.path.getmtime(path)

                if mf == mb or mf > mb:
                    continue
            else:
                path = files.createObject(obj["object_type"], obj["object_name"])
                print("Exporting %s to Working copy" % obj["object_name"])

            # print("%s object changed on the DB", obj["object_name"])
            data = db.getObjSource(obj["object_name"], obj["object_type"])
            print(" has been changed into db", obj["object_name"])

            with open(path, "wt") as f:
                f.truncate(0)
                f.write(data)
                f.write("\n")

            lastObj = db.getObjects(
                objectTypes=obj["object_type"], objectName=obj["object_name"]
            )

            # Update metadata table
            updated = self.crateOrUpdateMetadata(
                objectName=obj["object_name"],
                objectType=obj["object_type"],
                objectPath=path,
                lastCommit=files.repo.head.commit,
                lastDdlTime=obj["last_ddl_time"]
            )

            # files.updateModificationFileDate(path, lastObj[0]["last_ddl_time"])
            # print(path, datetime.fromtimestamp(mf).strftime('%Y-%m-%d %I:%M %p'))

        # print(obj)

    if action == "createMetadata":
        # print(files.files_to_timestamp())
        # Getting up object type, if it's package, package body, view, procedure, etc.
        db.createMetaTable()
        data = db.getObjects(withPath=True)
        db.metadataInsert(data)


if __name__ == "__main__":
    sys.exit(main())
