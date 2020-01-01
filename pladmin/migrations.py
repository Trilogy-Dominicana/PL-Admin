import os, cx_Oracle, git, re
from datetime import datetime, date
from pladmin.database import Database
from pladmin.files import Files


class Migrations(Database, Files):

    __ds_path          = None
    __as_path          = None
    __execute_scripts  = None
    __errors_scripts   = None 
    __basic_pl_path    = None
    __branch           = None
    __created          = None 
    __to_day           = None


    def __init__(self, schedule=datetime.now().strftime("/%Y/%m/%d")):

        self.repo = git.Repo(self.pl_path)
        self.__created = schedule
        self.__to_day  = datetime.now().strftime("%Y%m%d")
        self.__execute_scripts = os.path.join('/scripts/execute%s' % self.__created)
        self.__errors_scripts  = os.path.join('/scripts/error%s' % self.__created) 
        self.__ds_path = os.path.join('/scripts/ds%s' % self.__created)
        self.__as_path = os.path.join('/scripts/as%s' % self.__created)

        self.__createScriptsDir()

    def create_script(self, file_type, quantity=1, basic_pl=False):
        """ create file type .sql """
        path = self.__as_path

        if file_type == 'ds':
            path = self.__ds_path

        try:
            files_creating = []
            
            for i in range(0, quantity):
                date = datetime.now()
                today = date.strftime("%m%d%Y%H%M%S")

                """ counting the scripts in the directory to get next sequences """
                quantity_scripts_dir = len(os.listdir(path)) + 1

                file_name = "%s%s%s.sql" % (file_type, today, quantity_scripts_dir)
                files = "%s/%s" % (path, file_name.upper())

                os.mknod(files)
                files_creating.append(file_name)

                if basic_pl.upper() == 'Y':
                    self.__copy_content_file(files, self.__basic_pl_path)

            return files_creating

        except FileExistsError as e:
            return 'file %s exist' % file_name
    
    def __createScriptsDir(self):
        """ creating all dir necesary to migrations """
        if not os.path.exists(self.__ds_path):
            os.makedirs(self.__ds_path)

        if not os.path.exists(self.__as_path):
            os.makedirs(self.__as_path)

        if not os.path.exists(self.__errors_scripts):
            os.makedirs(self.__errors_scripts)
        
        if not os.path.exists(self.__execute_scripts):
            os.makedirs(self.__execute_scripts)
    
    @staticmethod
    def __copy_content_file(name_file_to_write, name_file_to_copy):
        """ this function copy file content and paste in other file """
        try:
            with open(name_file_to_copy) as f:
                with open(name_file_to_write, "w") as f1:
                    for line in f:
                        f1.write(line)
        except FileNotFoundError as e:
            raise

    def migrate(self, type_files=None):
        """ this function execute indicate scripts """
        data = []
        path = self.__as_path

        if type_files == 'ds':
            path = self.__ds_path

         # check if all AS script was executed 
        if type_files == 'ds' and len (os.listdir(self.__as_path)) > 0:
            return  'All scripts "AS" they must be executed before "DS" '
            

        if len (os.listdir(path)) == 0:
            return 'No script to migrate'
              
        for script in os.listdir(path):
            migration = os.path.join(path, script)
            dataMigration = self.getScriptByName(script)
            
            if dataMigration:
                return 'this script %s has already been executed' % script

            response = self.__execute_migrate(migrationFullPath=migration, 
            migrationName=script,infoMigration=dataMigration,typeScript=type_files)
            
            data.append(response)
        
        return data

    def __execute_migrate(self, **data):
        """ this function execute all instruccion sql in indicate file
            and create records with file execute """ 
        try:
            if not data['infoMigration']:
                db = self.dbConnect()
                cursor = db.cursor()
                output = []
                
                with open(data['migrationFullPath'], 'r') as script_file:
                    """ read file and convert in string for run like script by cx_oracle """
                    execute_statement = script_file.read()
                    
                    if execute_statement:
                        # enable DBMS_OUTPUT
                        cursor.callproc("dbms_output.enable")
                        cursor.execute(execute_statement)
                       
                       # perform loop to fetch the text that was added by PL/SQL
                        textVar = cursor.var(str)
                        statusVar = cursor.var(int)
                            
                        while True:
                            # get output in oracle script
                            cursor.callproc("dbms_output.get_line", (textVar, statusVar))
                            if statusVar.getvalue() != 0:
                                break
                            output.append(textVar.getvalue())
                        
                        dbms_output = ' '.join(output)

                        self.createMigration(scriptName=data['migrationName'], status='OK',
                        fullPath=data['migrationFullPath'], typeScript=data['typeScript'], 
                        output=dbms_output)
                        
                        ## moving file to execute path
                        os.rename(data['migrationFullPath'], os.path.join(self.__execute_scripts, data['migrationName']))
                        
                        # disabled oracle DBMS_OUTPUT
                        cursor.callproc("dbms_output.disable")
                        return dbms_output
        
                    else:
                        ## removing blank files to clean directory
                        os.remove(data['migrationFullPath'])
                        return 'Nothing to migrate'
                    
        except Exception as error:
            # if script raise error stop pap ejecution
            raise error
    
    def check_place_script(self):
        """ check that script DS dont have command ddl"""

        if len (os.listdir(self.__ds_path)) == 0:
            return 'Nothing to check'
        # These commands must be executed before production.
        reserved_word = ['ALTER','CREATE', 'REPLACE', 
        'DROP', 'TRUNCATE', 'RENAME', 'GRANT', 'REVOKE']

        script_moved = []
        message = "all script in order"

        for dir_file in os.listdir(self.__ds_path):
            script_revision = os.path.join(self.__ds_path, dir_file)
            with open(script_revision, 'r') as file_script:
                statement = file_script.read()

                for word in reserved_word:
                    exists_word = statement.count(word)
                    
                    if exists_word > 0:
                        script_moved.append(dir_file)
                        os.rename(script_revision, os.path.join(self.__as_path, dir_file))
                 
                if script_moved:
                    message = 'the scripts %s was moved to the execution of ace scripts, because it contained ddl instructions' % script_moved
        
        return message
    