import cx_Oracle, os
from dotenv import load_dotenv
load_dotenv()

class Database():
    def dbConnect(self):
        '''Encharge to connect to Oracle database'''

        service_name = os.getenv("DB_SERVICE_NAME")
        user         = os.getenv("DB_USER")
        password     = os.getenv("DB_PASSWORD")
        host         = os.getenv("DB_HOST")
        port         = os.getenv("DB_PORT")
        dsn          = cx_Oracle.makedsn(host, port, service_name=service_name)
        
        connection = ''

        try:
            connection = cx_Oracle.connect(user=user, password=password, dsn=dsn, mode=False, encoding="UTF-8")
            # connection = cx_Oracle.connect(user=user, password=password, dsn=dsn, mode=cx_Oracle.SYSDBA, encoding="UTF-8")
            # logger.info("Successfully connected as SYSDBA")
        except Exception as e:
            content= 'DB Error: %s ' % (str(e)).strip()
            print(content)
            return content
        
        return connection


    def listInvalidObjects(self, db=False):
        ''' Listing invalid Packages, Functions and Procedures '''
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()
        query = "SELECT * FROM all_objects WHERE status = 'VALID' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE')"

        result = cursor.execute(query)

        # Overriding rowfactory method to get the data in a dictionary
        result.rowfactory = self.makeDictFactory(result)

        data = result.fetchall()

        # Close DB connection
        cursor.close()

        # If the connection was open on this method, close localy.
        if localClose:
            db.close()

        return data


    def makeDictFactory(self, cursor):
        ''' cx-oracle library do not bring to us a simple way to make result query into a dictionary.'''
        columnNames = [d[0].lower() for d in cursor.description]
        def createRow(*args):
            return dict(zip(columnNames, args))

        return createRow
