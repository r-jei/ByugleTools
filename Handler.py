import ast
import re
import os
import requests
from bs4 import BeautifulSoup
import bs4
import mirror

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
        #self.php_cookie = self.session.cookies['PHPSESSID']
        #self.hbll_cookie = self.session.cookies['HBLL']
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
            URL = 'https://cas.byu.edu/cas/login'
            page = c.get(URL)
            self.session_cookie = c.cookies['JSESSIONID']

            soup = BeautifulSoup(page.content, 'html.parser')
            lt_tags = soup.find_all(attrs={'name':'lt'})
            LT = lt_tags[0]['value']

            login_data = dict(username=un, password=pw, _eventId='submit',
                              execution="e1s1", lt=LT)

            r_post = c.post(URL, data=login_data, headers={
                "Referer": "http://byugle.lib.byu.edu", "Cookie": "JSESSIONID="
                +self.session_cookie})


            result = r_post.content
            fi = open( 'my_html.html','w' )
            fi.write( result )

            self.handle_duo( c, result )
            
            return c

        
    ###################################################################
    #                              TODO                               #
    ###################################################################
    #                                                                 #
    ###################################################################
    def handle_duo( self, sess, result ):
        # Check if Duo Multifactor Authentication is in progress
        check = 'Multifactor Authentication is in progress...'
        if check in result:
            self.TX_HOST = 'host'
            self.TX_RQ = 'sig_request'
            self.TX_ARG = 'post_argument'
            pattern = re.compile( "Duo.init\({\s*'" + self.TX_HOST + \
                                  "':\s*'.*',\s*'" + self.TX_RQ + \
                                  "':\s*'.*',\s*'" + self.TX_ARG + \
                                  "':\s*'.*'\s*}\)" )
            match = pattern.search( result )
            
            if match:
                duo_str = match.group(0)
                dict_str = duo_str[9:]
                dict_str = dict_str[:-1]
                post_dict = ast.literal_eval( dict_str )
                self.tx = post_dict[self.TX_RQ][:96]
            else:
                raise Error()

            self.auth_request( sess, post_dict )
            
        else:
            return

        
    ###################################################################
    #                               TODO                              #
    ###################################################################
    #                                                                 #
    ###################################################################
    def auth_request( self, sess, dct ):

        cookies = {
            'trc|DUQFZ4LXTWO1DOUW1SKB|DAUG7PQGSC0SA1OIHO0R':'EPL7DMTJSJ024EUK1VQ7',
            'hac|DUQFZ4LXTWO1DOUW1SKB|DAUG7PQGSC0SA1OIHO0R':'|128.187.112.29|1535553787|d74f00945ff3ce0487feb5caccbc662a500fb8a4'
        }
        
        URL = "https://" + dct[self.TX_HOST] + \
            '/frame/web/v1/auth?tx=' + \
            dct[self.TX_RQ][:96] + \
            '&parent=https://cas.byu.edu/cas/login'

        params = {
            'parent':'https://cas.byu.edu/cas/login',
            'tx':dct[self.TX_RQ][:96]
        }

        headers = {'Host': dct[self.TX_HOST],
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Referer': 'https://' + dct[self.TX_HOST],
                   #'Cookie': cookies,
                   'DNT': '1',
                   'Connection': 'keep-alive',
                   'Upgrade-Insecure-Requests': '1'}
        print(headers)
        
        print('GET request to: ' + URL)
        page = sess.get(URL, data=params, cookies=cookies)
        print(page.status_code)
        f = open('TX_get1.html','w')
        f.write( page.content )
        f.close()





        headers = {'Host': dct[self.TX_HOST],
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Referer': URL,
                   'Connection': 'keep-alive',
                   'Upgrade-Insecure-Requests': '1'}
        
        params = {
            'parent':'https://cas.byu.edu/cas/login',
            'tx':dct[self.TX_RQ][:96]
        }

        print('POST req to:' + URL)
        result = sess.post( URL, headers=headers,data=params,cookies=cookies )
        print(result.status_code)
        
        f = open('TX_post1.html','w')
        f.write( result.content )
        f.close()



        
        
        soup = BeautifulSoup( result.content, 'html.parser' )
        sid = soup.input['value']

        URL = 'https://' + dct[self.TX_HOST] + '/frame/prompt'#'/?sid=' + sid
        URL.replace('%7C','|')

        headers = {'Host': 'api-d3b66583.duosecurity.com',
                   'User-Agent': \
                       'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
                   'Accept': 'text/plain, */*; q=0.01',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Referer': \
                       'https://api-d3b66583.duosecurity.com/frame/prompt?sid='+sid,
                   'Content-Type':
                       'application/x-www-form-urlencoded; charset=UTF-8',
                   'X-Requested-With': 'XMLHttpRequest',
                   #'Content-Length': '205',
                   #'Cookie': 'trc|DUQFZ4LXTWO1DOUW1SKB|DAUG7PQGSC0SA1OIHO0R=EPL7DMTJSJ024EUK1VQ7; hac|DUQFZ4LXTWO1DOUW1SKB|DAUG7PQGSC0SA1OIHO0R=|128.187.112.29|1535127182|1a2d395f2824afe9395520d7d11b15fce8b9df58',
                   'DNT': '1',
                   'Connection': 'keep-alive'}
        print('POST req to: ' + URL )
        result = sess.post(URL, headers=headers, cookies=cookies)
        print(result.status_code)
        f = open('TX_redir.html','w')
        f.write( result.content )
        f.close()
        
        
    ###################################################################
    #                              login                              #
    ###################################################################
    # Uses username and password to get a logged-in Byugle session.   #
    #                                                                 #
    # @un: username                                                   #
    # @pw: password                                                   #
    # @return: logged-in Byugle session.                              #
    ###################################################################
    def loadMaps( self ):
        self.dpt_map = dict()
        self.dpt_map['0'] = '-- or browse by department --'
        self.dpt_map['79'] = 'Alice Louise Reynolds'
        self.dpt_map['2'] = 'American Heritage'
        self.dpt_map['81'] = 'American Studies'
        self.dpt_map['3'] = 'Anthropology'
        self.dpt_map['4'] = 'Asian and Near Eastern Languages'
        self.dpt_map['86'] = 'Center for Language Studies'
        self.dpt_map['62'] = 'Center for Teaching and Learning'
        self.dpt_map['76'] = 'Church History and Doctrine'
        self.dpt_map['71'] = 'Cluff Lecture Series'
        self.dpt_map['9'] = 'Communications'
        self.dpt_map['13'] = 'Department of Business Management'
        self.dpt_map['14'] = 'Economics'
        self.dpt_map['17'] = 'English'
        self.dpt_map['77'] = 'English Reading Series'
        self.dpt_map['73'] = 'Entrepreneur Lecture Series'
        self.dpt_map['67'] = 'Faculty Center'
        self.dpt_map['19'] = 'Family Life'
        self.dpt_map['74'] = 'Harvard Business School Seminar'
        self.dpt_map['24'] = 'Health Science'
        self.dpt_map['68'] = 'Healthy Relationships Conference'
        self.dpt_map['25'] = 'History'
        self.dpt_map['61'] = 'House of Learning'
        self.dpt_map['26'] = 'Humanities, Classics, and Comparative Literature'
        self.dpt_map['29'] = 'Integrative Biology'
        self.dpt_map['78'] = 'International Studies'
        self.dpt_map['69'] = 'Joseph Smith Lectures'
        self.dpt_map['66'] = 'Library - Special Interests'
        self.dpt_map['83'] = 'Library Promos'
        self.dpt_map['30'] = 'Linguistics and English Language'
        self.dpt_map['59'] = 'LRC'
        self.dpt_map['63'] = 'LRC/LDS'
        self.dpt_map['31'] = 'Mathematics'
        self.dpt_map['34'] = 'Microbiology and Molecular Biology'
        self.dpt_map['75'] = 'Music and Dance Library'
        self.dpt_map['58'] = 'Nursing'
        self.dpt_map['37'] = 'Nutrition, Dietetics, and Food Science'
        self.dpt_map['64'] = 'Office of Academic Vice President'
        self.dpt_map['72'] = 'Other Lectures'
        self.dpt_map['39'] = 'Philosophy'
        self.dpt_map['40'] = 'Physics and Astronomy'
        self.dpt_map['43'] = 'Political Science'
        self.dpt_map['82'] = 'Robert Burns'
        self.dpt_map['47'] = 'School of Accountancy'
        self.dpt_map['48'] = 'School of Music'
        self.dpt_map['49'] = 'School of Technology'
        self.dpt_map['50'] = 'Social Work'
        self.dpt_map['51'] = 'Sociology'
        self.dpt_map['52'] = 'Spanish and Portuguese'
        self.dpt_map['87'] = 'Special Collections'
        self.dpt_map['55'] = 'Theatre and Media Arts'
        self.dpt_map['80'] = 'Thomas L. Kane'
        self.dpt_map['70'] = 'To Tell the Tale Lectures'
        self.dpt_map['60'] = 'UEN'
        self.dpt_map['56'] = 'Visual Arts'
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


    ###################################################################
    #                              login                              #
    ###################################################################
    # Uses username and password to get a logged-in Byugle session.   #
    ###################################################################
    def dpt_name( self, num ):
        return self.dpt_map[num]

    ###################################################################
    #                            col_name                             #
    ###################################################################
    # Uses username and password to get a logged-in Byugle session.   #
    ###################################################################
    def col_name( self, num ):
        return self.col_map[num]


    ###################################################################
    #                           update_video                          #
    ###################################################################
    # Uses username and password to get a logged-in Byugle session.   #
    #                                                                 #
    # @un: username                                                   #
    # @pw: password                                                   #
    # @return: logged-in Byugle session.                              #
    ###################################################################
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
                                     "Cookie": "HBLL_IS_AUTH=true; " },\
                                 data=params)


        soup = BeautifulSoup(post.content,'html.parser')
        if len(soup(id='errMsg'))>0:
            err = 'ERROR: '
            # assuming that the error message is the only <p> tag on the page.
            #TODO: A more elephant/foolproof way of getting the error msg.
            err += soup.p.get_text()
            #todo move log functionality from mirror.py to s.t.  more general
            raise Exception(err)

        #for testing ---
        file = open('test.html','w')
        file.write(post.content)
        file.close()
        
    ###################################################################
    #                              parse_HTML                         #
    ###################################################################
    #                                                                 #
    ###################################################################
    def parse_HTML( self, VID_ID ):
        dictionary = dict()
        page = self.session.get('http://byugle.lib.byu.edu/' + \
                                'editVideoDataAdmin.php?vid='+ \
                                VID_ID)
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
            #if we get to this there's a problem.
            #we shouldn't be trying to make any new rules.
            #TODO maybe that's not necessarily true. rethink this.
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

        ########### Parameters for the creation of a new rule
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

        # byugle gives weird <select> tags here not recognized by parser.html.
        # handling through siblings rather than through children
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
        ############

        #remember to replace '+' with a whitespace
        dictionary['txtAuthor'] = \
            soup.find( id='txtAuthor' ).get( 'value' )

        dictionary['txtBroadcastDay'] = \
            soup.find( id='txtBroadcastDay' ).get( 'value' )

        dictionary['txtBroadcastMon'] = \
            soup.find( id='txtBroadcastMon' ).get( 'value' )

        dictionary['txtBroadcastYr'] = \
            soup.find( id='txtBroadcastYr' ).get( 'value' )

        dictionary['txtCitations'] = \
            soup.find( id='txtCitations' ).get( 'value' )

        dictionary['txtConstraints'] = \
            soup.find( id='txtConstraints' ).get( 'value' )

        dictionary['txtCrApproveNum'] = \
            soup.find( id='txtCrApproveNum' ).get( 'value' )

        dictionary['txtCrHolder'] = \
            soup.find( id='txtCrHolder' ).get( 'value' )

        dictionary['txtCrYear'] = \
            soup.find( id='txtCrYear' ).get( 'value' )

        dictionary['txtDescription'] = \
            soup.find( id='txtDescription' ).get_text()

        dictionary['txtDurHrs'] = \
            soup.find( id='txtDurHrs' ).get( 'value' )

        dictionary['txtDurMin'] = \
            soup.find( id='txtDurMin' ).get( 'value' )

        dictionary['txtDurSec'] = soup.find( id='txtDurSec' ).get( 'value' )

        dictionary['txtEpisode'] = soup.find( id='txtEpisode' ).get( 'value' )

        dictionary['txtEpisodeNum'] = \
            soup.find( id='txtEpisodeNum' ).get( 'value' )

        dictionary['txtExpiresDay'] = \
            soup.find( id='txtExpiresDay' ).get( 'value' )

        dictionary['txtExpiresMon'] = \
            soup.find( id='txtExpiresMon' ).get( 'value' )

        dictionary['txtExpiresYr'] = \
            soup.find( id='txtExpiresYr' ).get( 'value' )

        dictionary['txtNotes'] = soup.find( id='txtNotes' ).get_text()

        dictionary['txtOffCampusStreamUrl'] = \
            soup.find( id='txtOffCampusStreamUrl' ).get( 'value' )

        dictionary['txtStreamUrl'] = \
            soup.find( id='txtStreamUrl' ).get( 'value' )

        dictionary['txtThumbUrl'] = soup.find( id='txtThumbUrl' ).get( 'value' )

        dictionary['txtTitle'] = soup.find( id='txtTitle' ).get( 'value' )

        return dictionary
