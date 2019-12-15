import os, cx_Oracle, git
from datetime import datetime
from pladmin.database import Database
from pladmin.files import Files


class Migrations(Database, Files):
    __scripts_path = os.path.join('/scripts')
    __ddl_path = os.path.join('/scripts/ddls%s' % datetime.now().strftime("/%Y/%m/%d"))
    __dml_path = os.path.join('/scripts/dmls%s' % datetime.now().strftime("/%Y/%m/%d"))
    __errors_scripts_path = os.path.join('/scripts/errors%s' % datetime.now().strftime("/%Y/%m/%d"))
    __basic_pl_path = os.path.join('/plsqltest/basic.sql')

    def __init__(self):
        if not os.path.exists(self.__ddl_path):
            os.makedirs(self.__ddl_path)

        if not os.path.exists(self.__dml_path):
            os.makedirs(self.__dml_path)

        if not os.path.exists(self.__errors_scripts_path):
            os.makedirs(self.__errors_scripts_path)

    """ this function create files dmls and ddls """
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

                file_name = "%s_%s_%s.sql" % (file_type, today, i + 1)
                files = "%s/%s" % (path, file_name)
                os.mknod(files)
                files_creating.append(file_name)

                if basic_pl.upper() == 'Y':
                    self.__copy_content_file(files, self.__basic_pl_path)

            print(files_creating)

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
        db = self.dbConnect()
        cursor = db.cursor()

        path_scripts = self.__dml_path

        if type_files == 'ddl':
            path_scripts = self.__ddl_path

        """ enable output to oracle scripts """
        cursor.callproc("dbms_output.enable")

        text_var = cursor.var(str)
        status_var = cursor.var(int)

        for script in os.listdir(path_scripts):
            open_file = os.path.join(path_scripts, script)

            with open(open_file, 'r') as file:
                """ read file and convert in string for run like script by cx_oracle """
                data = file.read().replace('\n', ' ')
                try:
                    if data:
                        cursor.execute(data)
                        """ get output in oracle script """
                        cursor.callproc("dbms_output.get_line", (text_var, status_var))
                        if status_var.getvalue() != 0:
                            break
                        print (status_var.getvalue())

                except cx_Oracle.DatabaseError as error:
                    """ move script with errors to folder /scripts/errors/ """
                    script_errors = os.path.join(self.__errors_scripts_path, script)
                    os.rename(open_file, script_errors)
                    print('error %s' % error)

        self.scripts_with_error()
        cursor.close()

    """ get scripts with errors, find in directories by date """
    def scripts_with_error(self, date=datetime.now().strftime("/%Y/%m/%d")):
        dir_find_errors = os.path.join('/scripts/errors%s' % date)
        scripts_with_errors = [errors for errors in os.listdir(dir_find_errors)]
        return 'scripts con errores %s' % len(scripts_with_errors)