import os, cx_Oracle, git, re
from termcolor import colored
from datetime import datetime, date
from pladmin.database import Database
from pladmin.files import Files


class Migrations(Database, Files):

    __dsPath          = None
    __asPath          = None
    __executeScripts  = None
    __basePlPath      = None
    __branch          = None
    __created         = None 
    __toDay           = None
   

    def __init__(self, folderSchedule=datetime.now().strftime("/%Y/%m/%d")):
        # self.repo = git.Repo(self.__basePlPath)
        self.__created = folderSchedule
        self.__toDay  = datetime.now().strftime("%Y%m%d")
        self.__executeScripts = os.path.join('/scripts/execute%s' % self.__created)
        self.__dsPath = os.path.join('/scripts/ds%s' % self.__created)
        self.__asPath = os.path.join('/scripts/as%s' % self.__created)
       
        self.__createScriptsDir()

    def createScript(self, fileType, quantity=1, basicPl=False):
        """ create file type .sql """
        path = self.__asPath

        if fileType == 'ds':
            path = self.__dsPath

        try:
            fileCreating = []
            
            for i in range(0, quantity):
                date = datetime.now()
                today = date.strftime("%m%d%Y%H%M%S")

                """ counting the scripts in the directory to get next sequences """
                quantityScriptsDir = len(os.listdir(path)) + 1

                fileName = "%s%s%s.sql" % (fileType, today, quantityScriptsDir)
                files = "%s/%s" % (path, fileName.upper())

                os.mknod(files)
                fileCreating.append(fileName)

                if basicPl == 'Y':
                    self.__copyContentFile(files, self.__basePlPath)

            return fileCreating

        except FileExistsError as e:
            raise 
    
    def __createScriptsDir(self):
        """ creating all dir necesary to migrations """
        if not os.path.exists(self.__dsPath):
            os.makedirs(self.__dsPath)

        if not os.path.exists(self.__asPath):
            os.makedirs(self.__asPath)
        
        if not os.path.exists(self.__executeScripts):
            os.makedirs(self.__executeScripts)
    
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

    def migrate(self, typeFile=None):
        """ this function execute indicate scripts """
        data = []
        path = self.__asPath

        if typeFile == 'ds':
            path = self.__dsPath

         # check if all AS script was executed 
        if typeFile == 'ds' and len (os.listdir(self.__asPath)) > 0:
            return  colored('All scripts "AS" they must be executed before "DS" ', 'red')
            
        
        if len (os.listdir(path)) == 0:
            return colored('No script to migrate', 'yellow')
              
        for script in os.listdir(path):
            migration = os.path.join(path, script)
            dataMigration = self.getScriptByName(script)
            
            if dataMigration:
                os.remove(script)
                return colored('this script %s has already been executed' % script, 'red')
            
            response = self.__executeMigration(
                migrationFullPath=migration, migrationName=script, infoMigration=dataMigration,
                typeScript=typeFile
            )
            
            # removing dir if no exist script to migrate
            if len (os.listdir(path)) < 1:
                os.rmdir(path)

            data.append(response)
        
        return data

    def __executeMigration(self, **data):
        """ this function execute all instruccion sql in indicate file
            and create records with file execute """ 
        try:
            if not data['infoMigration']:
                db = self.dbConnect()
                cursor = db.cursor()
                output = []
                with open(data['migrationFullPath'], 'r') as scriptFile:
                    """ read file and convert in string for run like script by cx_oracle """
                    executeStatement = scriptFile.read()
                    
                    if executeStatement:
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

                        self.createMigration(scriptName=data['migrationName'], status='OK',
                        fullPath=data['migrationFullPath'], typeScript=data['typeScript'], 
                        output=dbmsOutPut)
                        
                        ## moving file to execute path
                        os.rename(data['migrationFullPath'], os.path.join(self.__executeScripts, data['migrationName']))
                        
                        # disabled oracle DBMS_OUTPUT
                        cursor.callproc("dbms_output.disable")
                        return colored(dbmsOutPut, 'green')
        
                    else:
                        ## removing blank files to clean directory
                        os.remove(data['migrationFullPath'])
                        return colored ('Nothing to migrate', 'yellow')
                    
        except Exception as error:
            # if script raise error stop pap ejecution
            raise Exception('an error occurred in the execution of the script %s error: %s' % (data['migrationFullPath'], error))
    
    def checkPlaceScript(self):
        """ check that script DS dont have command ddl """

        if len (os.listdir(self.__dsPath)) == 0:
            return colored('Nothing to check', 'yellow')
        # These commands must be executed before production.
        reservedWords = ['ALTER','CREATE', 'REPLACE', 
        'DROP', 'TRUNCATE', 'RENAME', 'GRANT', 'REVOKE']

        scriptsMove = []
        color = 'green'
        message = "all script in order"

        for dirFiles in os.listdir(self.__dsPath):
            scriptRevision = os.path.join(self.__dsPath, dirFiles)
            with open(scriptRevision, 'r') as fileScript:
                statement = fileScript.read()

                for word in reservedWords:
                    existsWord = statement.count(word)
                    
                    if existsWord > 0:
                        scriptMove.append(dirFiles)
                        os.rename(scriptRevision, os.path.join(self.__asPath, dirFiles))
                 
                if scriptMove:
                    color = 'yellow'
                    message = 'the scripts %s was moved to the execution of ace scripts, because it contained ddl instructions' % scriptMove
        
        return colored(message, color)
           