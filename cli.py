#!/usr/bin/python
import sys
import getopt
from src.database import Database

def main(argv):
    """Main function to execute command line"""

    emethod = ''
    try:
        opts, arg = getopt.getopt(argv, "hie:", ["emethod="])
    except getopt.GetoptError:
        # print('Something wrong with the args. type -h to see help ')
        sys.exit(2)

    print('Probando')
    
    for opt, arg in opts:
        if opt in ('-i'):
            ''' List invalid packages on DB'''
            print('Fetching packages... \n')
            db = Database()
            print(db.listInvalidObjects())
        elif opt in ("-e", "--emethod"):
            emethod = arg
        else:
            print('Available opcions -e <method_name>\n')
            sys.exit('0')

if __name__ == "__main__":
    main(sys.argv[1:])
