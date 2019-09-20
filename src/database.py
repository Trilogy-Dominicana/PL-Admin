import cx_Oracle, os
from dotenv import load_dotenv
load_dotenv()

class Database():
    def connect(self):
        '''Encharge to connect to Oracle database'''
        print('Entering to database')
        print(os.getenv("SERVICE_NAME"))
        connection = 'Conectado'
        # connection = cx_Oracle.connect("ROAM_LOADER_APP", "VWWecatgGuAfQRnu", "192.168.100.242/DBTARIF.OM.DO")
        return connection
 