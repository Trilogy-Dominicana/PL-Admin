class Files():
    plsql_path = os.path.join(os.getcwd(), 'plsql')

    def listPendingFiles(self):
        """Listing Pending files"""
        data = []
        # List all .par into Pending dir
        files = glob.glob(os.path.join(self.pending_files, '*.par'))
        for file in files:
            name = self.getFileName(file)
            data.append({'name': name['name'], 'ext': name['ext'], 'path': file})

        return data
        
    def unzipFiles(self):
        """ Create files just to unzip the files and remove .zg file
        
        Parameters
        ---------
        files: (List) This list contaning a dictionany with file name and content file"""

        # Getting files from host dir (self.host_files_dir) 
        files = glob.glob(os.path.join(self.host_files_dir, '*.ascii.gz'))
        emptyFiles = 0

        # Open compress files
        for file in files:
            zfile = gzip.open(file)
            zcont = zfile.read()

            # Avoiding empty files.
            if len(zcont) < 1:
                print('Archivo vacío %s' % file)
                # Move empty file to empty_gz_backup dir
                shutil.move(file, self.empty_gzbackup)
                emptyFiles += 1
                continue

            # get just file name to move to zgbackup dir and create new .par file
            fname = self.getFileName(file)

            newFileName = os.path.join(*[self.host_files_dir, self.pending_files, fname['name'] + '.par'])
            fileToBeSaved = open(newFileName, 'wb')
            fileToBeSaved.write(zcont)
            fileToBeSaved.close()

            # Move gz file to gzbackup dir
            shutil.move(file, self.gzbackup)

            zfile.close()
        return emptyFiles

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

    def ftpConnect(self, host, user, password):
        """ Connect to sFTP using pysftp library
           
            Parameters
            ----------
            host: (string) FTP host
            user: (string) FTP User
            passwd: (string) FTP Password 
 
            Returns: (object) pysftp object library"""

        # cnopts = pysftp.CnOpts()
        try:
            return pysftp.Connection(host, username=user, password=password)
        except Exception as e:
            print('Error al conectar al FTP')
            # print('Error: {0}'.format(err))
            print('*** Caught exception: %s: %s' % (e.__class__, e))
            return False

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
