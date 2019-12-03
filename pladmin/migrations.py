import os
from datetime import datetime

class Migrations:

    _sripct_path = os.path.join('/scripts')
    _ddl_path     = os.path.join('/scripts/ddls')
    _dml_path     = os.path.join('/scripts/dmls')

    def __init__(self):
        
        if not os.path.exists(self._sripct_path):
            os.makedirs(self._sripct_path)

    
    def create_ddl(self):
        date = datetime.now()
        today = date.strftime("%m%d%Y%H%M%S")
        name_file = 'ddl_%s.sql'%today
        self.createFile(name=name_file,path=self._ddl_path)


    def create_dml(self):
        date = datetime.now()
        today = date.strftime("%m%d%Y%H%M%S")
        name_file = 'dml_%s.sql'%today

        self.createFile(name=name_file, path=self._dml_path)
    
    
    def createFile(self, name, path):
         
        if not os.path.exists(path):
            os.makedirs(path)
     
        try:
            dml_file = "%s/%s" % (path, name)
            os.mknod(dml_file)
            print('file create %s'%name)
        except FileExistsError as e:
            print('file %s exist'%name)

        



