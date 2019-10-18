import os, re, shutil, glob

class Files():
    plsql_path = os.path.join(os.getcwd(), 'plsql')

    # def __init__(self):
        # self.objTypes = self.objTypes()


    def objTypes(self):
        ''' Do not change the order of items''' 
        data = {}
        data['PACKAGE'] = '.psk'
        data['VIEW'] = '.vew'
        data['FUNCTION'] = '.fnc'
        data['PROCEDURE'] = '.prc'
        data['PACKAGE BODY'] = '.pbk'

        return data


    def listAllObjsFiles(self):
        types = self.objTypes().values()
        objs = []

        for files in types:
            path = os.path.join(self.plsql_path, '**/*' + files)
            objs.extend(glob.glob(path, recursive=True))

        return objs


    def findObjFileByType(self, objType, objectName):

        oType = self.objTypes()[objType]

        path = os.path.join(self.plsql_path, '**/' + objectName + oType)
        files = glob.glob(path)

        return files


    def listModifedFiles(self):
        '''Listing Pending files'''
        data = []
        # List all .par into Pending dir
        files = glob.glob(os.path.join(self.pending_files, '*.par'))
        for file in files:
            name = self.getFileName(file)
            data.append({'name': name['name'], 'ext': name['ext'], 'path': file})

        return data


    def getFiles(self):
        '''This method read and copy files from ftp
            Rerturn: (List) with each donwloaded file name '''
        downloadedFiles = []
        sftp = self.ftpConnect(host=self.host, user=self.user, password=self.password)
        if sftp:
            sftp.cwd(self.ftp_path)
        else:
            return False

        # List only necessaries files
        regex = re.compile(r'CD.+DOMAC.+\.ascii\.gz')
        ftpFiles = filter(regex.match, sftp.listdir())

        for sfile in ftpFiles:
            # Before download files from sFTP server check if exist in local dir
            fexist = self.findFile(sfile, self.host_files_dir)
            if fexist == True:
                print(' The file ' + sfile + ' Already exist')
                continue

            # Download each compressed file
            fname = sfile.split('.')
            dloaded = os.path.join(self.host_files_dir, sfile)
            sftp.get(sfile, dloaded)
            downloadedFiles.append(sfile)
            print('%s... downloaded' % sfile)

        sftp.close()
        return downloadedFiles


    def findFile(self, name, path):
        """ Determinate if a exist into a tree directory """
        for root, dirs, files in os.walk(path):
            if name in files:
                return True

        return False


    def getFileName(self, path):
        ''' Extract file name and file extention from a path
        Params:
        ------
        path (string): String structured with / e.g: you/path/dir/to/file.pbk
        '''
        gzfname = path.split('/')
        fullfname = gzfname[-1]
        fname = fullfname.split('.')

        return {'name': fname[0], 'ext': fname[1]}


    def createDirs(self):
        
        dt = datetime.now().strftime('%Y%m%d%H%M%S')

        # Create dir to save ftp files if not exits
        os.makedirs(self.host_files_dir, exist_ok=True)

        # Create dir to save pending files to be parsed
        self.pending_files = os.path.join(*[os.getcwd(), self.host_files_dir, 'pending'])
        os.makedirs(self.pending_files, exist_ok=True)

        # Create dir to save corrupted files
        self.corrupted_files = os.path.join(*[os.getcwd(), self.host_files_dir, 'pending_corrupted'])
        os.makedirs(self.corrupted_files, exist_ok=True)

        # Create directory structure to save the files e.g (./YYYY/MM/filename.par)
        self.uncompressed_file_dir = os.path.join(*[os.getcwd(), self.host_files_dir, dt[0:4], dt[4:6], dt[6:8]])
        os.makedirs(self.uncompressed_file_dir, exist_ok=True)

        # Dir to save .gz files that have already been descompresed
        self.gzbackup = os.path.join(self.uncompressed_file_dir, 'gzbackup')
        os.makedirs(self.gzbackup, exist_ok=True)

        # Create dir to saved empties compressed files
        self.empty_gzbackup = os.path.join(self.uncompressed_file_dir, 'gzbackup_empty')
        os.makedirs(self.empty_gzbackup, exist_ok=True)
