import os, cx_Oracle
from datetime import datetime
from pladmin.database import Database

class Migrations(Database):

    _sripct_path   = os.path.join('/scripts')
    _ddl_path      = os.path.join('/scripts/ddls')
    _dml_path      = os.path.join('/scripts/dmls')
    _basic_pl_path = os.path.join('/plsqltest/basic.sql')
    
    def __init__(self):
        
        if not os.path.exists(self._sripct_path):
            os.makedirs(self._sripct_path)

    """ this function create files dmls and ddls """
    def createScript(self, file_type, quantity=1, basic_pl=False):
         
        path = self._sripct_path+"/%s%s"%(file_type, 's')
        if not os.path.exists(path):
            os.makedirs(path)
     
        try:
            for i in range(0, quantity):
                
                date  = datetime.now()
                today = date.strftime("%m%d%Y%H%M%S")
                file_name = file_type  + "_%s_%s.sql"%(today,i+1)
                files = "%s/%s" % (path, file_name)
                os.mknod(files)

                if basic_pl.upper() == 'Y':
                    self.copyContentFile(files, self._basic_pl_path)

                print('file create %s'%file_name)
          
        except FileExistsError as e:
            print('file %s exist'%name)
    
    """ this function copy file content and paste in other file """
    def copyContentFile(self, name_file_to_write, name_file_to_copy):
        with open(name_file_to_copy) as f:
            with open(name_file_to_write, "w") as f1:
                for line in f:
                    f1.write(line)
    
    """ this function execute all files in folder /scipts/ """
    def migrate(self, type_files=None):
        db      = self.dbConnect()
        cursor  = db.cursor() 
    
        path_scripts = self._dml_path

        if type_files == 'ddl':
            path_scripts = self._ddl_path
        
        cursor.callproc("dbms_output.enable")
        
        textVar = cursor.var(str)
        statusVar = cursor.var(int)

        for script in os.listdir(path_scripts):
            with open(script, 'r') as file:
                """read file and convert in string for read cx_oracle"""
                data = file.read().replace('\n', ' ')
                try:
                    if data:
                        cursor.execute(data)
                        cursor.callproc("dbms_output.get_line", (textVar, statusVar))
                        if statusVar.getvalue() != 0:
                            break
                        print (textVar.getvalue())
                        
                   
                except cx_Oracle.DatabaseError as error:
                    print('error %s'%error)
               
        cursor.close()
    
    

   