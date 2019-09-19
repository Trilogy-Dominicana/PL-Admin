import cx_Oracle

class Database():
    def connect(self):
        '''Encharge to connect to Oracle database'''
        connection = cx_Oracle.connect("ROAM_LOADER_APP", "VWWecatgGuAfQRnu", "192.168.100.242/DBTARIF.OM.DO")
        return connection
 