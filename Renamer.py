import datetime
import re
import errno
import calendar
import subprocess
import os
import shutil
import requests
import Handler
import ErrorMsg
from Updater import Updater
from configparser import RawConfigParser

################################################################################

###################################################################
#                            Renamer                              #
###################################################################
# An object responsible chiefly for ensuring that information on
# a website (in our case, the byugle streaming service) is kept up
# to date after moving or renaming files.
#
# @__init__:
# @rename:
# @
#
###################################################################

class Renamer(Updater):

    ###################################################################
    #
    ###################################################################
    def __init__( self, username, password ):
        Updater.__init__(self)
        
        self.mount_smbfs()
        self.handler = Handler.Handler(username, password)
        self.config()  
        self.handler.loadMaps()
        
    ###################################################################
    #
    ###################################################################
    def rename( self, old, new_path, filename ):

        mtpt = self.SMB_MTPT
        
        if not os.path.exists( mtpt + new_path ):
            try:
                os.makedirs( mtpt + new_path )
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        try:
            os.rename( mtpt + old, mtpt + new_path + filename )
        except OSError:
            self.prep_log_msg( ErrorMsg.RENAME_FAIL )

            
    ###################################################################
    #
    ###################################################################
    def update( self, VID_ID ):
        param_dict = self.handler.parse_HTML( VID_ID )
        old_stream = param_dict['txtStreamUrl']
        filename, extension, new_path = self.filename_ext_new(
            param_dict, VID_ID
        )
        new_stream = new_path + filename + extension
        valid = self.valid_url( old_stream, new_stream, VID_ID )

        if valid:
            try:
                self.rename( old_stream, new_path, filename + extension )
                self.update_note_field( param_dict )
                msg =  'Updating to \n"' + new_path + filename + '"'
                self.prep_log_msg( msg )
            
                param_dict['txtStreamUrl'] = new_stream 
                URL = "http://byugle.lib.byu.edu" \
                    + "/dbmod/dbEditVideoDataAdmin.php?vid=" \
                    + str(VID_ID)

                self.handler.post_form_data( URL, param_dict )

            except (OSError, Exception) as exc:
                self.prep_log_msg( repr(exc) )

        self.commit_log_msg()

    ###################################################################
    #
    ###################################################################
    def valid_url( self, old_stream, new_stream, VID_ID ):
        self.log_date_time()
        msg = 'VID_ID:' + VID_ID  + ' - Stream URL update from\n"' \
            + old_stream + '"'U
        self.prep_log_msg( msg )

        path_len = len( new_stream )
        if path_len > 150:
            msg = ErrorMsg.THUMB_LEN_WARN + str(path_len)
            self.prep_log_msg( msg )
        
        if old_stream == '':
            self.prep_log_msg( ErrorMsg.EMPTY_STREAM )
            return False

        if new_stream != old_stream:
            return True
        
        else:
            msg = '"' + new_stream + '"\n' + ErrorMsg.SAME_URL
            self.prep_log_msg( msg )
            return False

            
    ###################################################################
    #
    ###################################################################
    def update_note_field( self, param_dict ):
        today = str( datetime.date.today().year ) + '.' \
            + str( datetime.date.today().month ) + '.' \
            + str( datetime.date.today().day )
        
        note_update = '\n' + today + ': Stream URL updated from:\n' + \
            param_dict['txtStreamUrl']

        if len( param_dict['txtNotes'] ) == 0:
            param_dict['txtNotes'] = note_update + '\n'
        else:
            param_dict['txtNotes'] += '\n' + note_update + '\n'

            
    ###################################################################
    #
    ###################################################################
    def day_mon_yr( self, param_dict ):
        yr = param_dict['txtBroadcastYr']
        mon = param_dict['txtBroadcastMon']
        day = param_dict['txtBroadcastDay']
        if yr == '0000':
            yr = param_dict['txtCrYear']
            if yr in ['0','00','000']:
                yr = '0000'

        if mon == '00':
            mon = ''
            day = ''
        else:
            mon = calendar.month_name[ int(mon) ][:3].upper()
            if day == '00':
                day = ''
                
        return day, mon, yr

    
    ###################################################################
    #
    ###################################################################    
    def author_title( self, param_dict ):
        regex = re.compile('[^a-zA-Z0-9]')
        author = param_dict['txtAuthor']
        author = regex.sub('',author)[:25]
        title = param_dict['txtTitle']
        title = regex.sub('',title)[:25]

        return author, title

    
    ###################################################################
    #

    ###################################################################
    def dpt_col( self, param_dict ):
        dpt     = self.handler.getDpt( param_dict['selDept'] )
        college = self.handler.getCol( param_dict['selCollege'] )

        return dpt, college

    
    ###################################################################
    #
    ###################################################################    
    def filename_ext_new( self, param_dict, VID_ID ):
        dpt, college = self.dpt_col( param_dict )
        day, mon, yr = self.day_mon_yr( param_dict )
        author, title = self.author_title( param_dict )
        
        old_stream = param_dict['txtStreamUrl']
        
        filename, extension = os.path.splitext(old_stream)
        filename = '{}{}{}_{}_{}_{}_VID{}'.format( yr, mon, day, dpt, author,
                                                   title, VID_ID )
        new_path = 'BYU/' + college + '/' + dpt + '/' + yr + '/'

        return filename, extension, new_path
