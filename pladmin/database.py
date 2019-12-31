import cx_Oracle, os, re, glob
from pladmin.files import Files as files
from datetime import datetime, date

files = files()


class Database:

    db_admin_user = os.getenv("DB_ADMIN_USER").upper()
    db_admin_password = os.getenv("DB_ADMIN_PASSWORD")
    db_default_table_space = os.getenv("DB_DEFAULT_TABLE_SPACE").upper()
    db_temp_table_space = os.getenv("DB_TEMP_TABLE_SPACE").upper()
    db_main_schema = os.getenv("DB_MAIN_SCHEMA").upper()
    service_name = os.getenv("DB_SERVICE_NAME")
    user = os.getenv("DB_USER").upper()
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    lastIntends = 0

    def __init__(self, displayInfo=False):
        self.types = files.objectsTypes().keys()
        self.extentions = files.objectsTypes().values()

        self.displayInfo = displayInfo
        files.displayInfo = displayInfo

    def createSchema(self):
        # To create users, give permission, etc. We need to connect with admin user using param sysDBA
        db = self.dbConnect(sysDBA=True)

        # Drop and create the user
        self.newUser(db=db)

        # Give grants to the user
        self.createGramtsTo(
            originSchema=self.db_main_schema, detinationSchema=self.user, db=db
        )

        # Create table of migrations
        self.createMetaTableScripts()

        # Create synonyms
        self.createSynonyms(
            originSchema=self.db_main_schema, detinationSchema=self.user, db=db,
        )

        # Create meta table
        self.createMetaTable()

        # Create o replace packages, views, functions and procedures (All elements in files.objectsTypes())
        data = files.listAllObjsFiles()
        self.createReplaceObject(path=data)

        # If some objects are invalids, try to compile
        invalids = self.compileObjects()

        # Getting up object type, if it's package, package body, view, procedure, etc.
        data = self.getObjects(withPath=True)
        self.metadataInsert(data)

        db.close()
        return invalids

    def createMetaTable(self, db=None):
        """
        Create metadata to manage meta information
        """
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        # Drop
        data = cursor.execute("DROP TABLE %s.PLADMIN_METADATA" % self.user)

        sql = (
            """CREATE TABLE %s.PLADMIN_METADATA(
                    object_name varchar2(30) not null,
                    object_type varchar2(18) not null,
                    object_path varchar2(255) not null,
                    last_commit varchar2(255) not null,
                    sync_date date not null,
                    last_ddl_time date not null,
                    primary key (object_name, object_type)
                )"""
            % self.user
        )

        data = cursor.execute(sql)

        if localClose:
            db.close()

        return data

    def metadataValidate(self, objectName, objectType, db=None):

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        sql = (
            "SELECT object_name FROM %s.PLADMIN_METADATA WHERE OBJECT_NAME = '%s' AND OBJECT_TYPE = '%s'"
            % (self.user, objectName, objectType)
        )
        data = cursor.execute(sql)
        obj = data.fetchone()

        cursor.close()
        if localClose:
            db.close()

        return obj

    def metadataInsert(self, data, db=None):
        """ Insert data into metadata table.
        
        Params: 
        data: list that contain and dict with the following keys: object_name, object_type, object_path, last_commit, last_ddl_time
        """

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        cursor = db.cursor()

        for obj in data:
            sql = (
                "INSERT INTO %s.PLADMIN_METADATA VALUES('%s', '%s', '%s', '%s', sysdate, TO_DATE('%s','RRRR/MM/DD HH24:MI:SS')) "
                % (
                    self.user,
                    obj["object_name"],
                    obj["object_type"],
                    obj["object_path"],
                    obj["last_commit"],
                    obj["last_ddl_time"],
                )
            )
            cursor.execute(sql)

        cursor.close()

        if localClose:
            db.commit()
            db.close()

    def metadataUpdate(self, data, db=None):

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        cursor = db.cursor()

        for obj in data:

            if len(obj["object_path"]):
                objectPath = "OBJECT_PATH= '%s', " % obj["object_path"]

            sql = """UPDATE %s.PLADMIN_METADATA SET %s LAST_COMMIT='%s', SYNC_DATE=SYSDATE, LAST_DDL_TIME=TO_DATE('%s','RRRR/MM/DD HH24:MI:SS') 
                WHERE object_name = '%s' and object_type = '%s' """ % (
                self.user,
                objectPath,
                obj["last_commit"],
                obj["last_ddl_time"],
                obj["object_name"],
                obj["object_type"],
            )
            cursor.execute(sql)

        cursor.close()
        if localClose:
            db.commit()
            db.close()

    def metadataDelete(self, data, db=None):

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        cursor = db.cursor()

        for obj in data:
            sql = (
                """DELETE FROM %s.PLADMIN_METADATA WHERE object_name = '%s' and object_type = '%s' """
                % (self.user, obj["object_name"], obj["object_type"])
            )
            cursor.execute(sql)

        cursor.close()

        if localClose:
            db.commit()
            db.close()

    def crateOrUpdateMetadata(self, data, db=None):
        """ Create or update data on metadata table """
        localClose = False

        if not db:
            db = self.dbConnect()
            localClose = True
        cursor = db.cursor()

        # Validate if the object exist on metadata table
        obj = self.metadataValidate(data["object_name"], data["object_type"], db)

        # If the object exist, update it
        if obj:
            self.metadataUpdate([data], db)
        else:
            self.metadataInsert([data], db)

        if localClose:
            db.commit()
            db.close()

        return obj

    def compileObjects(self, db=None):
        localClose = False
        data = []

        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        invalids = self.getObjects(status="INVALID")
        objLen = len(invalids)

        for obj in invalids:
            sql = "ALTER %s %s.%s COMPILE" % (
                obj["object_type"],
                obj["owner"],
                obj["object_name"],
            )

            # If package type is body, the sentence has to change
            if obj["object_type"] == "PACKAGE BODY":
                sql = "ALTER PACKAGE %s.%s COMPILE BODY" % (
                    obj["owner"],
                    obj["object_name"],
                )

            cursor.execute(sql)

        if objLen != self.lastIntends:
            self.lastIntends = objLen
            self.compileObjects(db=db)

        if localClose:
            db.commit()
            print("Commit on compile invalids")
            db.close()

        return invalids

    def createReplaceObject(self, path=None, db=None):
        """
        Create or Replace packges, views, procedures and functions 

        params:
        ------
        path (list): path routes of the object on the file system
        db (cx_Oracle.Connection): If you opened a db connection puth here please to avoid

        return (list) with errors if some package were an error
        """

        data = []
        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        # Prepare data for progress bar
        progressTotal = len(path)
        i = 0
        files.progress(
            i,
            progressTotal,
            status="LISTING PACKAGES...",
            title="CREATE OR REPLACE PACKAGES",
        )

        for f in path:
            fname, ftype = files.getFileName(f)

            # Only valid extencions sould be processed
            if not "." + ftype in self.extentions:
                continue

            # Display progress bar
            files.progress(i, progressTotal, "CRATEING %s" % fname)
            i += 1

            opf = open(f, "r")
            content = opf.read()
            opf.close()

            context = "CREATE OR REPLACE "
            if ftype == "vew":
                context = "CREATE OR REPLACE FORCE VIEW %s AS \n" % fname

            # Execute create or replace package
            cursor.execute(context + content)

            # # Update metadata table
            # updated = self.crateOrUpdateMetadata(
            #     objectName=obj["object_name"],
            #     objectType=obj["object_type"],
            #     objectPath=f,
            #     lastCommit=files.head_commit,
            #     lastDdlTime=obj["last_ddl_time"],
            #     db=db,
            # )

            # Check if the object has some errors
            # errors = self.getObjErrors(owner=self.user, objName=fname, db=db)
            # if errors:
            #     data.extend(errors)

        files.progress(
            i,
            progressTotal,
            status="OBJECTS HAS BEEN CREATED (ERRORS: %s)" % len(data),
            end=True,
        )

        if localClose:
            db.close()

        return data

    def getObjErrors(self, owner, objName, db=None):
        """ Get object errors on execution time """

        query = "SELECT * FROM dba_errors WHERE owner = '%s' and NAME = '%s'" % (
            owner,
            objName,
        )
        result = self.getData(query=query, db=db)

        return result

    def getObjects(
        self,
        objectTypes=None,
        objectName=None,
        status=None,
        withPath=False,
        fetchOne=None,
    ):
        # [] Se debe agregar a este metodo el porqué el objeto está invalido
        """
        List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        status (string): Valid values [VALID, INVALID].
        db (cx_Oracle) is an instance of cx_Oracle lib.

        return (dic) with all objects listed
        """

        types = "', '".join(self.types)
        if objectTypes:
            types = "', '".join([objectTypes])

        query = (
            """SELECT owner, object_id, object_name, object_type, status, last_ddl_time, created FROM dba_objects WHERE owner = '%s' AND object_type in ('%s')"""
            % (self.user, types)
        )

        if (status == "INVALID") or status == "VALID":
            query += " AND status = '%s'" % status

        if objectName:
            query += " AND object_name = '%s'" % objectName

        # Return a dic with the data
        result = self.getData(query=query, fetchOne=fetchOne)

        if len(result) and withPath:
            i = 0
            for obj in result:
                p = files.findObjFileByType(
                    objectType=obj["object_type"], objectName=obj["object_name"]
                )

                result[i].update({"object_path": p[0]})
                result[i].update({"last_commit": files.head_commit})
                i += 1

        return result

    def getObjectsDb2Wc(self):
        """ Get objects that has been changed after the last syncronization"""
        types = "', '".join(self.types)

        sql = """SELECT
                dbs.object_name
                ,dbs.object_type
                ,dbs.status
                ,dbs.last_ddl_time
                ,mt.last_ddl_time as meta_last_ddl_time
                ,mt.object_path
                ,mt.last_commit
            FROM dba_objects dbs
            INNER JOIN %s.PLADMIN_METADATA mt on dbs.object_name = mt.object_name and dbs.object_type = mt.object_type
            WHERE owner = '%s' 
                AND dbs.LAST_DDL_TIME <> mt.LAST_DDL_TIME
                AND dbs.object_type in ('%s') """ % (
            self.user,
            self.user,
            types,
        )

        result = self.getData(sql)

        return result

    def getNewObjects(self):
        """ Get Objects that exist on dba_object and does't exist on metadata table"""
        types = "', '".join(self.types)

        sql = """SELECT
                dbs.object_name
                ,dbs.object_type
                ,dbs.status
                ,dbs.last_ddl_time
                ,mt.last_ddl_time as meta_last_ddl_time
                ,mt.object_path
                ,mt.last_commit
            FROM dba_objects dbs
            LEFT JOIN %s.PLADMIN_METADATA mt on dbs.object_name = mt.object_name and dbs.object_type = mt.object_type
            WHERE owner = '%s' 
                AND mt.object_name IS NULL
                AND dbs.object_type in ('%s') """ % (
            self.user,
            self.user,
            types,
        )

        result = self.getData(sql)

        return result

    def getDeletedObjects(self):
        """ Get Objects that exist on pladmin_metadata table and does't exist on metadata dba_objects"""
        types = "', '".join(self.types)

        sql = """ SELECT a.*
        FROM %s.PLADMIN_METADATA a
        WHERE NOT EXISTS (SELECT 1 FROM dba_objects b WHERE b.object_name = a.object_name AND b.object_type = a.object_type AND b.owner='%s')
        AND a.object_type in ('%s') """ % (
            self.user,
            self.user,
            types,
        )

        sql = """SELECT 
                    mt.object_name 
                    ,mt.object_type
                    ,dbs.status
                    ,mt.last_ddl_time
                    ,mt.last_ddl_time as meta_last_ddl_time
                    ,mt.object_path
                    ,mt.last_commit 
                    FROM %s.PLADMIN_METADATA mt LEFT JOIN
                    dba_objects dbs ON dbs.object_name = mt.object_name AND dbs.object_type = mt.object_type AND dbs.owner ='%s'
                    AND dbs.object_type IN ('%s')
                    WHERE  dbs.object_name IS NULL""" % (
            self.user,
            self.user,
            types,
        )

        result = self.getData(sql)

        return result

    def createGramtsTo(self, originSchema, detinationSchema, db=None):
        cursor = db.cursor()
        i = 0
        permisions = [
            "GRANT CREATE PROCEDURE TO",
            "GRANT CREATE SEQUENCE TO",
            "GRANT CREATE TABLE TO",
            "GRANT CREATE VIEW TO",
            "GRANT CREATE TRIGGER TO",
            "GRANT EXECUTE ANY PROCEDURE TO",
            "GRANT SELECT ANY DICTIONARY TO",
            "GRANT CREATE SESSION TO",
            "GRANT SELECT ANY DICTIONARY TO",
            "GRANT EXECUTE ANY PROCEDURE TO",
            "GRANT EXECUTE ANY TYPE TO",
            "GRANT ALTER ANY TABLE TO",
            "GRANT ALTER ANY SEQUENCE TO",
            "GRANT UPDATE ANY TABLE TO",
            "GRANT DEBUG ANY PROCEDURE TO",
            "GRANT DEBUG CONNECT ANY to",
            "GRANT DELETE ANY TABLE TO",
            "GRANT ALTER ANY INDEX TO",
            "GRANT INSERT ANY TABLE TO",
            "GRANT READ ANY TABLE TO",
            "GRANT SELECT ANY TABLE TO",
            "GRANT SELECT ANY SEQUENCE TO",
            "GRANT UPDATE ON SYS.SOURCE$ TO",
            "GRANT EXECUTE ON SYS.DBMS_LOCK TO",
        ]

        # Prepare vars to progress bar
        progressTotal = len(permisions)
        files.progress(
            i,
            progressTotal,
            status="LISTING PERMISSIONS %s" % detinationSchema,
            title="GIVE GRANTS",
        )

        for p in permisions:
            # Write progress bar
            files.progress(i, progressTotal, status="GRANT TO %s " % detinationSchema)

            # Excute to db
            cursor.execute(p + " " + detinationSchema)

            i += 1

        # This is a special permission
        cursor.execute(
            "CREATE SYNONYM %s.FERIADOS FOR OMEGA.FERIADOS" % detinationSchema
        )
        files.progress(
            i, progressTotal, status="GRANT TO %s " % detinationSchema, end=True
        )

    def createSynonyms(self, originSchema, detinationSchema, db):
        """ Create synonyms types ('SEQUENCE', 'TABLE', 'TYPE') from originSchema to destinationSchema """

        cursor = db.cursor()
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
                    AND status = 'VALID' """ % (
            originSchema,
            detinationSchema,
        )

        synonyms = self.getData(query=sql, db=db)

        # Params to process bar
        progressTotal = len(synonyms)
        i = 0
        files.progress(i, progressTotal, "LISTING TABLES", title="CREATE SYNONYMS")

        for synon in synonyms:
            # Write progress bar
            files.progress(
                i,
                progressTotal,
                status="CREATE SYNONYM %s.%s"
                % (detinationSchema, synon["object_name"]),
            )

            sql = "CREATE SYNONYM %s.%s FOR %s.%s" % (
                detinationSchema,
                synon["object_name"],
                originSchema,
                synon["object_name"],
            )
            cursor.execute(sql)

            i += 1

        files.progress(i, progressTotal, status="SYNONYMS CREATED", end=True)
        cursor.close()

    def getData(self, query, params=None, fetchOne=None, db=None):
        """ 
        List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        query (string): SQL query data.
        db (cx_Oracle) is an instance of cx_Oracle lib.
        """

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
        if fetchOne:
            data = result.fetchone()
        else:
            data = result.fetchall()

        # Close DB connection
        cursor.close()

        # If the connection was open on this method, close localy.
        if localClose:
            db.close()

        return data

    def newUser(self, db):

        progressTotal = 3
        files.progress(
            count=1,
            total=progressTotal,
            status="VALIDATING...",
            title="CREATING " + self.user,
        )

        cursor = db.cursor()
        # Firts, we need to validate if the user exist
        sql = "SELECT COUNT(1) AS v_count FROM dba_users WHERE username = :db_user"
        cursor.execute(sql, {"db_user": self.user})

        # If user exist, drop it
        if cursor.fetchone()[0] > 0:
            files.progress(
                count=2, total=progressTotal, status="DROP USER %s" % self.user
            )
            cursor.execute("DROP USER %s CASCADE" % self.user)

        # Create the user
        files.progress(
            count=2, total=progressTotal, status="CREATING USER %s" % self.user
        )
        sql = (
            "CREATE USER %s IDENTIFIED BY %s DEFAULT TABLESPACE %s TEMPORARY TABLESPACE %s QUOTA UNLIMITED ON %s"
            % (
                self.user,
                self.password,
                self.db_default_table_space,
                self.db_temp_table_space,
                self.db_default_table_space,
            )
        )
        cursor.execute(sql)

        files.progress(
            count=3, total=progressTotal, status="USER %s CREATED" % self.user, end=True
        )

    def dbConnect(self, sysDBA=False):
        """
        Encharge to connect to Oracle database

        Params:
        -------
        sysDBA (boolean): True of False
        """

        self.dsn = cx_Oracle.makedsn(
            self.host, self.port, service_name=self.service_name
        )
        user = self.user
        password = self.password

        mode = 0
        if sysDBA:
            mode = cx_Oracle.SYSDBA
            user = self.db_admin_user
            password = self.db_admin_password

        return cx_Oracle.connect(
            user=user, password=password, dsn=self.dsn, mode=mode, encoding="UTF-8"
        )

    def makeDictFactory(self, cursor):
        """ cx_Oracle library doesn't bring a simple way to convert a query result into a dictionary. """
        columnNames = [d[0].lower() for d in cursor.description]

        def createRow(*args):
            return dict(zip(columnNames, args))

        return createRow

    def getObjSource(self, object_name, object_type):

        # Open db connection as a sysadmin
        db = self.dbConnect(sysDBA=True)

        sql = """ SELECT * FROM DBA_SOURCE
            WHERE OWNER = '%s' AND NAME = '%s' AND type = '%s' """ % (
            self.user,
            object_name,
            object_type,
        )

        if object_type == "VIEW":
            sql = """ SELECT * FROM DBA_VIEWS
            WHERE OWNER = '%s' AND VIEW_NAME = '%s' """ % (
                self.user,
                object_name,
            )

        result = self.getData(sql, db=db)
        text = ""

        for res in result:
            text += res["text"]

        return text
    
    def createMetaTableScripts(self, db=None):
        """
        Create metadata to manage meta information
        """
        localClose = False
        
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        # Drop
        data = cursor.execute("DROP TABLE %s.PLADMIN_MIGRATIONS" % self.user)

        sql = (
            """ CREATE TABLE %s.PLADMIN_MIGRATIONS (
                ID NUMBER GENERATED ALWAYS AS IDENTITY ( START WITH 1 INCREMENT BY 1 ) PRIMARY KEY,
                SCRIPT_NAME VARCHAR2(50) NOT NULL,
                STATUS VARCHAR(5), 
                CREATED_AT timestamp DEFAULT SYSDATE,
                FULL_PATH VARCHAR2(250),
                TYPE_SCRIPT VARCHAR2(6),
                OUTPUT VARCHAR2(4000),
                CONSTRAINT script_name_unique unique (script_name)
            )""" % self.user)

        data = cursor.execute(sql)

        if localClose:
            db.close()

        return data
    
    def createMigration(self, scriptName, fullPath, status, typeScript, output, db=None):
         
         localClose = False

         if not db:
            db = self.dbConnect()
            localClose = True
      
         cursor = db.cursor()
        

         migration = self.getScriptByName(scriptName=scriptName)
     
         if not migration:

             sql = ( """ 
                      INSERT INTO %s.PLADMIN_MIGRATIONS (SCRIPT_NAME, STATUS, FULL_PATH, TYPE_SCRIPT, OUTPUT) 
                      VALUES('%s', '%s', '%s', '%s', '%s')
                     
                      """
                    ) % (self.user, scriptName, status, fullPath, typeScript, output) 
             data = cursor.execute(sql)

         if localClose:
             db.commit()
             db.close()

    def getScriptByName(self, scriptName):
         sql = (
             "SELECT * FROM %s.PLADMIN_MIGRATIONS WHERE script_name='%s' "
             %(self.user, scriptName)
         )
         
         data = self.getData(query=sql, fetchOne=True)
         
         return data
    
    def getScriptDB(self, status='OK', date=None):

         if not date:
             date = datetime.now().strftime("%Y%m%d")
            
         sql = (
              
               """ SELECT * FROM %s.PLADMIN_MIGRATIONS 
                   WHERE status = '%s'
                   AND created_at >= TO_DATE ('%s', 'YYYYMMDD') 
               """
              
              )%(self.user, status, date)
         
         data = self.getData(query=sql)

         return data