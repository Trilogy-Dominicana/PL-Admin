import os, sys, re, shutil, glob, git

class Files():
    pl_path = os.path.join('/plsql')

    def __init__(self):
        # Initialize git repo
        self.repo = git.Repo(self.pl_path)


    def objectsTypes(self):
        ''' Do not change the order of items''' 
        data = {}
        data['PACKAGE']      = '.psk'
        data['VIEW']         = '.vew'
        data['FUNCTION']     = '.fnc'
        data['PROCEDURES']   = '.prc'
        data['PACKAGE BODY'] = '.pbk'

        return data


    def localChanges(self):
        ''' Get files changes comparing actual branch with actual changes and the last commit ''' 
        repo = self.repo
        diff = repo.git.diff('--name-only', 'HEAD~1')
        return diff.split('\n')


    def remoteChanges(self):
        data = []
        repo = self.repo
        diff = repo.index.diff('origin/master')

        for item in diff:
            data.append(item.a_path)

        return data


    def listAllObjsFiles(self):
        types = self.objectsTypes().values()
        objs = []

        for files in types:
            path = os.path.join(self.pl_path, '**/*' + files)
            objs.extend(glob.glob(path, recursive=True))

        return objs


    def findObjFileByType(self, objType, objectName):
        ''' Search file by objetct type on DB and return complete path
        
        Params:
        ------
        objType (string) Object Type on DB (PACKAGE, PACKAGE BODY, PROCEDURE, VIEW or FUNCTION)
        objectName (string) Object name on DB, the name has to be the same on DB and the repo (e.g MY_PACKAGE_EXAMPLE)

        return (array) with the complete path of file '''

        oType = self.objectsTypes()[objType]

        path = os.path.join(self.pl_path, '**/' + objectName + oType)
        files = glob.glob(path)

        return files


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


    def progress(self, count, total, status=''):
        ''' 
        Progress bar generator

        params:
        ------
        count (int) counter var 
        total (int) max of counter
        status (string) message to print out right of progres bar
        '''

        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s \n %s \r' % (bar, percents, '%', status))
        sys.stdout.flush()

        return True