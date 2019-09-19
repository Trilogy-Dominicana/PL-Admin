#!/usr/bin/python
import sys
import getopt
from src.database import Database

def main(argv):
    """Main function to execute command line"""

    emethod = ''
    try:
        opts, arg = getopt.getopt(argv, "he:", ["emethod="])
    except getopt.GetoptError:
        # print('Something wrong with the args. type -h to see help ')
        sys.exit(2)


    for opt, arg in opts:
        if opt == '-h':
            print('Available opcions -e <method_name>\n')
            # help(rlFManager)
            sys.exit('0')
        elif opt in ("-e", "--emethod"):
            emethod = arg
        else:
            sys.exit()

    if emethod == 'run':
        db = Database()
        db.connect()
        print('Excecuting')
    else:
        print('No method reconaized')


if __name__ == "__main__":
    main(sys.argv[1:])
