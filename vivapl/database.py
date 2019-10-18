import cx_Oracle, os, re, glob
from dotenv import load_dotenv
from vivapl.files import Files as files

files = files()
load_dotenv()

class Database():

    db_admin_user          = os.getenv("DB_ADMIN_USER").upper()
    db_admin_password      = os.getenv("DB_ADMIN_PASSWORD")
    db_default_table_space = os.getenv("DB_DEFAULT_TABLE_SPACE").upper()
    db_temp_table_space    = os.getenv("DB_TEMP_TABLE_SPACE").upper()
    db_main_schema         = os.getenv("DB_MAIN_SCHEMA").upper()
    service_name           = os.getenv("DB_SERVICE_NAME")
    user                   = os.getenv("DB_USER").upper()
    password               = os.getenv("DB_PASSWORD")
    host                   = os.getenv("DB_HOST")
    port                   = os.getenv("DB_PORT")

    def createSchema(self):
        # To create users, give permission, etc. We need to connect with admin user using param asAdmin
        db      = self.dbConnect(sysDBA=True)
        cursor  = db.cursor()

        # Firts, we need to validate if the user exist COUNT(1)
        sql = "SELECT COUNT(1) AS v_count FROM dba_users WHERE username = :pldb_user"
        cursor.execute(sql, {'pldb_user': self.user})
        
        # Add parameter drop the user in case of 
        if cursor.fetchone()[0] > 0:
            print('DROP USER %s' % self.user)
            cursor.execute("DROP USER %s CASCADE" % self.user)

        print('CREATED USER %s' % self.user)
        sql = "CREATE USER %s IDENTIFIED BY %s DEFAULT TABLESPACE %s TEMPORARY TABLESPACE %s QUOTA UNLIMITED ON %s" % (
            self.user,
            self.password,
            self.db_default_table_space,
            self.db_temp_table_space,
            self.db_default_table_space
        )
        cursor.execute(sql)
        
        # Give grants to the user
        self.createGramtsTo(originSchema=self.db_main_schema, detinationSchema=self.user, db=db)

        # print("ACTUALIZANDO SINONIMOS")
        self.createSynonyms(originSchema=self.db_main_schema, detinationSchema=self.user, db=db)

        # print("COMPILAR PAQUETES DESDE EL REPOSITORIO A LA DB")
        data = files.listAllObjsFiles()
        self.createReplaceObject(data)
        
        # print("RECOMPILANDO")
        db.getObjStatus(status='INVALID')
        db.compileObj(invalids)


    def compileObj(self, objList, db=None):

        localClose = False
        data = []

        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        
        for obj in objList:
            sql = 'ALTER %s %s.%s COMPILE'%(obj['object_type'], obj['owner'], obj['object_name'])
            cursor.execute(sql)
            # data.extend(self.getObjErrors(owner=self.user, objName=fname, db=db))

        if localClose:
            db.close()

        return data


    def createReplaceObject(self, path=None, db=None):
        ''' Función para crear (recompilar) paquetes, funciones y procedimientos '''
        data = []

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        
        for f in path:
            fi = files.getFileName(f)
            fname = fi['name']
            ftype = fi['ext']

            opf = open(f, 'r')
            content = opf.read()
            opf.close()
            
            print('Compiling %s.%s' % (fname, ftype))

            context = 'CREATE OR REPLACE '
            if ftype == 'vew':
                context = 'CREATE OR REPLACE FORCE VIEW %s AS \n' % fname
            
            cursor.execute(context + content)
            data.extend(self.getObjErrors(owner=self.user, objName=fname, db=db))

            # db.commit() # The commit is not necessary

        if localClose:
            db.close()

        return data
    

    def getObjErrors(self, owner, objName, db=None):
        ''' Get object errors on execution time '''

        query = "SELECT * FROM all_errors WHERE owner = '%s' and NAME = '%s'" % (owner, objName)
        result = self.getData(query=query, db=db)
        
        return result


    def getObjStatus(self, status=None, withPath=False):
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

        i = 0
        if withPath: 
            for obj in result:
                p = files.findObjFileByType(objType=obj['object_type'], objectName=obj['object_name'])
                result[i].update({'path': p[0]})
                i = i + 1

        return result


    def createGramtsTo(self, originSchema, detinationSchema, db=None):
        
        cursor  = db.cursor()
        cursor.execute("GRANT CREATE PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE SEQUENCE TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE VIEW TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE TRIGGER TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ANY PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY DICTIONARY TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE SESSION TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY DICTIONARY TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ANY PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ANY TYPE TO %s" % detinationSchema)
        cursor.execute("GRANT ALTER ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT ALTER ANY SEQUENCE TO %s" % detinationSchema)
        cursor.execute("GRANT UPDATE ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT DEBUG ANY PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT DEBUG CONNECT ANY to %s" % detinationSchema)
        cursor.execute("GRANT DELETE ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT ALTER ANY INDEX TO %s" % detinationSchema)
        cursor.execute("GRANT INSERT ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT READ ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY SEQUENCE TO %s" % detinationSchema)

        cursor.execute("GRANT UPDATE ON SYS.SOURCE$ TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ON SYS.DBMS_LOCK TO %s" % detinationSchema)
        cursor.execute("CREATE SYNONYM %s.FERIADOS FOR OMEGA.FERIADOS" % detinationSchema)

        # Now, we hace to get 
        # sql = ''' SELECT oo.object_name, oo.object_type, oo.status
        #         FROM sys.dba_objects oo
        #         WHERE oo.owner=:origin_schema
        #         AND oo.object_type in ('SEQUENCE','TABLE','TYPE')
        #         AND oo.object_name not like 'SYS_PLSQL_%%'
        #         AND oo.object_name not like 'QTSF_CHAIN_%%'
        #         AND oo.status='VALID'
        #         AND oo.object_name not in (SELECT tp.table_name FROM dba_tab_privs tp where tp.grantee=:destination_schema AND owner=:origin_schema) '''
        
        # result = self.getData(sql, {'origin_schema': originSchema, 'destination_schema': detinationSchema })

        # for obj in result:
        #     sql = "GRANT ALL PRIVILEGES ON %s.%s TO %s" % (originSchema, obj['object_name'], detinationSchema)
        #     cursor.execute(sql)

        # cursor = db.close()


    def createSynonyms(self, originSchema, detinationSchema, db):
        """ Create synonyms types ('SEQUENCE', 'TABLE', 'TYPE') from originSchema to destinationSchema """

        cursor = db.cursor()
        sql = ''' SELECT oo.object_name, oo.object_type, oo.status
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
                    AND status = 'VALID' ''' % (originSchema, detinationSchema)

        synonyms = self.getData(query=sql, db=db)


        for synon in synonyms:
            sql = "CREATE SYNONYM %s.%s FOR %s.%s" % (detinationSchema, synon['object_name'], originSchema, synon['object_name'])
            print(sql)
            cursor.execute(sql)

        cursor.close()


    def getData(self, query, params=None, db=None):
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
        if not params:
            result = cursor.execute(query)
        else:
            result = cursor.execute(query, data)

        # Overriding rowfactory method to get the data in a dictionary
        result.rowfactory = self.makeDictFactory(result)

        # Fetching data from DB
        data = result.fetchall()

        # Close DB connection
        # cursor.close()

        # If the connection was open on this method, close localy.
        if localClose:
            db.close()

        return data


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
