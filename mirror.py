import os
import sys
import string
from requests.auth import HTTPBasicAuth
from paramiko import *
from ftplib import FTP_TLS
import datetime
import calendar
import urllib.request, urllib.error, urllib.parse
import Handler
from Updater import Updater
from configparser import RawConfigParser
from ErrorMsg import *

'''
todo:
    more robust error checking - unicode, etc
    integration with Duo two-step verification system
'''
###################################################################
#                           Mirror                                #
###################################################################
# members                                                         #
# @self.handler: Handler.Handler()                                #
#                                                                 #
# methods                                                         #
# @copy_thumb: uses FTP to copy old thumbnails into new     #
#   locations on the FTP server.                                  #
# @update_metadata: updates the Byugle editVideoDataAdmin.php     #
#   form to get thumbnail from elsewhere. Also records update     #
#   history and fills in missing information on the form.         #
#   TODO: Separate thumbnail-update functionality                 #
#       from information-fill functionality                       #
# @log: Simple logging function with error handling.              #
# @mirror_thumb: Parse HTML, Mirror thumbnail, update metadata.   #
###################################################################
class Mirror(Updater):
    def __init__( self, username, password ):
        Updater.__init__(self)
        self.handler = Handler.Handler(username, password)
        self.config()
        self.PREFIX = 'http://videoweb.lib.byu.edu/images/'
        
    ###################################################################
    #                           mirror_thumb                          #
    ###################################################################
    # After parsing HTML, copy a new thumbnail and update online data #
    #                                                                 #
    # @VID_ID: The URL Video ID of the video to update.               #
    ###################################################################
    def mirror_thumb( self, VID_ID ):
        param_dict = self.handler.parse_HTML( VID_ID )

        new_url = self.copy_thumb(
            param_dict['txtStreamUrl'],
            param_dict['txtThumbUrl']
        )

        #handle this as an exception in the copy_thumb function
        if new_url == None:
            msg = '\nVID_ID:' + VID_ID + ' - ERROR: Unable to mirror thumbnail.\n\tThumbUrl: ' + '\'' + param_dict['txtThumbUrl'] + '\'\n' +\
            '\tStreamUrl: ' + '\'' + param_dict['txtStreamUrl'] + '\''
            print(msg)
            
            self.prep_log_msg(msg)
            return None

        return self.update_metadata( VID_ID, param_dict, new_url )

    
    ###################################################################
    #                             copy_thumb                          #
    ###################################################################
    # Copy thumbnail file to the sftp thumbnail server at a location  #
    # analogous to that of the video file's location on the streaming #
    # server, with the same filename as the video file. Afterwards,   #
    # update_metadata should be used so that the target video refer-  #
    #                                                                 #
    # For example:                                                    #
    # Video_xx has:                                                   #
    #   Streaming URL:                                                #
    #      BYU/HBLL/video_xx.mp4                                      #
    #   Thumb URL:                                                    #
    #      http:// (...) /images/dummy_thummy.jpg                     #
    # -->New Thumb URL:<--                                            #
    #      http:// (...) /images/BYU_thumbs/HBLL/video_xx.jpg         #
    #                                                                 #
    # @stream_url: The streaming URL exactly as it appeared on byugle #
    # @thumb_url: The thumbnail URL exactly as it appeared on byugle  #
    # @return: The "New Thumb URL" of the new copy (as above).        #
    ###################################################################
    def copy_thumb( self, stream_url, thumb_url ):
        old_thumb_url, new_filepath, decoded_url = self.generate_urls(
            thumb_url, stream_url
        )

        if all( v is None for v in [old_thumb_url, new_filepath, decoded_url] ):
            return None

        tr = Transport( (self.SFTP_HOST, int( self.SFTP_PORT) ) )
        new_thumb_url = ''
        
        try:
            tr.connect( username = self.SFTP_UN, password = self.SFTP_PW )
            self.sftp = SFTPClient.from_transport( tr )
            print(  self.sftp.getcwd() )
            self.sftp.chdir( self.SFTP_START_DIR )
            print(  self.sftp.getcwd() )
            
            if self.thumb_exists( decoded_url ) is None:
                return None
            
            new_thumb_url, new_filename = self.setup_dirs(
                decoded_url, new_filepath
            )
            self.copy( new_filename, old_thumb_url )
                    
        except Exception as exc:
            print( repr(exc) )
        finally:
            tr.close()

        return new_thumb_url

    
    ###################################################################
    #
    ###################################################################
    #todo - this isn't going to change thumb_url because it's immutable
    def generate_urls( self, thumb_url, stream_url ):


        #decode the url from percent-encoding
        decoded_url = urllib.parse.unquote(thumb_url)
        decoded_url = decoded_url.replace(self.PREFIX,'')
        thumb_ext = os.path.splitext(decoded_url)[1]

        stream_ext = os.path.splitext(stream_url)[1]
        print(('"' + stream_ext + '"'))
        new_filepath = stream_url
        if stream_ext != '':
            new_filepath = new_filepath.replace(stream_ext,thumb_ext)
        else:
            new_filepath += thumb_ext

        old_thumb_url = self.SFTP_START_DIR + decoded_url

        if '' in [stream_url,decoded_url]:
            print('empty string in either stream or thumb url')
            return None, None, None
        
        return old_thumb_url, new_filepath, decoded_url

    
    ###################################################################
    #
    ###################################################################
    def setup_dirs( self, decoded_url, new_filepath ):
        self.sftp.chdir(None)
        self.sftp.chdir(self.SFTP_START_DIR)

        dirs = new_filepath.split('/')
        
        if dirs[0]=='BYU':
            #set name of thumbnail folder within /images/
            dirs[0] = "BYU_thumbs" 
        else:
            #this shouldn't happen often, as BYUgle forces BYU to be the first directory.
            dirs.insert(0,'BYU_thumbs')
            
            dirs.insert(1,'root_images')
                
        new_thumb_url = self.PREFIX + '/'.join(dirs)
        new_filename = dirs.pop()

        #If path doesn't exist, make it
        for dir in dirs:
            try:
                self.sftp.chdir(dir)
            except IOError:
                self.sftp.mkdir(dir)
                self.sftp.chdir(dir)

        #might be prettier to just pass back new_thumb_url and
        #get the filename from that somehow
        return new_thumb_url, new_filename

    
    ###################################################################
    #
    ###################################################################    
    def copy( self, new_filename, old_thumb_url ):
        #if file exists, do nothing
        try:
            file = self.sftp.file(new_filename)
            file.close()
            #if file doesn't exist, copy the new thumbnail file
        except IOError:
            self.sftp.file(new_filename,'x')
            new_file = self.sftp.file(new_filename,'w')
            self.sftp.getfo(old_thumb_url,new_file)
            new_file.close()
            
    ###################################################################
    #
    ###################################################################
    def thumb_exists( self, decoded_url ):
        #check if there's a thumbnail image at the old thumbnail url
        dirs = decoded_url.split('/')
        old_thumb_filename = dirs.pop()

        try:
            for dir in dirs:
                print(dir)
                self.sftp.chdir(dir)
            print(('name: ' + old_thumb_filename))
            file = self.sftp.file(old_thumb_filename)
            file.close()
            return True
        
        except IOError:
            print('no thumbnail on the old thumbnail url')
            return None
        




    ##################################################################
    #                      update_metadata                           #
    ##################################################################
    # Updates the video metadata                                     #
    # TODO: -Error handling ('Use constraints description, etc)      #
    #                                                                #
    # @VID_ID: The Byugle ID of the target video, as it appears in   #
    #          the URL of any given video.                           #
    # @params: A dictionary containing the original (not updated)    #
    #         field data of the HTML form.                           #
    # @new_url: The new thumbnail URL as it will appear afterwards.  #
    # @return: the login session                                     #  
    ##################################################################
    def update_metadata( self, VID_ID, params, new_url ):
        new_url = new_url.replace('%20',' ')
        URL = 'http://byugle.lib.byu.edu/editVideoDataAdmin.php'
        payload = {'vid': str(VID_ID)}
        page = self.handler.session.get(URL, params=payload)

        self.log_date_time()
        
        msg =  'VID_ID:' + str(VID_ID) + ' - Attempting update from OLD:\n\t' \
            + params['txtThumbUrl'] + '\n\t' \
            + 'to NEW:\n\t' \
            + new_url
        self.prep_log_msg( msg )

        if len(new_url) > THUMB_URL_MAXLEN:
            self.prep_log_msg( THUMB_LEN_FAIL )
            return None
       
        self.update_description( params )

        if params['txtThumbUrl'] != new_url:
            self.update_notes_field( params )
 
            #Update thumb URL
            params['txtThumbUrl'] = new_url
            
            URL = 'http://byugle.lib.byu.edu/' \
                + 'dbmod/dbEditVideoDataAdmin.php?vid=' \
                + str(VID_ID)
            print(URL)
            print('BEGIN PARAMS')
            [print(item) for item in params.items()]
            
            self.handler.post_form_data( URL, params, log_response=True )

        return

    ###################################################################
    #                        update_notes_field                       #
    ###################################################################
    #
    ###################################################################
    def update_notes_field( self, params ):
        #log this update in the "Notes" metadata field
        today = str(datetime.date.today().year) + '.' + \
            str(datetime.date.today().month) + '.' + \
            str(datetime.date.today().day)
        
        if len(params['txtNotes']) == 0:
            params['txtNotes'] = today + ': Thumbnail updated from:\n' + \
                params['txtThumbUrl'] + '\n'
        else:
            params['txtNotes'] += '\n' + today + ': Thumbnail updated from:\n' \
                + params['txtThumbUrl'] + '\n'

        return params['txtNotes']

    
    ###################################################################
    #                        update_description                       #
    ###################################################################
    #
    ###################################################################
    def update_description( self, params ):

        #Is there any metadata already in the description?
        desc_metadata = ['Date:', 'Series:', 'Speaker:', 'Author:', 'Title:']
        desc_has_metadata = False
        for item in desc_metadata:
            if item in params['txtDescription']:
                desc_has_metadata = True

        if desc_has_metadata == False:
            if params['txtBroadcastDay']=='00':
                day = ''
            else:
                day = params['txtBroadcastDay'] + ' '

            month_name = calendar.month_name[int(params['txtBroadcastMon'])]
            if len(month_name) > 0:
                month_name += ' '

            yr = params['txtBroadcastYr']
            if  yr == '0000':
                yr = params['txtCrYear']

            date = 'Date: {}{}{}'.format( day, month_name, yr )

            if params['selDept'] == '77':
                series = 'Series: English Reading Series (ERS)'
            else:
                series = ''

            speaker = 'Author: ' + params['txtAuthor'].encode('utf-8')
            title = 'Title: ' + params['txtTitle'].encode('utf-8')

            desc_meta = '{}\n{}\n{}\n{}\n\n'.format( date,series,speaker,title )
            print(('Adding to description:\n' + desc_meta))

            params['txtDescription'] = desc_meta \
                + params['txtDescription'].encode('utf-8')

            return params['txtDescription']
