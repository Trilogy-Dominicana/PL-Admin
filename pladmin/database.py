import cx_Oracle, os, re, glob, hashlib

from pladmin.files import Files as files


from datetime import datetime, date
from dotenv import load_dotenv

files = files()


class Database:
    lastIntends = 0

    def __init__(self, displayInfo=False):

        if not os.path.exists(files.db_cnfpath):
            print(
                "Database config file does not exist. Please, copy .env.sample file to your PL/SQL code path with new name as .env, change the params and try again"
            )
            exit()

        try:
            # Load database config
            load_dotenv(files.db_cnfpath)

            self.db_admin_user = os.getenv("DB_ADMIN_USER").upper()
            self.db_admin_password = os.getenv("DB_ADMIN_PASSWORD")
            self.db_default_table_space = os.getenv("DB_DEFAULT_TABLE_SPACE").upper()
            self.db_temp_table_space = os.getenv("DB_TEMP_TABLE_SPACE").upper()
            self.db_main_schema = os.getenv("DB_MAIN_SCHEMA").upper()
            self.service_name = os.getenv("DB_SERVICE_NAME")
            self.user = os.getenv("DB_USER").upper()
            self.password = os.getenv("DB_PASSWORD")
            self.host = os.getenv("DB_HOST")
            self.port = os.getenv("DB_PORT")

        except Exception as e:
            print("Make sure you have all params setup on .env file")

        self.types = files.objectsTypes().keys()
        self.extentions = files.objectsTypes().values()

        self.displayInfo = displayInfo
        files.displayInfo = self.displayInfo

    def createSchema(self, force=False):
        # To create users, give permission, etc. We need to connect with admin user using param sysDBA
        db = self.dbConnect(sysDBA=True)

        # Drop and create the user
        user = self.newUser(db=db, force=force)

        if not user:
            print(
                "\n The user %s already exist, use --force option override the schema"
                % self.user
            )
            exit()

        # Give grants to the user
        self.createGramtsTo(
            originSchema=self.db_main_schema, detinationSchema=self.user, db=db
        )

        # Create table of migrations
        # self.createMetaTableScripts()

        # Create synonyms
        self.createSynonyms(
            originSchema=self.db_main_schema, detinationSchema=self.user, db=db
        )

        # Close SYS admin db connection
        db.close()

        # Create meta table
        self.createMetaTable()

        # Create o replace packages, views, functions and procedures (All elements in files.objectsTypes())
        data = files.listAllObjsFiles()
        self.createReplaceDbObject(path=data, showInfo=True)

        # If some objects are invalids, try to compile
        invalids = self.compileObjects()

        # Getting up object type, if it's package, package body, view, procedure, etc.
        data = self.getObjects(withPath=True)
        self.metadataInsert(data)

        return invalids

    def tableExist(self, table_name, user=False):
        """ Validate if a table exist"""
        if not user:
            user = self.user
            
        sql = (
            "SELECT * FROM DBA_TABLES WHERE TABLESPACE_NAME = '%s' AND TABLE_NAME = '%s' AND owner = '%s'"
            % (self.db_default_table_space, table_name, user)
        )
        metatable = self.getData(query=sql, fetchOne=True)

        if metatable:
            return True
        
        return False

    def createMetaTable(self, db=None):
        """
        Create metadata table to manage meta information
        """
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        # Drop
        try:
            cursor.execute("DROP TABLE %s.PLADMIN_METADATA" % self.user)
        except:
            pass

        sql = (
            """CREATE TABLE %s.PLADMIN_METADATA(
                    object_name varchar2(100) not null,
                    object_type varchar2(18) not null,
                    object_path varchar2(255) not null,
                    md5 varchar2(32) not null,
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

    def metadataInsert(self, data, md5=False, db=None):
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
            md5 = files.fileMD5(obj["object_path"])

            sql = (
                "INSERT INTO %s.PLADMIN_METADATA VALUES('%s', '%s', '%s','%s', sysdate, TO_DATE('%s','RRRR/MM/DD HH24:MI:SS'))"
                % (
                    self.user,
                    obj["object_name"],
                    obj["object_type"],
                    obj["object_path"],
                    md5,
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
            objectPath = ""
            if "object_path" in obj:
                objectPath = "OBJECT_PATH= '%s', " % obj["object_path"]

            lastDdlTime = ""
            if "last_ddl_time" in obj:
                lastDdlTime = (
                    "LAST_DDL_TIME=TO_DATE('%s','RRRR/MM/DD HH24:MI:SS'), "
                    % obj["last_ddl_time"]
                )

            md5 = ""
            if "md5" in obj:
                md5 = "MD5='%s', " % obj["md5"]

            sql = """UPDATE %s.PLADMIN_METADATA SET %s %s %s SYNC_DATE=SYSDATE 
                WHERE object_name = '%s' and object_type = '%s' """ % (
                self.user,
                objectPath,
                lastDdlTime,
                md5,
                obj["object_name"],
                obj["object_type"],
            )

            cursor.execute(sql)

        # cursor.close()
        if localClose:
            db.commit()
            db.close()

    def metadataDelete(self, object_type, object_name, db=None):

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        sql = (
            """DELETE FROM %s.PLADMIN_METADATA WHERE object_name = '%s' AND object_type = '%s' """
            % (self.user, object_type, object_name)
        )

        try:
            cursor.execute(sql)
        except Exception as e:
            print(e)
            pass

        if localClose:
            db.commit()
            db.close()

    def metadataAllObjects(self):
        """ Get all data from metadata"""

        query = "SELECT * FROM %s.pladmin_metadata" % self.user
        result = self.getData(query=query)

        return result

    def createOrUpdateMetadata(self, data, db=None):
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

            try:
                cursor.execute(sql)
            except Exception as e:
                print('Error on compile %s ' % obj["object_name"], e)
                pass

        if objLen != self.lastIntends:
            self.lastIntends = objLen
            self.compileObjects(db=db)

        if localClose:
            db.commit()
            db.close()

        return invalids

    def createReplaceObject(self, object_name, object_type, md5, object_path):
        """ Create or replace object and update metadata table at the same time """

        _, error = self.createReplaceDbObject([object_path])
        
        if error:
            return error, _

        # Get the new object that has been created with his last_ddl_time
        newObject = self.getObjects(
            objectTypes=[object_type], objectName=object_name, fetchOne=True
        )

        if not newObject:
            return 'ERROR CREATING OBJECT %s' % object_name

        newObject.update(object_path=object_path, md5=md5)

        # Update metadata table
        updated = self.createOrUpdateMetadata(newObject)

        return error, updated

    def dropDbObjects(self, object_type, object_name, db=None):
        """
        Drop packges, views, procedures or functions

        params:
        ------
        db (cx_Oracle.Connection): If you opened a db connection puth here please to avoid

        return (list) with errors if some package were an error
        """

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        sql = "DROP %s %s.%s" % (object_type, self.user, object_name)

        if object_type == "VIEW":
            sql = "DROP VIEW %s" % object_name

        # Execute sql statement
        try:
            cursor.execute(sql)
        except:
            pass

        if localClose:
            db.close()

    def createReplaceDbObject(self, path=None, db=None, showInfo=False):
        """
        Creates or Replaces packges, views, procedures and functions.

        params:
        ------
        path (list): path routes of the object on the file system
        db (cx_Oracle.Connection): If you opened a db connection puth here please to avoid

        return (list) with errors if some package were an error
        """

        success = []
        errors = []
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
            fname, ftype, objectType = files.getFileName(f)
            # Only valid extencions sould be processed
            if not "." + ftype in self.extentions:
                continue

            # Display progress bar
            files.progress(i, progressTotal, "CREATING %s" % fname)
            i += 1

            opf = open(f, "r")
            content = opf.read()
            opf.close()

            context = "CREATE OR REPLACE "
            if ftype == "vw":
                context = "CREATE OR REPLACE FORCE VIEW %s AS \n" % fname

            # Execute create or replace package
            try:
                cursor.execute(context + content)
                success.append(fname)
            except Exception as e:
                errors.append(e)
                if showInfo:
                    print(e)
                pass

        files.progress(
            i,
            progressTotal,
            status="OBJECTS HAS BEEN CREATED (ERRORS: %s)" % len(errors),
            end=True,
        )

        if localClose:
            db.close()

        return success, errors

    def getObjErrors(self, owner, object_name, object_type, db=None):
        """ Get object errors on execution time """

        query = (
            "SELECT * FROM dba_errors WHERE owner = '%s' and NAME = '%s' and TYPE = '%s'"
            % (owner, object_name, object_type)
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
        db=None
    ):
        """
        List Packages, Functions and Procedures and Views
        
        Params:
        ------
        status (string): Valid values [VALID, INVALID].
        objectTypes (list): List of object type that you want [PACKAGE, FUNCTION, PROCEDURE]
        withPath (Boolean): [True] if you want to include the path of the object

        return (dic) with all objects listed
        """

        types = "', '".join(self.types)
        if objectTypes:
            types = "', '".join(objectTypes)

        query = (
            """SELECT owner, object_id, object_name, object_type, status, last_ddl_time, created FROM dba_objects WHERE owner = '%s' AND object_type in ('%s')"""
            % (self.user, types)
        )

        if (status == "INVALID") or status == "VALID":
            query += " AND status = '%s'" % status

        if objectName:
            query += " AND object_name = '%s'" % objectName

        # Return a dic with the data
        result = self.getData(query=query, fetchOne=fetchOne, db=db)

        if fetchOne:
            return result

        if len(result) and withPath:
            for obj in result:

                p = files.findObjFileByType(
                    objectType=obj["object_type"], objectName=obj["object_name"]
                )

                obj.update({"object_path": ''})

                if len(p):
                    obj.update({"object_path": p[0]})

        return result

    def getObjectsDb2Wc(self, db=None):
        """ Get objects that has been changed after the last syncronization"""
        types = "', '".join(self.types)

        sql = """SELECT
                dbs.object_name
                ,dbs.object_type
                ,dbs.status
                ,dbs.last_ddl_time
                ,mt.last_ddl_time as meta_last_ddl_time
                ,mt.object_path
                ,mt.md5
            FROM dba_objects dbs
            INNER JOIN %s.PLADMIN_METADATA mt on dbs.object_name = mt.object_name and dbs.object_type = mt.object_type
            WHERE owner = '%s' 
                AND dbs.LAST_DDL_TIME <> mt.LAST_DDL_TIME
                AND dbs.object_type in ('%s') """ % (
            self.user,
            self.user,
            types,
        )

        result = self.getData(sql, db=db)

        return result

    def getNewObjects(self, db=None):
        """ Get Objects that exist on dba_object and does't exist on metadata table"""
        types = "', '".join(self.types)

        sql = """SELECT
                dbs.object_name
                ,dbs.object_type
                ,dbs.status
                ,dbs.last_ddl_time
                ,mt.last_ddl_time as meta_last_ddl_time
                ,mt.object_path
                ,mt.md5
            FROM dba_objects dbs
            LEFT JOIN %s.PLADMIN_METADATA mt on dbs.object_name = mt.object_name and dbs.object_type = mt.object_type
            WHERE owner = '%s' 
                AND mt.object_name IS NULL
                AND dbs.object_type in ('%s') """ % (
            self.user,
            self.user,
            types,
        )

        result = self.getData(sql, db=db)

        return result

    def getLastObjectsHash(self):
        """ Get last database update """

        sql = (
            """SELECT * FROM (SELECT last_commit, last_ddl_time FROM %s.PLADMIN_METADATA ORDER BY LAST_DDL_TIME DESC)
                WHERE rownum = 1"""
            % self.user
        )

        result = self.getData(query=sql, fetchOne=True)

        return result

    def getDeletedObjects(self, db=None):
        """ Get Objects that exist on pladmin_metadata table and does't exist on metadata dba_objects"""
        types = "', '".join(self.types)

        sql = """SELECT a.*
        FROM %s.PLADMIN_METADATA a
        WHERE NOT EXISTS (SELECT 1 FROM dba_objects b WHERE b.object_name = a.object_name AND b.object_type = a.object_type AND b.owner='%s')
        AND a.object_type in ('%s') """ % (
            self.user,
            self.user,
            types,
        )

        result = self.getData(sql, db=db)

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
                    AND oo.object_name <> 'PLADMIN_METADATA'
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

    def getData(self, query, params=None, fetchOne=None, db=None, returnDict=True):
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
            result = cursor.execute(query, params)

        # Overriding rowfactory method to get the data in a dictionary
        if returnDict:
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

    def newUser(self, db, force=False):

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

        user = cursor.fetchone()
        if user[0]:
            if force:
                files.progress(
                    count=2, total=progressTotal, status="DROP USER %s" % self.user
                )
                cursor.execute("DROP USER %s CASCADE" % self.user)
            else:
                return False

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
        return True

    def dbConnect(self, sysDBA=False):
        """
        Responsible for connecting to oracle database

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
            user = self.db_admin_user
            password = self.db_admin_password

            if self.db_admin_user == "SYS":
                mode = cx_Oracle.SYSDBA
        try:
            return cx_Oracle.connect(
                user=user, password=password, dsn=self.dsn, mode=mode, encoding="UTF-8"
            )
        except Exception as e:
            print("Error using %s schema" % self.user)
            # print('*** Caught exception: %s: %s' % (e.__class__, e))
            print(e)
            exit()

    def makeDictFactory(self, cursor):
        """ cx_Oracle library doesn't bring a simple way to convert a query result into a dictionary. """
        columnNames = [d[0].lower() for d in cursor.description]

        def createRow(*args):
            return dict(zip(columnNames, args))

        return createRow

    def getObjSource(self, object_name, object_type, md5=False):

        # Open db connection as a sysadmin
        db = self.dbConnect(sysDBA=True)

        sql = """SELECT * FROM DBA_SOURCE
            WHERE OWNER = '%s' AND NAME = '%s' AND type = '%s' ORDER BY line ASC""" % (
            self.user,
            object_name,
            object_type,
        )

        if object_type == "VIEW":
            sql = """SELECT * FROM DBA_VIEWS
            WHERE OWNER = '%s' AND VIEW_NAME = '%s' """ % (
                self.user,
                object_name,
            )

        result = self.getData(sql, db=db)
        content = ""
        
        if not result:
            return False
        
        for res in result:
            content += res["text"]

        if md5:
            return hashlib.md5(content.encode()).hexdigest()

        return content

    def dropObject(self, object_type, object_name):
        """ This method has to be executed to remove object from database and in the metadata table"""

        # Remove the object in the database
        self.dropDbObjects(object_type, object_name)

        # Remove the object in metadata table
        self.metadataDelete(object_type, object_name)

        return "Removed"


#############################################################
#                      SCRIPTS METHODS                      #
#############################################################
    def scriptsMigrationTable(self, db=None):
        """
        Create migration table for scripts excution
        Migration table has to be created on main schema
        """
        localClose = False

        if not db:
            db = self.dbConnect(sysDBA=True)
            localClose = True

        cursor = db.cursor()

        # Drop (CHECK IF NECESSARY)
        # cursor.execute("DROP TABLE %s.PLADMIN_MIGRATIONS" % self.db_main_schema)

        sql = (
            """ CREATE TABLE %s.PLADMIN_MIGRATIONS (
                ID NUMBER GENERATED ALWAYS AS IDENTITY ( START WITH 1 INCREMENT BY 1 ) PRIMARY KEY,
                NAME VARCHAR2(100) NOT NULL,
                TYPE VARCHAR2(2),
                STATUS VARCHAR(4), 
                OUTPUT VARCHAR2(4000),
                EXECUTED_AT timestamp DEFAULT SYSDATE,
                CONSTRAINT name_unique unique (name)
            )"""
            % self.db_main_schema
        )
        
        data = cursor.execute(sql)

        if localClose:
            db.close()

        return data

    def getScript(self, scriptName, db=None):

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        sql = (
            "SELECT * FROM %s.PLADMIN_MIGRATIONS WHERE NAME = '%s'"
            % (self.db_main_schema, scriptName)
        )
        data = cursor.execute(sql)
        obj = data.fetchone()

        cursor.close()
        if localClose:
            db.close()

        return obj

    def insertScript(self, data, md5=False, db=None):
        """ Insert script on to migrations table
        Params: 
            data: list that contains and dictionary with the following keys: 
            object_name, 
            object_type, 
            object_path, 
            last_commit, 
            last_ddl_time
        """

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        cursor = db.cursor()

        # for obj in data:

        sql = (
            "INSERT INTO %s.PLADMIN_MIGRATIONS (name, type, status, output) VALUES('%s', '%s', '%s','%s')"
            % (
                self.db_main_schema,
                data["name"],
                data["type"],
                data["status"],
                data["output"]
            )
        )
        # print(sql)
        cursor.execute(sql)

        cursor.close()

        if localClose:
            db.commit()
            db.close()


    def RunSqlScript(self, conn, **kwargs):
        statementParts = []
        cursor = conn.cursor()
        replaceValues = [("&" + k + ".", v) for k, v in kwargs.items()] + \
                [("&" + k, v) for k, v in kwargs.items()]
        
        # scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        # fileName = os.path.join(scriptDir, "sql", scriptName + "Exec.sql")
        
        scriptDir = '/plsql/scripts/pendigns/'
        fileName = os.path.join(scriptDir,"20201125102318_WDELACRUZ_AS.sql")

        for line in open(fileName):
            # print(line.strip())
            if line.strip() == "/":
                statement = "".join(statementParts).strip()
                if statement:
                    for searchValue, replaceValue in replaceValues:
                        statement = statement.replace(searchValue, replaceValue)
                    
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        print("\nFailed to execute SQL: %s \n" % fileName, e)
                        # print(e, "\n")
                        # raise
                        pass
                statementParts = []
            else:
                statementParts.append(line)
                cursor.execute("""
                select name, type, line, position, text
                from dba_errors
                where owner = upper(:owner)
                order by name, type, line, position""",
                owner = self.db_main_schema)

        # exit(0)
        # prevName = prevObjType = None
        # for name, objType, lineNum, position, text in cursor:
        #     if name != prevName or objType != prevObjType:
        #         print("%s (%s)" % (name, objType))
        #         prevName = name
        #         prevObjType = objType
        #     print("        %s/%s %s" % (lineNum, position, text))


    # def executeScript(self, script_path, db=None):
    #     """
    #     Execute scripts

    #     params:
    #     ------
    #     path: path routes of the object on the file system
    #     db (cx_Oracle.Connection): The database connection

    #     return (list) with errors if some package were an error
    #     """
    #     localClose = False
    #     if not db:
    #         db = self.dbConnect()
    #         localClose = True

    #     cursor = db.cursor()
    #     cursor.callproc("dbms_output.enable")

    #     opf = open(script_path, "r")
    #     content = opf.read()
    #     opf.close()
        
    #     # print(content)

    #     # Execute create or replace package
    #     try:
    #         cursor.execute(content)
    #         print(self.dbms_output(cursor))
    #     except Exception as e:
    #         # errors.append(e)
    #         pass

    #     if localClose:
    #         db.close()

    #     return True


    def dbms_output(self, cursor):
        output = []

        # Perform loop to fetch the text that was added by PL/SQL
        textVar = cursor.var(str)
        statusVar = cursor.var(int)
            
        while True:
            # get output in oracle script
            cursor.callproc("dbms_output.get_line", (textVar, statusVar))
            if statusVar.getvalue() != 0:
                break
            output.append(textVar.getvalue())
        
        dbmsOutPut = ' '.join(output)
        
        return dbmsOutPut


    # def createMigration(
    #     self, scriptName, fullPath, status, typeScript, output, db=None
    # ):

    #     localClose = False

    #     if not db:
    #         db = self.dbConnect()
    #         localClose = True

    #     cursor = db.cursor()

    #     migration = self.getScriptByName(scriptName=scriptName)

    #     if not migration:

    #         sql = (
    #             (
    #                 """ 
    #                   INSERT INTO omega.PLADMIN_MIGRATIONS (SCRIPT_NAME, STATUS, FULL_PATH, TYPE_SCRIPT, OUTPUT) 
    #                   VALUES('%s', '%s', '%s', '%s', '%s')
                     
    #                   """
    #             )
    #             % (scriptName, status, fullPath, typeScript, output)
    #         )
    #         data = cursor.execute(sql)

    #     if localClose:
    #         db.commit()
    #         db.close()

    # def getScriptByName(self, scriptName):
    #     sql = "SELECT * FROM PLADMIN_MIGRATIONS WHERE script_name='%s' " % (scriptName)

    #     data = self.getData(query=sql, fetchOne=True)

    #     return data

    # def getScriptDB(self, status="OK", date=None):

        if not date:
            date = datetime.now().strftime("%Y%m%d")

        sql = (
            (
                """ SELECT * FROM %s.PLADMIN_MIGRATIONS 
                   WHERE status = '%s'
                   AND created_at >= TO_DATE ('%s', 'YYYYMMDD') 
               """
            )
            % (self.user, status, date)
        )

        data = self.getData(query=sql)

        return data




