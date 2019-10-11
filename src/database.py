import cx_Oracle, os, re, glob
from dotenv import load_dotenv
from src.files import Files as fileLib

fileLib = fileLib()
load_dotenv()

class Database():
    db_admin_user          = os.getenv("DB_ADMIN_USER")
    db_admin_password      = os.getenv("DB_ADMIN_PASSWORD")
    db_default_table_space = os.getenv("DB_DEFAULT_TABLE_SPACE")
    db_temp_table_space    = os.getenv("DB_TEMP_TABLE_SPACE")
    db_main_schema         = os.getenv("DB_MAIN_SCHEMA")
    
    service_name = os.getenv("DB_SERVICE_NAME")
    user         = os.getenv("DB_USER").upper()
    password     = os.getenv("DB_PASSWORD")
    host         = os.getenv("DB_HOST")
    port         = os.getenv("DB_PORT")


    def createReplaceObject(self, path=None, db=None):
        ''' Función para crear (recompilar) paquetes, funciones y procedimientos '''
        data = []

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        
        for f in path:
            fname = fileLib.getFileName(f)

            opf = open(f, 'r')
            content = opf.read()
            opf.close()
            
            cursor.execute('CREATE OR REPLACE ' + content)
            data.extend(self.getObjErrors(owner=self.user, objName=fname['name'], db=db))

            # db.commit() # The commit is not necessary

        if localClose:
            db.close()
            
        return data
    

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


    def createSchema(self):
        # To create users, give permission, etc. We need to connect with admin user using param asAdmin
        db      = self.dbConnect(asAdmin=True)
        cursor  = db.cursor()

        # Firts, we need to validate if the user exist COUNT(1)
        sql = "SELECT COUNT(1) AS v_count FROM dba_users WHERE username = :pldb_user"
        cursor.execute(sql, {'pldb_user': self.user})
        
        # Add parameter drop the user in case of 
        if cursor.fetchone()[0] > 0:
            print('DROP USER %s' % self.user)
            cursor.execute("DROP USER %s CASCADE" % self.user)

        # print("*CREATE SCHEMA")
        sql = "CREATE USER %s IDENTIFIED BY %s DEFAULT TABLESPACE %s TEMPORARY TABLESPACE %s QUOTA UNLIMITED ON %s" % (
            self.user, 
            self.password,
            self.db_default_table_space,
            self.db_temp_table_space, 
            self.db_default_table_space
        )
        cursor.execute(sql)

        # print("*GRANT ALL")
        self.schemaPermision(db, self.user)


        # print("ACTUALIZANDO SINONIMOS")
        synonyms = self.getSynonyms(mainSchema=self.db_main_schema, dbUser=self.user, db=db)


        self.updateSynonyms(synonyms=synonyms, originSchema=self.db_main_schema, detinationSchema=self.user, db=db)


        # print("COMPILAR PAQUETES DESDE EL REPOSITORIO A LA DB")
        # list(self.wc2db())
        
        print("RECOMPILANDO")
        # self.DBCompile()

    def updateSynonyms(self, synonyms, originSchema, detinationSchema, db):
        cursor = db.cursor()

        for synon in synonyms:
            # If we need to exclude some object
            # if object_name in excludes:
            #     continue
            sql = "CREATE SYNONYM %s.%s FOR %s.%s" % (detinationSchema, synon['object_name'], originSchema, synon['object_name'])

            print(sql)
            cursor.execute(sql)

        cursor.close()

    def getSynonyms(self, mainSchema, dbUser, db=None):
        ''' This method get synonyms type ('SEQUENCE', 'TABLE', 'TYPE') from owner and avoid '''

        sql = """ SELECT oo.object_name, oo.object_type, oo.status
                FROM sys.dba_objects oo
                WHERE     oo.owner = '%s'
                    AND oo.object_type IN ('SEQUENCE', 'TABLE', 'TYPE')
                    AND oo.object_name NOT LIKE 'SYS_PLSQL_%%'
                    AND oo.object_name NOT LIKE 'QTSF_CHAIN_%%'
                    AND oo.object_name <> 'METADATA_TABLE'
                    AND NOT EXISTS
                            (SELECT 1
                                FROM sys.dba_objects tob
                                WHERE     tob.owner = '%s'
                                    AND tob.object_name = oo.object_name)
                    AND status = 'VALID' """ % (mainSchema, dbUser)

        result = self.getData(sql, db)
       
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


    def schemaPermision(self, db, user):
        cursor  = db.cursor()
        
        cursor.execute("GRANT CREATE PROCEDURE TO %s" % user)
        cursor.execute("GRANT CREATE SEQUENCE TO %s" % user)
        cursor.execute("GRANT CREATE TABLE TO %s" % user)
        cursor.execute("GRANT CREATE VIEW TO %s" % user)
        cursor.execute("GRANT CREATE TRIGGER TO %s" % user)
        cursor.execute("GRANT EXECUTE ANY PROCEDURE TO %s" % user)
        cursor.execute("GRANT SELECT ANY DICTIONARY TO %s" % user)
        cursor.execute("GRANT CREATE SESSION TO %s" % user)
        
        cursor = db.cursor()


    def dbConnect(self, asAdmin=False, sysDBA=False):
        """
        Encharge to connect to Oracle database

        Params:
        -------
        sysDBA (boolean): True of False
        """
        self.dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
        user=self.user
        password=self.password

        mode = False
        if sysDBA:
            mode = cx_Oracle.SYSDBA

        if asAdmin:
            user=self.db_admin_user
            password=self.db_admin_password

        try:
            return cx_Oracle.connect(user=user, password=password, dsn=self.dsn, mode=mode, encoding="UTF-8")
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
