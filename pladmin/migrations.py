import os
from datetime import datetime

class Migrations:

    _sripct_path  = os.path.join('/scripts')
    _ddl_path     = os.path.join('/scripts/ddls')
    _dml_path     = os.path.join('/scripts/dmls')
    _basic_pl_path = os.path.join('/plsqltest/basic.sql')

    def __init__(self):
        
        if not os.path.exists(self._sripct_path):
            os.makedirs(self._sripct_path)

    
    def create_ddl(self, quantity=1, basic_pl=False):
        name_file = 'ddl'
        self.createFile(name=name_file, path=self._ddl_path, quantity=quantity, basic_pl=basic_pl)

    def create_dml(self, quantity=1):
        name_file = 'dml'
        self.createFile(name=name_file, path=self._dml_path, quantity=quantity)
    
    def createFile(self, name, path, quantity=1, basic_pl=False):
         
        if not os.path.exists(path):
            os.makedirs(path)
     
        try:
            for i in range(0, quantity):
                
                date  = datetime.now()
                today = date.strftime("%m%d%Y%H%M%S")
                file_name = name + "_%s_%s.sql"%(today,i+1)
                files = "%s/%s" % (path, file_name)
                os.mknod(files)
                print(basic_pl)
                if basic_pl:
                    self.copyContentFile(files, self._basic_pl_path)


                print('file create %s'%file_name)
          
        except FileExistsError as e:
            print('file %s exist'%name)
    
    def copyContentFile(self, name_file_to_write, name_file_to_copy):
        with open(name_file_to_copy) as f:
            with open(name_file_to_write, "w") as f1:
                for line in f:
                    f1.write(line)