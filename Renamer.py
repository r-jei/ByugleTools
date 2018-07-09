import datetime
import re
import errno
import calendar
import subprocess
import os
import shutil
import requests
from Handler import Handler
from ConfigParser import RawConfigParser

###################################################################
#                            Renamer                              #
###################################################################
# An object responsible chiefly for ensuring that information on
# a website (in our case, the byugle streaming service) is kept
# to date after moving or renaming files.
#
# @__init__:
# @rename:
# @
#
###################################################################

class Renamer():
    def __init__( self, username, password ):
        self.handler = Handler(username, password)
        self.config()
        self.loadMaps()
        self.mount_smbfs()

    def loadMaps( self ):
        self.dpt_map = dict()
        self.dpt_map['0'] = None#'Please select your department'
        self.dpt_map['79'] = 'ALR'#'Alice Louise Reynolds'
        self.dpt_map['81'] = 'AmericanStudies'#'American Studies'
        self.dpt_map['62'] = 'CTL'#'Center for teaching and Learning'
        self.dpt_map['71'] = 'CluffLectures'#'Cluff Lecture Series'
        self.dpt_map['77'] = 'ERS'#'English Reading Series'
        self.dpt_map['68'] = 'HealthyRelations'#'Healthy Relationships Conference'
        self.dpt_map['61'] = 'HOL'#'House of Learning'
        self.dpt_map['69'] = 'JSLectures'#'Joseph Smith Lectures'
        self.dpt_map['66'] = 'SpecialInterests'#'Library - Special Interests'
        self.dpt_map['83'] = 'Promos'#'Library Promos'
        self.dpt_map['59'] = 'LRC'
        self.dpt_map['63'] = 'LRC-LDS'
        self.dpt_map['75'] = 'Music-And-Dance'#'Music and Dance Library'
        self.dpt_map['72'] = 'Other'#'Other Lectures'
        self.dpt_map['82'] = 'RobertBurns'#'Robert Burns'
        self.dpt_map['87'] = 'SpecialCollections'#'Special Collections'
        self.dpt_map['80'] = 'ThomasLKane'#'Thomas L. Kane'
        self.dpt_map['70'] = 'TTTLectures'#'To Tell the Tale Lectures'
        self.dpt_map['60'] = 'UEN'
        self.dpt_map['85'] = 'Wheatley'#'Wheatley Forum'

        self.col_map = dict()
        self.col_map['0'] = None#'Please select your College'
        self.col_map['13'] = 'BYUAdministration'#'BYU Administration'
        self.col_map['16'] = 'DavidKennedyCtr'#'David M. Kennedy Center'
        self.col_map['2'] = 'EngineeringAndTech'#'Engineering and Technology'
        self.col_map['14'] = 'FacultyCenter'#'Faculty Center'
        self.col_map['3'] = 'FHSS'#'Family, Home, & Social Sciences'
        self.col_map['4'] = 'FineArtsAndCommunications'#'Fine Arts and Communications'
        self.col_map['12'] = 'HBLL'#'Harold B. Lee Library'
        self.col_map['5'] = 'HealthAndPerformance'#'Health and Human Performance'
        self.col_map['6'] = 'Humanities'
        self.col_map['7'] = 'JRC-LawSchool'#'J. Reuben Clark Law School'
        self.col_map['17'] = 'KennedyCtr'#'Kennedy Center'
        self.col_map['1'] = 'LifeSciences'#'Life Sciences'
        self.col_map['8'] = 'MarriottSchool'#'Marriott School of Management'
        self.col_map['9'] = 'McKaySchool'#'McKay School of Education'
        self.col_map['10'] = 'Nursing'
        self.col_map['11'] = 'PhysicalAndMathSciences'#'Physical & Math. Sciences'
        self.col_map['15'] = 'ReligiousEducation'#'Religious Education'
        
    ###################################################################
    #
    ###################################################################
    def update( self, VID_ID ):
        param_dict = self.handler.parse_HTML( VID_ID )
        old = param_dict['txtStreamUrl']
        dpt = self.dpt_map[ param_dict['selDept'] ]
        col = self.col_map[ param_dict['selCollege'] ]
        
        yr = param_dict['txtBroadcastYr']
        
        mon = param_dict['txtBroadcastMon']
        if mon == '00':
            mon = ''
        else:
            mon = calendar.month_name[ int(mon) ][:3].upper()
            
        day = param_dict['txtBroadcastDay']
        if day == '00':
            day = ''

        author = param_dict['txtAuthor']
        regex = re.compile('[^a-zA-Z]')
        author = regex.sub('',author)[:50]
            
        filename, extension = os.path.splitext(old)
        filename = '{}{}{}_{}_{}_{}_VID{}'.format( yr, mon, day, col, dpt, author, VID_ID )
        new_path = 'BYU/' + col + '/' + dpt + '/' + yr + '/'

        self.rename(old,new_path,filename + extension)

        today = str( datetime.date.today().year ) + '.' + str( datetime.date.today().month ) + '.' + str( datetime.date.today().day )
        note_update = today + ': Stream URL updated from:\n' + param_dict['txtStreamUrl']
        if len( param_dict['txtNotes'] ) == 0:
            param_dict['txtNotes'] = note_update + '\n'
        else:
            param_dict['txtNotes'] += '\n' + note_update + '\n'
            
        param_dict['txtStreamUrl'] = new_path + filename + extension

        URL = "http://byugle.lib.byu.edu/dbmod/dbEditVideoDataAdmin.php?vid=" + str(VID_ID)
        self.handler.update_video( URL, param_dict  )

    def rename( self, old, new_path, filename ):
        to_BYU = self.MTPT + '/BYU/'
        
        if not os.path.exists(self.MTPT + new_path):
            try:
                os.makedirs(self.MTPT + new_path)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise

        print self.MTPT+old
        print os.path.isfile( self.MTPT + old )
        print os.path.isfile( self.MTPT + new_path + filename )
        os.rename( self.MTPT + old, self.MTPT + new_path + filename )
        
    ###################################################################
    #
    ###################################################################
    def mount_smbfs( self ):
        cmd = 'mount_smbfs //' + self.UN + ':' + self.PW + '@' + self.HOST + self.ROOT + ' ' + self.MTPT
        subprocess.call(cmd.split())

    ###################################################################
    #                           config                                #
    ###################################################################
    #
    #
    #
    ###################################################################
    def config( self, filename='./config.ini' ):
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

if __name__ == '__main__':
    pass
