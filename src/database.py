import cx_Oracle, os, re, glob
from dotenv import load_dotenv
from src.files import Files as fileLib

fileLib = fileLib()
load_dotenv()

class Database():
    service_name = os.getenv("DB_SERVICE_NAME")
    user         = os.getenv("DB_USER")
    password     = os.getenv("DB_PASSWORD")
    host         = os.getenv("DB_HOST")
    port         = os.getenv("DB_PORT")


    def compileObj(self, obj=None, db=None):
        ''' Función para crear (recompilar) paquetes, funciones y procedimientos '''
        
        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()

        # List all files in on pending dir ({self.pending_files}) directory and push into {file} var
        path = os.path.join('plsql', 'packages', '*.pbk')
        files = glob.glob(path)
        
        for f in files:
            fname = fileLib.getFileName(f)

            opf = open(f, 'r')
            content = opf.read()
            opf.close()
            
            cursor.execute(content)
            data = self.getObjErrors(owner=self.user, objName=fname['name'], db=db)

            # db.commit() # The commit is not necessary

        if localClose:
            db.close()
            
        print(data)

        # print(content)
        # print(files)

    
    def getObjErrors(self, owner, objName, db=None):
        ''' Get object errors on execution time '''

        query = "SELECT * FROM all_errors WHERE owner = '%s' and NAME = '%s'" % (owner, objName)
        result = self.getData(query=query, db=db)
        
        return result


    def getObjStatus(self, status=None):
        # [] Se debe agregar a este metodo el porqué el objeto está invalido
        ''' 
        List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        status (string): Valid values [VALID, INVALID].
        db (cx_Oracle) is an instance of cx_Oracle lib.
        '''
        
        query = """
        SELECT     
            owner
            ,object_id
            ,object_name
            ,object_type
            ,status
            ,last_ddl_time
            ,created 
        FROM all_objects WHERE object_type in ('PACKAGE','PACKAGE BODY','FUNCTION','PROCEDURE', 'VIEW') AND owner = '%s'""" % self.user

        # If re.match(r'VALID|INVALID', status):
        if ('INVALID' == status) or 'VALID' == status:
            query = query + " AND status = '%s'" % status
        
        result = self.getData(query)
        
        return result


    def getData(self, query, db=None):
        ''' 
        List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        query (string): SQL query data.
        db (cx_Oracle) is an instance of cx_Oracle lib.
        '''

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        
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
