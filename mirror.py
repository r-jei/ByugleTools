import os
import sys
import string
from requests.auth import HTTPBasicAuth
from paramiko import *
from ftplib import FTP_TLS
import datetime
import calendar
import urllib2
from Handler import Handler
from ConfigParser import RawConfigParser

THUMB_URL_MAXLENGTH = 200

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
# @mirror_thumbnail: uses FTP to copy old thumbnails into new     #
#   locations on the FTP server.                                  #
# @update_metadata: updates the Byugle editVideoDataAdmin.php     #
#   form to get thumbnail from elsewhere. Also records update     #
#   history and fills in missing information on the form.         #
# @log: Simple logging function with error handling.              #
# @update_video: Parse HTML, Mirror thumbnail, update metadata.   #
###################################################################
class Mirror():
    def __init__( self, username, password ):
        self.handler = Handler(username, password)
        self.config()
        
    ###################################################################
    #                         mirror_thumbnail                        #
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
    def mirror_thumbnail( self, stream_url, thumb_url ):
        PREFIX = 'http://videoweb.lib.byu.edu/images/'

        #decode the url from percent-encoding
        thumb_url = urllib2.unquote(thumb_url)
        thumb_url = thumb_url.replace(PREFIX,'')
        thumb_ext = os.path.splitext(thumb_url)[1]


        stream_ext = os.path.splitext(stream_url)[1]
        print '\'' + stream_ext + '\''
        new_filepath = stream_url
        if stream_ext != '':
            new_filepath = new_filepath.replace(stream_ext,thumb_ext)
        else:
            new_filepath += thumb_ext

        old_thumb_url = self.START_DIR + thumb_url

        if '' in [stream_url,thumb_url]:
            print('empty string in either stream or thumb url')
            return None

        try:
            tr = Transport((self.HOST, self.PORT))
            tr.connect(username=self.UN,password=self.PW)
            sftp = SFTPClient.from_transport(tr)
            sftp.chdir(self.START_DIR)

            #check if there's a thumbnail image at the old thumbnail url 
            dirs = thumb_url.split('/')
            old_thumb_filename = dirs.pop()

            try:
                for dir in dirs:
                    print(dir)
                    sftp.chdir(dir)
                print('name: ' + old_thumb_filename)
                file = sftp.file(old_thumb_filename)
                file.close()

            except IOError:
                print('no thumbnail on the old thumbnail url')
                return None
            sftp.chdir(None)
            sftp.chdir(self.START_DIR)

            dirs = new_filepath.split('/')

            if dirs[0]=='BYU':
                dirs[0] = "BYU_thumbs"  #set name of thumbnail folder within /images/
            else:
                dirs.insert(0,'BYU_thumbs')
                #this shouldn't happen very often, as BYUgle forces BYU to be the first directory.
                dirs.insert(1,'root_images')
            new_thumb_url = PREFIX + string.join(dirs, '/')
            new_thumb_url = new_thumb_url.replace(' ','%20')
            new_filename = dirs.pop()

            for dir in dirs:
                try:
                    sftp.chdir(dir)
                except IOError:
                    sftp.mkdir(dir)
                    sftp.chdir(dir)

            #Check if file already exists
            try:
                file = sftp.file(new_filename)
                file.close()

            except IOError:
                sftp.file(new_filename,'x')
                new_file = sftp.file(new_filename,'w')
                sftp.getfo(old_thumb_url,new_file)
                new_file.close()
        except:
            print('Error connecting to SFTP server')
        finally:
            tr.close()

        return new_thumb_url


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
        session = self.handler.session
        page = session.get(URL, params=payload)
        session_cookie = session.cookies['JSESSIONID']
        php_cookie = session.cookies['PHPSESSID']
        hbll_cookie = session.cookies['HBLL']
        print 'VID_ID: {}'.format(VID_ID)

        #log this update in the "Notes" metadata field
        today = str(datetime.date.today().year) + '.' + str(datetime.date.today().month) + '.' + str(datetime.date.today().day)

        log_msg = "\nVID_ID:" + VID_ID + " - Attempting update from OLD:\n\t" + params['txtThumbUrl'] + '\n\tto NEW:\n\t' + new_url + '\n'
        self.log(log_msg)

        if len(new_url) > THUMB_URL_MAXLENGTH:
            log('ERROR: URL length above ' + str(THUMB_URL_MAXLENGTH))
            print new_url
            print 'ERROR: URL length above ' + str(THUMB_URL_MAXLENGTH)
            return None

        #Automatically fill in the description field with metadata (Byugle search only parses titles & descriptions)
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
                series = 'Series: English Reading Series (ERS)\n'
            else:
                series = ''

            speaker = 'Author: {}'.format( params['txtAuthor'].encode('utf-8') )
            title = 'Title: {}'.format( params['txtTitle'].encode('utf-8'))

            desc_meta = '{}\n{}{}\n{}\n\n'.format( date,series,speaker,title )
            print 'Adding to description:\n' + desc_meta

            params['txtDescription'] = desc_meta + params['txtDescription'].encode('utf-8')


        if params['txtThumbUrl'] != new_url:
            print('txtThumbUrl: ',params['txtThumbUrl'],'\n','new_url: ',new_url)
            if len(params['txtNotes']) == 0:
                params['txtNotes'] = today + ': Thumbnail updated from:\n' + params['txtThumbUrl']
            else:
                params['txtNotes'] += '\n' + today + ': Thumbnail updated from:\n' + params['txtThumbUrl']


            #Update thumb URL
            params['txtThumbUrl'] = new_url

            URL = "http://byugle.lib.byu.edu/dbmod/dbEditVideoDataAdmin.php?vid=" + str(VID_ID)
            post = session.post(URL, \
                                headers={\
                                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",\
                                         "Accept-Encoding": "gzip, deflate",\
                                         "Accept-Language": "en-US,en;q=0.5",\
                                         "Connection": "keep-alive",\
                                         "Content-Type": "application/x-www-form-urlencoded",
                                         "Host": "byugle.lib.byu.edu",
                                         "Referer": "http://byugle.lib.byu.edu/editVideoDataAdmin.php?vid=1022",
                                         "Upgrade-Insecure-Requests": "1",
                                         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0",
                                         "Cookie": \
                                            "HBLL_IS_AUTH=true; " + \
                                            #"JSESSIONID=" + session_cookie + "; " + \
                                            "PHPSESSID=" + php_cookie + "; " + \
                                            "HBLL="+hbll_cookie + ";" }, \
                                         data=params)#'''

            soup = BeautifulSoup(post.content,'html.parser')
            if len(soup(id='errMsg'))>0:
                err = 'ERROR: '
                #Here we are assuming that the error message is the only <p> tag on the page.
                #TODO: A more elegant/foolproof way of getting the error msg.
                err += soup.p.get_text() + '\n'
                log(err)

            file = open('test.html','w')
            file.write(post.content)
            file.close()

        return session


    ###################################################################
    #                               log                               #
    ###################################################################
    # Simple logging function. Error handling, etc.                   #
    ###################################################################
    def log( self, log_msg ):
        try:
            log = open('./log.txt','ab')
            log.write(log_msg.encode('utf-8'))
        except OSError:
            print("Unable to write to log file")
            
    ###################################################################
    #                              config                             #
    ###################################################################
    def config( self, filename='./config.ini' ):
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
            
        except OSError:
            print( 'OSError: Config file parse failed' )
            
    ###################################################################
    #                           update_video                          #
    ###################################################################
    # After parsing HTML, copy a new thumbnail and update online data #
    #                                                                 #
    # @VID_ID: The URL Video ID of the video to update.               #
    ###################################################################
    def update_video( self, VID_ID ):
        param_dict = self.handler.parse_HTML( VID_ID )

        new_url = self.mirror_thumbnail( param_dict['txtStreamUrl'], param_dict['txtThumbUrl'] )

        #handle this as an exception in the mirror_thumbnail function
        if new_url == None:
            msg = '\nVID_ID:' +VID_ID + ' - ERROR: Unable to mirror thumbnail.\n\tThumbUrl: ' + '\'' + param_dict['txtThumbUrl'] + '\'\n' +\
            '\tStreamUrl: ' + '\'' + param_dict['txtStreamUrl'] + '\'\n'
            print msg
            
            log(msg)  
            return None

        return self.update_metadata( VID_ID, param_dict, new_url )





