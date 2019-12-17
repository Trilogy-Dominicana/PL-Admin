import os, cx_Oracle, git
from datetime import datetime
from pladmin.database import Database
from pladmin.files import Files


class Migrations(Database, Files):
    __ddl_path = os.path.join('/scripts/ddl%s' % datetime.now().strftime("/%Y/%m/%d"))
    __dml_path = os.path.join('/scripts/dml%s' % datetime.now().strftime("/%Y/%m/%d"))
    __errors_scripts_path = os.path.join('/scripts/error%s' % datetime.now().strftime("/%Y/%m/%d"))
    __basic_pl_path = os.path.join('/plsqltest/basic.sql')
    __branch = None

    def __init__(self):
        self.repo = git.Repo(self.pl_path)
        self.__branch = self.repo.active_branch

        if not os.path.exists(self.__ddl_path):
            os.makedirs(self.__ddl_path)

        if not os.path.exists(self.__dml_path):
            os.makedirs(self.__dml_path)

        if not os.path.exists(self.__errors_scripts_path):
            os.makedirs(self.__errors_scripts_path)

    """ this function create files dml and ddl """

    def create_script(self, file_type, quantity=1, basic_pl=False):

        path = self.__dml_path

        if file_type == 'ddl':
            path = self.__ddl_path

        if not os.path.exists(path):
            os.makedirs(path)

        try:
            for i in range(0, quantity):

                files_creating = []
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

                print(file_name)

        except FileExistsError as e:
            print('file %s exist' % file_name)

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
    
        path = self.__dml_path

        if type_files == 'ddl':
            path = self.__ddl_path
            
        if len (os.listdir(path)) == 0:
            return 'No script to migrate'
        

        # print('test')
        # print(len (os.listdir(path)))
        # exit()
        
        for script in os.listdir(path):
     
            migration = os.path.join(path, script)
            dataMigration = self.getScriptByName(script)

            response = self.executeMigrateStatement(migrationFullPath=migration, 
            migrationName=script,infoMigration=dataMigration,typeScript=type_files)

            print(response)

    def executeMigrateStatement(self, migrationFullPath, infoMigration, migrationName, typeScript):

        try:
            if not infoMigration or (infoMigration and infoMigration['status'] == 'ERR'):
                db = self.dbConnect()
                cursor = db.cursor()
                
                with open(migrationFullPath, 'r') as script_file:

                    """ read file and convert in string for run like script by cx_oracle """
                    execute_statement = script_file.read().replace('\n', ' ')

                    cursor.callproc("dbms_output.enable")
                    text_var = cursor.var(str)
                    status_var = cursor.var(int)

                    if execute_statement:
                        cursor.execute(execute_statement)
                        """ get output in oracle script """
                        cursor.callproc("dbms_output.get_line", (text_var, status_var))

                        output = text_var.getvalue()
                       
                        if infoMigration and infoMigration['status'] == 'ERR':
                            self.updateMigration(status='OK', output=output, scriptName=migrationName)
                           
                        elif not infoMigration:
                            self.createMigration(scriptName=migrationName, status='OK',
                                                 fullPath=migrationFullPath, typeScript=typeScript, output=output)
                            
                        return output
        
        
            return 'Nothing to migrate'

        except FileNotFoundError as error:
            pass

        except cx_Oracle.DatabaseError as error:

            if infoMigration and infoMigration['status'] == 'ERR':
                self.updateMigration(status='ERR', output=error, scriptName=migrationName)

            elif not infoMigration:
                self.createMigration(scriptName=migrationName, status='ERR',
                                     fullPath=migrationFullPath, typeScript=typeScript, output=error)

            return 'error %s in script %s'%(error, migrationName)

    @staticmethod
    def scripts_with_error(date=datetime.now().strftime("/%Y/%m/%d")):
        """ get scripts with errors, find in directories by date """
        try:
            dir_find_errors = os.path.join('/scripts/errors%s' % date)
            scripts_with_errors = [errors for errors in os.listdir(dir_find_errors)]
            return 'scripts con errores %s' % len(scripts_with_errors)
        except FileNotFoundError as e:
            return 'los errores con la fecha indicada no existen'