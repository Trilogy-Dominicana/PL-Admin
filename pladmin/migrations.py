import os, cx_Oracle, git, re, ntpath
from pathlib import Path
from datetime import datetime, date
from pladmin.database import Database
from pladmin.files import Files


class Migrations(Files, Database):

    __dsPath          = None
    __asPath          = None
    __executeScripts  = None
    __basePlPath      = None
    __branch          = None
    __created         = None 
    __toDay           = None
   

    def __init__(self):
        super().__init__()
      
    def createScript(self, fileType, quantity=1, basicPl=False):
        """ create file type .sql """
        path = self.script_dir_dml

        if fileType == 'ddl':
            path = self.script_dir_dll

        fileCreating = []
            
        for i in range(0, quantity):
            date = datetime.now()
            today = date.strftime("%m%d%Y%H%M%S")

            """ counting the scripts in the directory to get next sequences """
            quantityScriptsDir = len(os.listdir(path)) + 1

            fileName = "%s%s%s.sql" % (fileType, today, quantityScriptsDir)
            FullPahtScript = "%s/%s" % (path, fileName)

            script = open(FullPahtScript, "w+")
            fileCreating.append(fileName)

            if basicPl == 'Y':
                self.__copyContentFile(files, self.__basePlPath)

        return fileCreating

    @staticmethod
    def __copyContentFile(nameFileWrite, nameFileCopy):
        """ this function copy file content and paste in other file """
        try:
            with open(nameFileCopy) as f:
                with open(nameFileWrite, "w") as f1:
                    for line in f:
                        f1.write(line)
        except FileNotFoundError as e:
            raise

    def migrate(self, typeFile=""):

        findPath = [
            self.script_dir_dll,
            self.script_dir_dml
        ]
     
        for path in findPath:
            for filename in Path(path).rglob('*.sql'):
                yield filename
            
    def executeMigration(self, FullName):
        """ this function execute all instruccion sql in indicate file
            and create records with file execute """ 
        
        scriptName = ntpath.basename(FullName)
        dataScript = self.getScriptByName(scriptName=scriptName)

        try:
            if not dataScript:
                with open(FullName, 'r') as scriptFile:
                    """ read file and convert in string for run like script by cx_oracle """
                    executeStatement = scriptFile.read()

                    if executeStatement:
                        db = self.dbConnect()
                        cursor = db.cursor()
                        output = []

                        # enable DBMS_OUTPUT
                        cursor.callproc("dbms_output.enable")
                        cursor.execute(executeStatement)
                        
                        # perform loop to fetch the text that was added by PL/SQL
                        textVar = cursor.var(str)
                        statusVar = cursor.var(int)
                            
                        while True:
                            # get output in oracle script
                            cursor.callproc("dbms_output.get_line", (textVar, statusVar))
                            if statusVar.getvalue() != 0:
                                break
                            output.append(textVar.getvalue())
                        
                        dbmsOutPut = ' '.join(output)

                        self.createMigration(scriptName=scriptName, status='OK',
                        fullPath=FullName, typeScript="Prueba", 
                        output=dbmsOutPut)
                                            
                        # disabled oracle DBMS_OUTPUT
                        cursor.callproc("dbms_output.disable")
                        return 'success %s' % scriptName

                    else:
                        return 'this file is blank'
       
            else:
                return 'Nothing to migrate'
    
        except Exception as error:
            raise
            # if script raise error stop pap ejecution
            # raise Exception('an error occurred in the execution of the script %s error: %s ' % (FullName, error))
    
    def checkPlaceScript(self):
        """ check that script DS dont have command ddl """

        if len (os.listdir(self.__dsPath)) == 0:
            return 'Nothing to check'
        # These commands must be executed before production.
        reservedWords = ['ALTER','CREATE', 'REPLACE', 
        'DROP', 'TRUNCATE', 'RENAME', 'GRANT', 'REVOKE']

        scriptsMove = []
        message = "all script in order"

        for dirFiles in os.listdir(self.__dsPath):
            scriptRevision = os.path.join(self.__dsPath, dirFiles)
            with open(scriptRevision, 'r') as fileScript:
                statement = fileScript.read()

                for word in reservedWords:
                    existsWord = statement.count(word)
                    
                    if existsWord > 0:
                        scriptsMove.append(dirFiles)
                        os.rename(scriptRevision, os.path.join(self.__asPath, dirFiles))
                 
                if scriptsMove:
                    message = ''' the scripts %s was moved to the execution of 
                    ace scripts, because it contained ddl instructions' % scriptsMove '''
        
        return message
    
    def listAllMigration(self):
        ds = os.listdir(self.__dsPath)
        aS = os.listdir(self.__asPath)

        return aS, ds
    
    def removeMigrations(self, migration):
        try:
            os.remove(migration)
            return 'migration removed'
        except FileNotFoundError as e:
            return 'migration not found'
    
    def getMigration(self, migration, typeFile):
        try:
            path = os.path.join(self.__asPath, migration.upper())

            if typeFile == 'ds':
                path = os.path.join(self.__dsPath, migration.upper())

            with open(path, 'r') as migration:
                return migration.read()

        except FileNotFoundError as e:
            return 'migration not found'
