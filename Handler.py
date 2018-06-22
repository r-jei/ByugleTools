import os
import requests
from bs4 import BeautifulSoup
import bs4

###################################################################
#                              Handler                            #
###################################################################
# The handler interfaces with the Requests session and parses     #
# the HTML of a particular video's editVideoDataAdmin.php page    #
# to build a dictionary of the video's metadata.                  #
#                                                                 #
# members:                                                        #
# @self.session: Stores a logged-in session.                      #
#                                                                 #
# methods:                                                        #
# @__init__: Take a  username and password, store login session.  #
# @login: Uses username/password to return a logged-in session.   #
# @parse_HTML: Uses the session to get HTML of video's edit page, #
#     and returns a dictionary with the video metadata.           #
###################################################################
class Handler():
    def __init__(self,un,pw):
        self.session = self.login(un,pw)
        
    ###################################################################
    #                              login                              #
    ###################################################################
    # Uses username and password to get a logged-in Byugle session.   #
    #                                                                 #
    # @un: username                                                   #
    # @pw: password                                                   #
    # @return: logged-in Byugle session.                              #
    ###################################################################
    def login(self,un,pw):
        with requests.Session() as c:
            URL = 'https://cas.byu.edu/cas/login?service=http://byugle.lib.byu.edu'
            page = c.get(URL)
            session_cookie = c.cookies['JSESSIONID']

            soup = BeautifulSoup(page.content, 'html.parser')
            lt_tags = soup.find_all(attrs={'name':'lt'})
            LT = lt_tags[0]['value']        

            login_data = dict(username=un, password=pw, _eventId='submit', execution="e1s1", lt=LT)

            r_post = c.post(URL, data=login_data, headers={"Referer": "http://byugle.lib.byu.edu", "Cookie": "JSESSIONID="+session_cookie})
            
            return c

    ###################################################################
    #                              parse_HTML                         #
    ###################################################################
    # Gets video metadata, returns it in a dictionary                 #
    #                                                                 #
    # @VID_ID: video's BYUgle ID (found in the video's URL)           #
    # @return: Dictionary containing video metadata                   #    
    ###################################################################
    def parse_HTML( self, VID_ID ):
        dictionary = dict()
        page = self.session.get('http://byugle.lib.byu.edu/editVideoDataAdmin.php?vid='+VID_ID)
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


    
