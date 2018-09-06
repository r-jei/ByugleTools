class Updater():

    def __init__( self ):
        self.log = u''

    def prep_log_msg( self, msg ):
        self.log += msg + u'\n'
        
    ###################################################################
    #                               log                               #
    ###################################################################
    # Simple logging function. Error handling, etc.                   #
    ###################################################################
    def commit_log_msg( self, log_filename='./log.txt' ):
        try:
            self.log += '\n'
            log_file = open(log_filename,'ab')
            log_file.write( self.log.encode('utf-8') )
            self.log = ''
            log_file.close()
        except OSError:
            print("Unable to write to log file")


    ###################################################################
    #                              mirror_config                             #
    ###################################################################
    def mirror_config( self, filename='./config.ini' ):
        try:
            print(os.getcwd())
            parser = RawConfigParser()
            parser.read(filename)
            section = 'SFTP_vars'
            
            self.HOST = parser.get(section,'HOST')
            self.PORT = int(parser.get(section,'PORT'))
            self.UN = parser.get(section,'UN')
            self.PW = parser.get(section,'PW')
            self.START_DIR = parser.get(section,'START_DIR')
            bHa
        except OSError:
            print( 'OSError: Config file parse failed' )


    ###################################################################
    #
    ###################################################################
    def mount_smbfs( self ):
        cmd = 'mount_smbfs //' + \
            self.UN + ':' + self.PW + '@' + \
            self.HOST + self.ROOT + ' ' + self.MTPT
        subprocess.call( cmd.split() )

    ###################################################################
    #                           renamer_config                                #
    ###################################################################
    #
    #
    ###################################################################
    def renamer_config( self, filename='./config.ini' ):
        try:
            parser = RawConfigParser()
            parser.read(filename)
            section = 'SMB_vars'
            
            self.HOST = parser.get( section, 'HOST' )
            self.UN = parser.get( section, 'UN' )
            self.PW = parser.get( section, 'PW' )
            self.ROOT = parser.get( section, 'ROOT' )
            self.MTPT = parser.get( section, 'MTPT' )
            
        except OSError:
            print( 'OSError: Config file parse failed' )
