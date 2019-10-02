import cx_Oracle, os, re
from dotenv import load_dotenv
load_dotenv()

class Database():
    service_name = os.getenv("DB_SERVICE_NAME")
    user         = os.getenv("DB_USER")
    password     = os.getenv("DB_PASSWORD")
    host         = os.getenv("DB_HOST")
    port         = os.getenv("DB_PORT")

    def listInvalidObjects(self, status='', db=False):
        ''' List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        status (string): Valid values [VALID, INVALID].
        db (cx_Oracle) is an instance of cx_Oracle lib
        '''

        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        query = "SELECT * FROM all_objects WHERE object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW') AND owner = '%s'" % self.user

        # If re.match(r'VALID|INVALID', status):
        if ('INVALID' == status) or 'VALID' == status:
            query = query + " AND status = '%s'" % status
        
        result = cursor.execute(query)

        # Overriding rowfactory method to get the data in a dictionary
        result.rowfactory = self.makeDictFactory(result)

        # Fetching data from DB
        data = result.fetchall()

        # Close DB connection
        cursor.close()

        # If the connection was open on this method, close localy.
        if localClose:
            db.close()

        return data

    
    def executeScript(slef):
        ''' Función para crear (recompilar) paquetes, funciones y procedimientos '''
        # Just tu execute and script

    def dbConnect(self, sysDBA=False):
        """ 
        Encharge to connect to Oracle database

        Params:
        -------
        sysDBA (boolean): True of False
        """
        self.dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
        
        mode = False
        if sysDBA:
            mode = cx_Oracle.SYSDBA

        try:
            return cx_Oracle.connect(user=self.user, password=self.password, dsn=self.dsn, mode=mode, encoding="UTF-8")

        except Exception as e:
            content= 'DB Error: %s ' % (str(e)).strip()
            print(content)
            return content


    def makeDictFactory(self, cursor):
        ''' cx_Oracle library doesn't bring a simple way to convert a query result into a dictionary. '''
        columnNames = [d[0].lower() for d in cursor.description]
        def createRow(*args):
            return dict(zip(columnNames, args))

        return createRow
