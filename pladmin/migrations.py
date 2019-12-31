import os, cx_Oracle, git
from datetime import datetime, date
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
     

    def __init__(self, schedule):

        self.repo = git.Repo(self.pl_path)
        self.__branch = self.repo.active_branch

        self.__created = schedule

        self.__to_day  = datetime.now().strftime("%Y%m%d")
        self.__execute_scripts = os.path.join('/scripts/execute%s' % self.__created)
        self.__errors_scripts  = os.path.join('/scripts/error%s' % self.__created) 
        self.__ddl_path = os.path.join('/scripts/ddl%s' % self.__created)
        self.__dml_path = os.path.join('/scripts/dml%s' % self.__created)

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

        year  = self.__created[:4]
        month = self.__created[4:6]
        day   = self.__created[6::]

        # # valid_date = datetime.date(year=year, month=month, day=day)
        # print(datetime.now(year=year, month=month, day=day))
        # exit()

        if not  self.__created > datetime.now().strftime("%Y%m%d"):
            print('La fecha de programacion debe ser mayor o igual al dia de hoy')
            return False

        is_valid_schedule = re.search(r"^[/](\d{4}[/\/-]\d{2}[/\/-]\d{2})|(\d{8,8})$", schedule)

        if not is_valid_schedule:
            return 'Not a valid date'

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

    def __execute_migrate(self, **data):
        """ this function execute all instruccion sql in indicate file
            and create records with file execute """
        try:
            if not data['infoMigration']:
                db = self.dbConnect()
                cursor = db.cursor()
                
                with open(data['migrationFullPath'], 'r') as script_file:

                    """ read file and convert in string for run like script by cx_oracle """
                    execute_statement = script_file.read()
         
                    cursor.callproc("dbms_output.enable")
                    text_var = cursor.var(str)
                    status_var = cursor.var(int)

                    if execute_statement:
                        cursor.execute(execute_statement)
                        """ get output in oracle script """
                        
                        while True:
                            cursor.callproc("dbms_output.get_line", (text_var, status_var))
                            output = text_var.getvalue()

                            if status_var.getvalue != 0:
                                break
                            print(text_var.getValue())
                       
                      
                        self.createMigration(scriptName=data['migrationName'], status='OK',
                        fullPath=data['migrationFullPath'], typeScript=data['typeScript'], output=output, db=db)
                        
                        ## moving file to execute path
                        os.rename(data['migrationFullPath'], os.path.join(self.__execute_scripts, data['migrationName']))

                        return output
        
                    else:
                        ## removing blank files to clean directory
                        os.remove(data['migrationFullPath'])
                        return 'Nothing to migrate'
                    
        except Exception as error:
            return 'error %s in script %s'%(error, data['migrationName'])

    def scripts_with_error(self, date=''):
        """ get scripts with errors, find in directories by date """
        return self.getScriptDB(status='ERR',date=date)
    