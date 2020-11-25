import os, sys, re, shutil, glob, time, hashlib
from datetime import datetime


class Files:
    pl_path = os.path.join("/plsql")
    script_path = os.path.join(pl_path, "scripts")
    displayInfo = False

    def __init__(self, displayInfo=False):

        # Initialize git repo
        # self.repo = git.Repo(self.pl_path)
        # self.head_commit = str(self.repo.head.commit)[:7]
        # Setup config path

        self.db_cnfpath = os.path.join(self.pl_path, '.env')
        
        # Create dir and initialize dir types
        self.createDirs()

        self.types = self.objectsTypes().keys()
        self.extentions = self.objectsTypes().values()
        self.progress_len = 0

    def objectsTypes(self, inverted=False, objKey=None):
        # Do not change the order of items
        data = {}
        data["PACKAGE"] = ".pks"
        data["VIEW"] = ".vw"
        data["FUNCTION"] = ".fun"
        data["PROCEDURE"] = ".prc"
        data["PACKAGE BODY"] = ".pkb"

        if inverted:
            data = dict(map(reversed, data.items()))

        if objKey:
            if objKey in data:
                return data[objKey]
            else:
                return False

        return data

    def localChanges(self):
        """ Get files changes comparing actual branch with actual changes and the last commit """
        repo = self.repo
        # diff = repo.git.diff("--name-only", "HEAD~1")
        diff = repo.git.diff("--name-only")
        if not len(diff):
            return False

        return diff.split("\n")

    def diffByHash(self, objHash, absolutePath=False):
        """ Get files changes comparing actual branch with actual changes and the last commit """
        repo = self.repo
        diff = repo.git.diff("--name-only", objHash)

        data = diff.split("\n")

        # Absolute path
        if absolutePath:
            data = [os.path.join(self.pl_path, s) for s in data]

        return data

    def diffByHashWithStatus(self, objHash):
        """ Get files changes comparing actual branch with actual changes and the last commit """
        repo = self.repo
        data = dict()
        modified = []
        deleted = []
        added = []

        diff = repo.git.diff("--name-status", objHash)
        lines = diff.splitlines()

        for l in lines:
            info = l.split('\t')
            status = info[0]
            path = os.path.join(self.pl_path, info[1])

            if status == 'M':
                modified.append(path)

            if status == 'D':
                deleted.append(path)
            
            if status == 'A':
                added.append(path)

        data['modified'] = modified
        data['deleted'] = deleted
        data['added'] = added 
        data['untraked'] = [os.path.join(self.pl_path, s) for s in repo.untracked_files]

        return data

    def remoteChanges(self):
        data = []
        repo = self.repo
        diff = repo.index.diff("origin/master")

        for item in diff:
            data.append(item.a_path)

        return data

    def files_to_timestamp(self, path=None):
        """ For every file found in path get the last modified timestamp """
        files = self.listAllObjsFiles()
        data = dict([(f, os.path.getmtime(f)) for f in files])

        return data

    def listAllObjectFullData(self, path=None, md5=False):
        """ For every file found in path get the last modified timestamp """
        files = self.listAllObjsFiles()
        data = []

        for f in files:
            obj = {}
            name, _, oType = self.getFileName(f)

            obj["object_name"] = name
            obj["object_type"] = oType
            obj["object_path"] = f
            obj["last_ddl_time"] = os.path.getmtime(f)

            if md5:
                obj["md5"] = self.fileMD5(f)

            data.append(obj)

        return data

    def updateModificationFileDate(self, path, date):

        modTime = time.mktime(date.timetuple())

        # Modify mtime of a file
        os.utime(path, (modTime, modTime))

    def listAllObjsFiles(self):
        types = self.objectsTypes().values()
        objs = []

        for files in types:
            path = self.pl_path + "/**/*" + files
            objs.extend(glob.glob(path, recursive=True))

        return objs

    def findObjFileByType(self, objectType, objectName):
        """ Search file by objetct type on DB and return complete path
        
        Params:
        ------
        objectType (string) Object Type on DB (PACKAGE, PACKAGE BODY, PROCEDURE, VIEW or FUNCTION)
        objectName (string) Object name on DB, the name has to be the same on DB and the repo (e.g MY_PACKAGE_EXAMPLE)

        return (list) with the complete path of file """

        oType = self.objectsTypes()[objectType]

        path = os.path.join(self.pl_path, "**/" + objectName + oType)
        files = glob.glob(path)

        return files

    def validateIfFileExist(self, name, path):
        """ Determinate if a exist into a tree directory """

        for _, _, files in os.walk(path):
            if name in files:
                return True

        return False

    def getFileName(self, path, object_type=False):
        """ Extract file name and file extention from a path
        Params:
        ------
        path (string): String structured with / e.g: you/path/dir/to/file.pbk
        return name, extention, objecType
        """
        gzfname = path.split("/")
        fullfname = gzfname[-1]
        fname = fullfname.split(".")
        name = fname[0]
        extention = fname[1]

        objectType = self.objectsTypes(inverted=True, objKey="." + extention)

        return name, extention, objectType

    def createDirs(self):
        """ Create default directories for """
        dt = datetime.now().strftime("%Y%m%d%H%M%S")

        # Create dir to save ftp files if not exits
        os.makedirs(self.pl_path, exist_ok=True)

        # Create packages ir of not exits
        self.packages_dir = os.path.join(self.pl_path, "packages")
        os.makedirs(self.packages_dir, exist_ok=True)

        # views dir
        self.views_dir = os.path.join(self.pl_path, "views")
        os.makedirs(self.views_dir, exist_ok=True)

        # Views dir
        self.procedures_dir = os.path.join(self.pl_path, "procedures")
        os.makedirs(self.procedures_dir, exist_ok=True)

        # Views dir
        self.functions_dir = os.path.join(self.pl_path, "functions")
        os.makedirs(self.functions_dir, exist_ok=True)

        # Pendings scripts 
        self.scripts_pendings = os.path.join(self.script_path, "pendigns")
        os.makedirs(self.scripts_pendings, exist_ok=True)
        
        # Executed scripts 
        self.scripts_executed = os.path.join(self.script_path, "executed")
        os.makedirs( self.scripts_executed , exist_ok=True)
        
        
        # Create directory structure to save the files e.g (./YYYY/MM/DD)
        # self.script_dir_dll = os.path.join(
        #     *[os.getcwd(), self.pl_path, 'scripts', 'DDL', dt[0:4], dt[4:6], dt[6:8]],
        # )

        # self.script_dir_dml = os.path.join(
        #     *[os.getcwd(), self.pl_path, 'scripts', 'DML', dt[0:4], dt[4:6], dt[6:8]],
        # )

        # os.makedirs(self.script_dir_dll, exist_ok=True)
        
        # os.makedirs(self.script_dir_dml, exist_ok=True)

    def createObject(self, objectName, objectType, contend):
        """ Creates object on it's correcponding dir """

        # Validate if the object type is permited
        if not objectType in self.types:
            return EOFError

        # Getting object extension
        ext = self.objectsTypes(objKey=objectType)

        if objectType == "PACKAGE" or objectType == "PACKAGE BODY":
            d = self.packages_dir

        if objectType == "VIEW":
            d = self.views_dir

        if objectType == "FUNCTION":
            d = self.functions_dir

        if objectType == "PROCEDURE":
            d = self.procedures_dir

        path = os.path.join(d, objectName + ext)

        with open(path, "wt+") as f:
            f.truncate(0)
            f.write(contend)

        return path

    def progress(self, count, total, status="", title=None, end=False):
        """ 
        Progress bar generator

        params:
        ------
        count (int) counter var 
        total (int) max of counter
        status (string) message to print out right of progres bar
        """

        if self.displayInfo:
            if title:
                print(title + "\r")

            bar_len = 60
            filled_len = int(round(bar_len * count / float(total)))
            percents = round(100.0 * count / float(total), 1)
            bar = "█" * filled_len + "░" * (bar_len - filled_len)

            msg = "\r%s %s%s: %s" % (bar, percents, "%", status)

            # Fill out string with spaces
            string = msg.ljust(self.progress_len)

            sys.stdout.write(string)
            sys.stdout.flush()

            self.progress_len = len(string)
            if end:
                print("\n")

        return False

    def fileMD5(self, filePath):
        """ Get file content, hash it and return it in a md5 hash"""
        with open(filePath) as opf:
            content = opf.read().encode()
        
        return hashlib.md5(content).hexdigest()

    # Scripts objects
    def createEmptyScript(self, type, user, content='', ):
        # Create script if no t exist
        os.makedirs(self.scripts_pendings, exist_ok=True)

        # Script path
        date = datetime.now().strftime("%Y%m%d%H%M%S")
        name = '%s_%s_%s.sql' % (date, user, type)
        path = os.path.join(self.scripts_pendings, name)

        with open(path, "wt+") as f:
            f.write(content)
        
        return name

    def listAllScriptsFiles(self, types):
        
        # Validate if types comes
        if not len(types):
            return False

        objs = []
        for files in types:
            path = self.script_path + "/**/*" + files + ".sql"
            objs.extend(glob.glob(path, recursive=True))

        return objs
