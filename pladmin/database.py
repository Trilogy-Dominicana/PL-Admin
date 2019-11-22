import cx_Oracle, os, re, glob
from pladmin.files import Files as files

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

        # Create synonyms
        self.createSynonyms(
            originSchema=self.db_main_schema, detinationSchema=self.user, db=db,
        )

        # Create o replace packages, views, functions and procedures (All elements in files.objectsTypes())
        data = files.listAllObjsFiles()
        self.createReplaceObject(path=data)

        # If some objects are invalids, try to compile
        invalids = self.compileObj()

        return invalids

    def getDBObjects(self):
        """ << TODO >> """
        db = self.dbConnect(sysDBA=True)
        cursor = db.cursor()

        # We need to get all object
        objects = self.getObjects()
        exit()

        # Get views
        vSql = "SELECT view_name FROM dba_views WHERE owner = '%s'" % self.user
        bdViews = self.getData(query=vSql, db=db)

        oSql = (
            "SELECT name, type, line, text FROM dba_source WHERE owner = '%s' and type IN ('%s')"
            % (self.user, types)
        )
        dbObj = self.getData(query=oSql, db=db)
        # cursor.execute(sql)

    def createMetadaTable(self, db=None):
        """
        Create metadata to manage meta information
        """
        if not db:
            db = self.dbConnect()
            localClose = True

        cursor = db.cursor()

        sql = (
            """CREATE TABLE %s.PLADMIN_METADATA(
                    object_name varchar2(30) not null,
                    object_type varchar2(18) not null,
                    last_commit number not null,
                    sync_date date not null,
                    primary key (object_name, object_type)
                )"""
            % self.user
        )

        return cursor.execute(sql)

    def compileObj(self, db=None):
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
                sql = "ALTER PACKAGE  %s.%s COMPILE BODY" % (
                    obj["owner"],
                    obj["object_name"],
                )

            cursor.execute(sql)

            # Update mofication date of file
            updateData = self.getObjects(
                objectTypes=obj["object_type"],
                objectName=obj["object_name"],
                withPath=True,
            )

            files.updateModificationFileDate(
                updateData[0]["path"], updateData[0]["last_ddl_time"]
            )

        if objLen != self.lastIntends:
            self.lastIntends = objLen
            self.compileObj(db=db)

        if localClose:
            db.close()

        return invalids

    def createReplaceObject(self, path=None, db=None):
        """
        Create or Replace packges, views, procedures and functions 

        params: 
        ------
        path (array): path routes of the object on the file system
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
            fi = files.getFileName(f)
            fname = fi["name"]
            ftype = fi["ext"]

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

            cursor.execute(context + content)

            # Getting up object type, if it's package, package body, view, procedure, etc.
            objType = files.objectsTypes(inverted=True)["." + ftype]
            obj = self.getObjects(objectTypes=objType, objectName=fname)

            # Update mofication date of file
            files.updateModificationFileDate(f, obj[0]["last_ddl_time"])

            # Check if the object has some errors
            errors = self.getObjErrors(owner=self.user, objName=fname, db=db)
            if errors:
                data.extend(errors)

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
        self, objectTypes=None, objectName=None, status=None, withPath=False
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

        query = """
        SELECT     
            owner
            ,object_id
            ,object_name
            ,object_type
            ,status
            ,last_ddl_time
            ,created 
        FROM dba_objects WHERE owner = '%s' AND object_type in ('%s')""" % (
            self.user,
            types,
        )

        if (status == "INVALID") or status == "VALID":
            query += " AND status = '%s'" % status

        if objectName:
            query += " AND object_name = '%s'" % objectName

        # Return a dic with the data
        result = self.getData(query)

        if len(result) and withPath:
            i = 0
            for obj in result:
                p = files.findObjFileByType(
                    objectType=obj["object_type"], objectName=obj["object_name"]
                )
                result[i].update({"path": p[0]})
                i += 1

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

    def getData(self, query, params=None, db=None):
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
        text = ''

        for res in result:
            text += res['text']

        return text
