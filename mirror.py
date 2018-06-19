import os
import sys
import string
import requests
import bs4
from requests.auth import HTTPBasicAuth
from paramiko import *
from HTMLParser import HTMLParser
from ftplib import FTP_TLS
from bs4 import BeautifulSoup
import datetime
import calendar
import urllib2



##################################################################
#                             MyHtmlParser                       #
##################################################################
# After fetching the HTML of the target video's admin edit page, #
# this parser is used to store the information associated with   #
# the video.                                                     #
#                                                                #
# TODO: Get rid of this because the parse function works fine    #
##################################################################
class MyHTMLParser(HTMLParser):
    attributes = []
    data = dict()
    
    def handle_starttag(self, tag, attrs):
        #print("Start tag :" + tag)
        self.load_data(attrs)
    
    #def handle_endtag(self,tag):
        #print("End tag   :" + tag)
        
    #def handle_data(self, data):
        #print("Data      :" + data)
        
    def load_data(self,attrs):
        NAME = ""
        VAL = ""

        for attr in attrs:
            #print "     attr:", attr
            if attr[0] == 'name':
                NAME = attr[1]
            if attr[0] == 'value':
                VAL = attr[1]
            
        if NAME == 'lt':
            self.data['lt'] = VAL
            
        if NAME == 'txtThumbUrl':
            self.data['thumb_url'] = VAL
            
        if NAME == 'txtStreamUrl':
            self.data['stream_url'] = VAL
            
    def get_data(self,key):
        return self.data[key]
    



#######################################################################
#                             login                                   #
#######################################################################
# Uses the provided username and password to get a logged-in session  #
#                                                                     #
# @USERNAME: The username associated with the target account          #
# @PASSWORD: The password associated with target account              #
# @return: A logged-in python Requests session                        #
#######################################################################
def login(USERNAME,PASSWORD):
    with requests.Session() as c:
        URL = 'https://cas.byu.edu/cas/login?service=http://byugle.lib.byu.edu'
        page = c.get(URL)
        session_cookie = c.cookies['JSESSIONID']

        soup = BeautifulSoup(page.content, 'html.parser')
        lt_tags = soup.find_all(attrs={'name':'lt'})
        LT = lt_tags[0]['value']        
        
        login_data = dict(username=USERNAME, password=PASSWORD, _eventId='submit', execution="e1s1", lt=LT)
        
        r_post = c.post(URL, data=login_data, headers={"Referer": "http://byugle.lib.byu.edu", "Cookie": "JSESSIONID="+session_cookie})
        
        return c
             
##################################################################
#                           parse_HTML                           #
##################################################################
# Given a logged-in session and video ID, puts all of the fields #
# of that videos edit form into a dictionary, with the fieldname #
# as the key and the form data as the value.                     #
#                                                                #
# @VID_ID: The ID of the target video as found in its URL.       #
# @session: A logged-in Byugle session.                          #
# @return: A python dictionary containing the video's form data  #
#          as it appears in its editVideoDataAdmin.php page.     #
##################################################################
def parse_HTML(VID_ID, session):
    dictionary = dict()
    page = session.get('http://byugle.lib.byu.edu/editVideoDataAdmin.php?vid='+VID_ID)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    dictionary['btnSubmit'] = 'Save'
    
    ###########
    if soup.find(id="radCopyrightYes").get('checked') != None:
        dictionary['radCopyright'] = '1'
    else:
        dictionary['radCopyright'] = '0'
    ###########
        
    ###########
    if soup.find(id='radRuleTypeOld').get('checked') != None:
        dictionary['radRuleType'] = 'old'
    else:
        #this is a problem. we shouldn't be trying to make any new rules...
        dictionary['radRuleType'] = 'new'
        raise IOError
    ###########
        
    ###########
    if soup.find(id="radUseRuleYes").get('checked') != None:
        dictionary["radUseRule"] = 'yes'
    else:
        dictionary["radUseRule"] = 'no'
    ###########
    
    ########### Parameters for the creation of a new rule (not necessary for simple metadata changes)
    dictionary['ruleCourse'] = ''
    dictionary['ruleCoursePrefix'] = ''
    dictionary['ruleDayEnd'] = ''
    dictionary['ruleDayStart'] = ''
    dictionary['ruleGro'] = ''
    dictionary['ruleMonEnd'] = ''
    dictionary['ruleMonStart'] = ''
    dictionary['ruleName'] = ''
    dictionary['ruleYrEnd'] = ''
    dictionary['ruleYrStart'] = ''
    ###########
    
    #byugle gives malformed <select> tags here. requires weird handling through siblings rather than through children
    ###########
    for tag in soup.find_all(value='0'):
        if type(tag) == bs4.element.Tag:
            if tag.text == 'Please select your College':
                college_sel = tag
                break
    for sibling in college_sel.next_siblings:
        if u'selected' in sibling.attrs:
            dictionary['selCollege'] = sibling[u'value']
            break
    if 'selCollege' not in dictionary:
        dictionary['selCollege'] = u'0'
        dictionary['selDept'] = u'0'
    else:
        for tag in soup.find_all(value='0'):
            if type(tag) == bs4.element.Tag:
                if tag.text == 'Please select your department':
                    dept_sel = tag
                    break
        for sibling in dept_sel.next_siblings:
            if u'selected' in sibling.attrs:
                dictionary['selDept'] = sibling[u'value']
                break
        if 'selDept' not in dictionary:
            dictionary['selDept'] = u'0'
    ###########
    
    ###########
    for child in soup(id='selExistingRules')[0].contents:
        if type(child) == bs4.element.Tag:
            if u'selected' in child.attrs:
                dictionary['selExistingRules'] = child[u'value']
                break
                #print( 'added selExistingRules: ' + dictionary['selExistingRules'] )
    ############
    
    #remember to replace + with ' '
    dictionary['txtAuthor'] = soup.find(id='txtAuthor').get('value')
    
    dictionary['txtBroadcastDay'] = soup.find(id='txtBroadcastDay').get('value')
    
    dictionary['txtBroadcastMon'] = soup.find(id='txtBroadcastMon').get('value')
    
    dictionary['txtBroadcastYr'] = soup.find(id='txtBroadcastYr').get('value')
    
    dictionary['txtCitations'] = soup.find(id='txtCitations').get('value')
    
    dictionary['txtConstraints'] = soup.find(id='txtConstraints').get('value')
    
    dictionary['txtCrApproveNum'] = soup.find(id='txtCrApproveNum').get('value')
    
    dictionary['txtCrHolder'] = soup.find(id='txtCrHolder').get('value')
    
    dictionary['txtCrYear'] = soup.find(id='txtCrYear').get('value')
    
    dictionary['txtDescription'] = soup.find(id='txtDescription').get_text()
    
    dictionary['txtDurHrs'] = soup.find(id='txtDurHrs').get('value')
    
    dictionary['txtDurMin'] = soup.find(id='txtDurMin').get('value')
    
    dictionary['txtDurSec'] = soup.find(id='txtDurSec').get('value')
    
    dictionary['txtEpisode']  = soup.find(id='txtEpisode').get('value')
    
    dictionary['txtEpisodeNum'] = soup.find(id='txtEpisodeNum').get('value')
    
    dictionary['txtExpiresDay'] = soup.find(id='txtExpiresDay').get('value')
 
    dictionary['txtExpiresMon'] = soup.find(id='txtExpiresMon').get('value')

    dictionary['txtExpiresYr'] = soup.find(id='txtExpiresYr').get('value')
    
    dictionary['txtNotes'] = soup.find(id='txtNotes').get_text()
    
    dictionary['txtOffCampusStreamUrl'] = soup.find(id='txtOffCampusStreamUrl').get('value')
    
    dictionary['txtStreamUrl'] = soup.find(id='txtStreamUrl').get('value')
    
    dictionary['txtThumbUrl'] = soup.find(id='txtThumbUrl').get('value')
    
    dictionary['txtTitle'] = soup.find(id='txtTitle').get('value')
        
    return dictionary


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
def mirror_thumbnail(stream_url, thumb_url):
        PREFIX = 'http://videoweb.lib.byu.edu/images/'
        thumb_url = urllib2.unquote(thumb_url)
        thumb_url = thumb_url.replace(PREFIX,'')
        thumb_ext = os.path.splitext(thumb_url)[1]
        print thumb_ext
        stream_ext = os.path.splitext(stream_url)[1]
        print '\'' + stream_ext + '\''
        new_filepath = stream_url
        if stream_ext != '':
            new_filepath = new_filepath.replace(stream_ext,thumb_ext)
        else:
            new_filepath += thumb_ext
        HOST = 'videoweb.lib.byu.edu'
        PORT = 22
        UN = '####'
        PW = '####'
        START_DIR = '/srv/www/vhosts/videoweb.lib/htdocs/images/'
        old_thumb_url = START_DIR + thumb_url
        
        if '' in [stream_url,thumb_url]:
            print('empty string in either stream or thumb url')
            return None
        
        try:
            
            tr = Transport((HOST, PORT))
            tr.connect(username=UN,password=PW)
            sftp = SFTPClient.from_transport(tr)
            sftp.chdir(START_DIR)
            
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
            sftp.chdir(START_DIR)
            
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
            
        finally:
            tr.close()
        
        return new_thumb_url


###################################################################                                                                #
#                      update_metadata                           #
##################################################################
# Updates the video metadata                                     #
# TODO: -Update Description with Date/Series/Speaker/Title       #
#       -Expand on this documentation :P                         #
#       -Error handling ('Use constraints description, etc)      #
#                                                                #
# @VID_ID: The Byugle ID of the target video, as it appears in   #
#          the URL of any given video.                           #
# @params: A dictionary containing the original (not updated)    #
#         field data of the HTML form.                           #
# @new_url: The new thumbnail URL as it will appear afterwards.  #
# @session: A logged-in python Requests session.                 #
##################################################################
def update_metadata(VID_ID, params, new_url, session):
    new_url = new_url.replace('%20',' ')
    URL = 'http://byugle.lib.byu.edu/editVideoDataAdmin.php'
    payload = {'vid': str(VID_ID)}
    page = session.get(URL, params=payload)
    session_cookie = session.cookies['JSESSIONID']
    php_cookie = session.cookies['PHPSESSID']
    hbll_cookie = session.cookies['HBLL']
    print 'VID_ID: {}'.format(VID_ID)
    #for key in params.keys():
    #    print(key + ': ' + params[key])
    
    #log this update in the "Notes" metadata field
    today = str(datetime.date.today().year) + '.' + str(datetime.date.today().month) + '.' + str(datetime.date.today().day)
    
    log_msg = "\nVID_ID:" + VID_ID + " - Attempting update from OLD:\n\t" + params['txtThumbUrl'] + '\n\tto NEW:\n\t' + new_url + '\n'
    log(log_msg)
    
    if len(new_url) > 200:
        log('ERROR: URL length above 200')
        print new_url
        print 'ERROR: URL length above 200'
        return None
    
    #Automatically fill in the description field with metadata (otherwise Byugle search only gets the title)
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
        err += soup.p.get_text() + '\n'
        log(err)
    
    file = open('test.html','w')
    file.write(post.content)
    file.close()
    
    return session

def log(log_msg):
    try:
        log = open('./log.txt','ab')
        log.write(log_msg.encode('utf-8'))
    except OSError:
        print("Unable to write to log file")   

def update_video(VID_ID, session):
    param_dict = parse_HTML( VID_ID, session )
    
    new_url = mirror_thumbnail( param_dict['txtStreamUrl'], param_dict['txtThumbUrl'] )
    if new_url == None:
        msg = '\nVID_ID:' +VID_ID + ' - ERROR: Unable to mirror thumbnail.\n\tThumbUrl: ' + '\'' + param_dict['txtThumbUrl'] + '\'\n' +\
        '\tStreamUrl: ' + '\'' + param_dict['txtStreamUrl'] + '\'\n'
        print msg
        log(msg)  
        return None
    
    return update_metadata(VID_ID, param_dict, new_url, session)

def main(argv):
    
    incorrect_input = False
    
    if len(argv)<4:
        incorrect_input = True
    else:
        USERNAME = argv[1]
        PASSWORD = argv[2]
        START_ID = argv[3]

    if len(argv) == 4:
        END_ID = str(int(argv[3])+1)        
        
    if len(argv) == 5:
        if int(argv[4]) > int(START_ID):
            END_ID = str(int(argv[4])+1)
        else:
            incorrect_input = True

    if len(argv)>5:
        incorrect_input = True

    if incorrect_input:
            print 'Usage: python mirror.py username password vid_id_start vid_id_end\n' +\
                'vid_id_start must be less than vid_id_end'
            return
        
        
    session = login( USERNAME, PASSWORD )    
    welcome = "\n#######################################\n WELCOME TO THE BYUGLE MIRROR PROGRAM\n" + \
    "#######################################\n"
    
    print(welcome)
    
    for ID in range(int(START_ID),int(END_ID)):
        result = update_video(str(ID), session)
        #todo: better error handling


if __name__ == "__main__":
    main(sys.argv)
