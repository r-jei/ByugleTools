from configparser import RawConfigParser
import subprocess
import datetime

class Updater():

    def __init__( self ):
        self.log = ''
        self.config()

    def prep_log_msg( self, msg ):
        self.log += msg + '\n'
        
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

    def log_date_time( self, date=True, time=True ):
        if not date and not time:
            return

        now = ''
        date, time = date_time()

        if date:
            now += date
        if time:
            now += ', ' + time
        
        self.prep_log_msg( now )

    def date_time( self ):
        now_obj = datetime.datetime.now()
        date = '{}.{}.{}'.format( now_obj.year, now_obj.month, now_obj.day )
        time = '{}:{}:{}.{}'.format(
            now_obj.hour, now_obj.minute, now_obj.second, now_obj.microsecond
        )
        return date, time
    
    def config( self, filename='./config.ini' ):
        try:
            config_parser = RawConfigParser()
            config_parser.read(filename)

            self.SFTP_HOST      = config_parser.get( 'SFTP_vars', 'HOST' )
            self.SFTP_PORT      = config_parser.get( 'SFTP_vars', 'PORT' )
            self.SFTP_UN        = config_parser.get( 'SFTP_vars', 'UN' )
            self.SFTP_PW        = config_parser.get( 'SFTP_vars', 'PW' )
            self.SFTP_START_DIR = config_parser.get( 'SFTP_vars', 'START_DIR' )
            self.SFTP_THUMB_DIR = config_parser.get( 'SFTP_vars', 'THUMB_DIR' )

            
            self.SMB_HOST       = config_parser.get( 'SMB_vars', 'HOST' )
            self.SMB_ROOT       = config_parser.get( 'SMB_vars', 'ROOT' )
            self.SMB_UN         = config_parser.get( 'SMB_vars', 'UN' )
            self.SMB_PW         = config_parser.get( 'SMB_vars', 'PW' )
            self.SMB_MTPT       = config_parser.get( 'SMB_vars', 'MTPT' )

            self.PREV_VIDID     = config_parser.get('DO_NOT_TOUCH','PREV_VIDID')
            
        except OSError:
            print( 'OSError: Config file parse failed' )

    ###################################################################
    #
    ###################################################################
    def mount_smbfs( self ):
        cmd = 'mount_smbfs //' \
            + self.SMB_UN + ':' + self.SMB_PW + '@' \
            + self.SMB_HOST + self.SMB_ROOT + ' ' \
            + self.SMB_MTPT
        subprocess.call( cmd.split() )
