import os, cx_Oracle, git
from datetime import datetime
from pladmin.database import Database
from pladmin.files import Files


class Migrations(Database, Files):

    __ddl_path         = None
    __dml_path         = None
    __execute_scripts  = None
    __errors_scripts   = None 
    __basic_pl_path    = None
    __branch           = None
    __created          = None 
    __to_day           = None
     

    def __init__(self):

        self.repo = git.Repo(self.pl_path)
        self.__branch = self.repo.active_branch

        self.__created = datetime.now().strftime("/%Y/%m/%d")
        self.__to_day  = datetime.now().strftime("%Y%m%d")
        self.__execute_scripts = os.path.join('/scripts/execute%s' % self.__created)
        self.__errors_scripts  = os.path.join('/scripts/error%s' % self.__created) 
        self.__ddl_path = os.path.join('/scripts/ddl')
        self.__dml_path = os.path.join('/scripts/dml')

        self.__createScriptsDir()
        
    def create_script(self, file_type, quantity=1, basic_pl=False):
    
        path = self.__dml_path

        if file_type == 'ddl':
            path = self.__ddl_path

        if not os.path.exists(path):
            os.makedirs(path)

        try:

            files_creating = []
            
            for i in range(0, quantity):
                date = datetime.now()
                today = date.strftime("%m%d%Y%H%M%S")

                """ counting the scripts in the directory to get next sequences """
                quantity_scripts_dir = len(os.listdir(path)) + 1

                file_name = "%s_%s_%s_%s.sql" % (self.__branch, file_type, today, quantity_scripts_dir)
                files = "%s/%s" % (path, file_name)

                os.mknod(files)
                files_creating.append(file_name)

                if basic_pl.upper() == 'Y':
                    self.__copy_content_file(files, self.__basic_pl_path)

            return files_creating

        except FileExistsError as e:
            print('file %s exist' % file_name)
    
    def __createScriptsDir(self):

        if not os.path.exists(self.__ddl_path):
            os.makedirs(self.__ddl_path)

        if not os.path.exists(self.__dml_path):
            os.makedirs(self.__dml_path)

        if not os.path.exists(self.__errors_scripts):
            os.makedirs(self.__errors_scripts)
        
        if not os.path.exists(self.__execute_scripts):
            os.makedirs(self.__execute_scripts)
          
    """ this function copy file content and paste in other file """
    @staticmethod
    def __copy_content_file(name_file_to_write, name_file_to_copy):
        try:
            with open(name_file_to_copy) as f:
                with open(name_file_to_write, "w") as f1:
                    for line in f:
                        f1.write(line)
        except FileNotFoundError as e:
            raise

    """ this function execute indicate scripts """
    def migrate(self, type_files=None):
        data = []
        path = self.__dml_path

        if type_files == 'ddl':
            path = self.__ddl_path
            
        if len (os.listdir(path)) == 0:
            return 'No script to migrate'
              
        for script in os.listdir(path):
     
            migration = os.path.join(path, script)
            dataMigration = self.getScriptByName(script)

            response = self.__execute_migrate(migrationFullPath=migration, 
            migrationName=script,infoMigration=dataMigration,typeScript=type_files)
            
            data.append(response)
        
        return data
        # print(self.scripts_with_error(date=self.__to_day))

    def __execute_migrate(self, migrationFullPath, infoMigration, migrationName, typeScript):

        try:
            if not infoMigration or (infoMigration and infoMigration['status'] == 'ERR'):
                db = self.dbConnect()
                cursor = db.cursor()
                
                with open(migrationFullPath, 'r') as script_file:

                    """ read file and convert in string for run like script by cx_oracle """
                    execute_statement = script_file.read()
         
                    cursor.callproc("dbms_output.enable")
                    text_var = cursor.var(str)
                    status_var = cursor.var(int)

                    if execute_statement:
                        cursor.execute(execute_statement)
                        """ get output in oracle script """
                        cursor.callproc("dbms_output.get_line", (text_var, status_var))

                        output = text_var.getvalue()
                       
                        if infoMigration and infoMigration['status'] == 'ERR':
                            self.updateMigration(status='OK', output=output, scriptName=migrationName, db=db)
                           
                        elif not infoMigration:
                            self.createMigration(scriptName=migrationName, status='OK',
                            fullPath=migrationFullPath, typeScript=typeScript, output=output, db=db)
                        
                        ## moving file to execute path
                        os.rename(migrationFullPath, os.path.join(self.__execute_scripts, migrationName))

                        return output

                    else:
                        return 'Nothing to migrate'
                    

        except FileNotFoundError as error:
            return error

        except cx_Oracle.DatabaseError as error:

            if infoMigration and infoMigration['status'] == 'ERR':
                self.updateMigration(status='ERR', output=error, scriptName=migrationName)

            elif not infoMigration:
                self.createMigration(scriptName=migrationName, status='ERR',
                                     fullPath=migrationFullPath, typeScript=typeScript, output=error)

            return 'error %s in script %s'%(error, migrationName)

    def scripts_with_error(self, date=''):
        """ get scripts with errors, find in directories by date """
        return self.getScriptDB(status='ERR',date=date)
