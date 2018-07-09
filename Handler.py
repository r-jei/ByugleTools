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
        self.session_cookie
        self.php_cookie = self.session.cookies['PHPSESSID']
        self.hbll_cookie = self.session.cookies['HBLL']
        self.loadMaps()
        
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
            self.session_cookie = c.cookies['JSESSIONID']


            soup = BeautifulSoup(page.content, 'html.parser')
            lt_tags = soup.find_all(attrs={'name':'lt'})
            LT = lt_tags[0]['value']        

            login_data = dict(username=un, password=pw, _eventId='submit', execution="e1s1", lt=LT)

            r_post = c.post(URL, data=login_data, headers={"Referer": "http://byugle.lib.byu.edu", "Cookie": "JSESSIONID="+self.session_cookie})

            return c

    def loadMaps( self ):
        self.dpt_map = dict()
        self.dpt_map['0'] = 'Please select your department'
        self.dpt_map['79'] = 'Alice Louise Reynolds'
        self.dpt_map['81'] = 'American Studies'
        self.dpt_map['62'] = 'Center for Teaching and Learning'
        self.dpt_map['71'] = 'Cluff Lecture Series'
        self.dpt_map['77'] = 'English Reading Series'
        self.dpt_map['68'] = 'Healthy Relationships Conference'
        self.dpt_map['61'] = 'House of Learning'
        self.dpt_map['69'] = 'Joseph Smith Lectures'
        self.dpt_map['66'] = 'Library - Special Interests'
        self.dpt_map['83'] = 'Library Promos'
        self.dpt_map['59'] = 'LRC'
        self.dpt_map['63'] = 'LRC/LDS'
        self.dpt_map['75'] = 'Music and Dance Library'
        self.dpt_map['72'] = 'Other Lectures'
        self.dpt_map['82'] = 'Robert Burns'
        self.dpt_map['87'] = 'Special Collections'
        self.dpt_map['80'] = 'Thomas L. Kane'
        self.dpt_map['70'] = 'To Tell the Tale Lectures'
        self.dpt_map['60'] = 'UEN'
        self.dpt_map['85'] = 'Wheatley Forum'

        self.col_map = dict()
        self.col_map['0'] = 'Please select your College'
        self.col_map['13'] = 'BYU Administration'
        self.col_map['16'] = 'David M. Kennedy Center'
        self.col_map['2'] = 'Engineering and Technology '
        self.col_map['14'] = 'Faculty Center'
        self.col_map['3'] = 'Family, Home, & Social Sciences '
        self.col_map['4'] = 'Fine Arts and Communications '
        self.col_map['12'] = 'Harold B. Lee Library'
        self.col_map['5'] = 'Health and Human Performance '
        self.col_map['6'] = 'Humanities '
        self.col_map['7'] = 'J. Reuben Clark Law School '
        self.col_map['17'] = 'Kennedy Center'
        self.col_map['1'] = 'Life Sciences'
        self.col_map['8'] = 'Marriott School of Management '
        self.col_map['9'] = 'McKay School of Education '
        self.col_map['10'] = 'Nursing '
        self.col_map['11'] = 'Physical & Math. Sciences '
        self.col_map['15'] = 'Religious Education'

    def dpt_name( self, num ):
        return self.dpt_map[num]

    def col_name( self, num ):
        return self.col_map[num]

    def update_video( self, URL, params ):

        post = self.session.post(URL, \
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
                                        "PHPSESSID=" + self.php_cookie + "; " + \
                                        "HBLL=" + self.hbll_cookie + ";" }, \
                                     data=params)#'''

        soup = BeautifulSoup(post.content,'html.parser')
        if len(soup(id='errMsg'))>0:
            err = 'ERROR: '
            #Here we are assuming that the error message is the only <p> tag on the page.
            #TODO: A more elephant/foolproof way of getting the error msg.
            err += soup.p.get_text() + '\n'
            log(err)

        '''for testing ---
        file = open('test.html','w')
        file.write(post.content)
        file.close()'''
        
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
            #if we get to this there's  a problem. we shouldn't be trying to make any new rules.
            dictionary['radRuleType'] = 'new'
            #TODO more helpful error handling
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
        dictionary['txtAuthor'] = soup.find( id='txtAuthor' ).get( 'value' )

        dictionary['txtBroadcastDay'] = soup.find( id='txtBroadcastDay' ).get( 'value' )

        dictionary['txtBroadcastMon'] = soup.find( id='txtBroadcastMon' ).get( 'value' )

        dictionary['txtBroadcastYr'] = soup.find( id='txtBroadcastYr' ).get( 'value' )

        dictionary['txtCitations'] = soup.find( id='txtCitations' ).get( 'value' )

        dictionary['txtConstraints'] = soup.find( id='txtConstraints' ).get( 'value' )

        dictionary['txtCrApproveNum'] = soup.find( id='txtCrApproveNum' ).get( 'value' )

        dictionary['txtCrHolder'] = soup.find( id='txtCrHolder' ).get( 'value' )

        dictionary['txtCrYear'] = soup.find( id='txtCrYear' ).get( 'value' )

        dictionary['txtDescription'] = soup.find( id='txtDescription' ).get_text()

        dictionary['txtDurHrs'] = soup.find( id='txtDurHrs' ).get( 'value' )

        dictionary['txtDurMin'] = soup.find( id='txtDurMin' ).get( 'value' )

        dictionary['txtDurSec'] = soup.find( id='txtDurSec' ).get( 'value' )

        dictionary['txtEpisode'] = soup.find( id='txtEpisode' ).get( 'value' )

        dictionary['txtEpisodeNum'] = soup.find( id='txtEpisodeNum' ).get( 'value' )

        dictionary['txtExpiresDay'] = soup.find( id='txtExpiresDay' ).get( 'value' )

        dictionary['txtExpiresMon'] = soup.find( id='txtExpiresMon' ).get( 'value' )

        dictionary['txtExpiresYr'] = soup.find( id='txtExpiresYr' ).get( 'value' )

        dictionary['txtNotes'] = soup.find( id='txtNotes' ).get_text()

        dictionary['txtOffCampusStreamUrl'] = soup.find( id='txtOffCampusStreamUrl' ).get( 'value' )

        dictionary['txtStreamUrl'] = soup.find( id='txtStreamUrl' ).get( 'value' )

        dictionary['txtThumbUrl'] = soup.find( id='txtThumbUrl' ).get( 'value' )

        dictionary['txtTitle'] = soup.find( id='txtTitle' ).get( 'value' )

        return dictionary
