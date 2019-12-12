#!/usr/local/bin/python
from __future__ import absolute_import
import sys, getopt, json, os, argparse, time

from datetime import datetime
from pladmin.database import Database
from pladmin.files import Files
from pladmin.utils import utils

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
                print("%s has local changes, fail!" % objectPath)

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

    args = parser.parse_args()
    action = args.action
    dry_run = args.dry_run
    force = args.force
    # print(vars(args))

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

    if action == "updateSchema":
        """ Override complete schema """
        objs = files.listAllObjsFiles()
        db.createReplaceObject(objs)

    if action == "db2wc":
        db2wc(dry_run, force)
    
    # Push changes from local repository to db
    if action == "wc2db":
        print("Getting updating schema with database chagnes")
        db2wc(dry_run, force)

        # first, we need to add new files that comming from pull or added directly
        
        # second, remove deleted files

        # and then, validate 
        
        # Listing all objects on local repository
        local = files.listAllObjectFullData()

        # List all objects into database
        inDB = db.getObjects()
    
        for lc in local:
            print(lc)
            objectName = lc['object_name']
            objectType = lc['object_type']
            objectDdl = datetime.fromtimestamp(lc['last_ddl_time'])

            dbobj = utils.getObjectDict(objects=inDB, name=objectName, type=objectType)
            

            if not len(dbobj):
                print('Objecto nuevo de cajeta')
                continue

            dbTime = dbobj[0]['last_ddl_time']
            # dbHash = dbobj[0]['last_commit']
            
            # "CUANDO SE CREA EL ESQUEMA SE DEBE ACTUALIZAR LA FECHA DE MODIFICACION DEL ARCHIVO QUE SE INSERTA EN METADA PARA PODER VALIDAR LOS ARCHIVOS QUE CAMBIAR EN LA COPIA DE TRABAJO"
            if dbTime > objectDdl:
                print("El objecto tiene cambios en la base de datos, usar --force")

            if objectDdl > dbTime:
                print("REPLACE EXCUTED")
                # print(dbHash)

                # print(dbTime)
                # print('\n')
                # print(objectDdl)
                
            exit()


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

    if action == "createMetadata":

        # print(files.files_to_timestamp())
        # Getting up object type, if it's package, package body, view, procedure, etc.
        db.createMetaTable()
        data = db.getObjects(withPath=True)
        db.metadataInsert(data)


if __name__ == "__main__":
    sys.exit(main())
