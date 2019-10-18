#!/usr/bin/python
import sys, getopt, json

# from dotenv import load_dotenv
from vivapl.database import Database
from vivapl.files import Files


def main(argv):
    ''' Main function to execute command line '''

    emethod = ''
    try:
        opts, arg = getopt.getopt(argv, "hie:", ["emethod="])
    except getopt.GetoptError:
        # print('Something wrong with the args. type -h to see help ')
        sys.exit(2)

    
    
    for opt, arg in opts:
        if opt in ('-i'):
            ''' List invalid packages on DB '''
            files = Files()
            db = Database()
            # con = db.dbConnect(asAdmin=True)
            
            # Create schemas
            # print(db.createSchema())
            
 
            # List invalid objects
            # print(db.getObjStatus(status='INVALID')[0])
            invalids = db.getObjStatus(status='INVALID')
            print(db.compileObj(invalids))
            
            # Get error, warnnings, info of a invalid package
            # print(db.getObjErrors('EBRADMIN', 'TX_CL_ENCUESTA'))
            
            # Get object path by type of db and nada
            # datos = files.findObjFileByType(objType='PACKAGE BODY', objectName='TX_CL_ENCUESTA')
            # print(datos)
            
            # Compiple an object list
            # datos = files.listAllObjsFiles()
            # data = []
            # invalids = db.getObjStatus(status='INVALID', withPath=True)
            # for v in invalids:
                # data.insert(0,v['path'])

            # print(invalids)
            # print(db.createReplaceObject(data))

            
        elif opt in ("-e", "--emethod"):
            emethod = arg
        else:
            print('Available opcions -e <method_name>\n')
            sys.exit('0')

if __name__ == "__main__": 
    main(sys.argv[1:])
