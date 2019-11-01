#!/usr/local/bin/python
from __future__ import absolute_import
import sys, getopt, json, os, argparse, time

from datetime import datetime
from pladmin.database import Database 
from pladmin.files import Files

# parser.add_argument('integers', metavar='N', type=int, nargs='+', default=max, help='an integer for the accumulator')
# parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')


'''
TODO:
[] Funcionalidad para compilar solo el archivo en el qué se está trabajando.
[] Funcionalidad para compilar todos los archivos que cambiaron a partir del ultimo commit.
[] Funcionalidad para compilar las diferencias entre el repositorio local y el remoto (master)
'''
db = Database(displayInfo=True)
files = Files(displayInfo=True)

def watch(path_to_watch):
    ''' Watch the provided path for changes in any of it's subdirectories '''
    
    print("Watching " + path_to_watch)
    before = files.files_to_timestamp(path_to_watch)



    while 1:
        time.sleep (.5)
        after = files.files_to_timestamp(path_to_watch)

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
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('action', metavar='action', type=str, help='Push the method name')

    args = parser.parse_args()
    action = args.action
    
    # Update schema command
    if action == 'updateSchema':
        
        # Get files has changed and are uncomited
        localChanges = files.localChanges()
        
        # Get changes comparing local branch with remote master branch
        remoteChanges = files.remoteChanges()
        
        # Remove duplicated key
        changes = list(dict.fromkeys(localChanges + remoteChanges))

        # Concat the path to each files
        data = [files.pl_path + '/' + x for x in changes]

        if data:
            invalids = db.createReplaceObject(path=data)
        
        # If some objects are invalids, try to compile again
        # if len(invalids):
            # self.compileObj(invalids)


        # TODO List file removed and drop it from database


    # Create schema command
    if action == 'newSchema':
        invalids = db.createSchema()
        
        if len(invalids):
            print(invalids)
        else:
            print('Schema created successfully!')


    if action == 'compileInvalids':
        # Get invalid objects
        invalids = db.getObjects(status='INVALID')

        # Try to compile it 
        db.compileObj(invalids)

        result = db.getObjects(status='INVALID')
        print(result)


    if action == 'watch':
        watch(files.pl_path)


    if action == 'wc2db':
        ''' Override complete schema '''
        objs = files.listAllObjsFiles()
        db.createReplaceObject(objs)


    if action == 'test':
        print(files.remoteChanges())




if __name__ == '__main__':
    sys.exit(main())
