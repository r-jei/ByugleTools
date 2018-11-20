import datetime
import string
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
# An object responsible for ensuring that information on
# a website (in our case, the byugle streaming service) is kept up
# to date after moving or renaming files (such as thumbnails or
# .mp4 files)
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
    def __init__( self, handler ):
        Updater.__init__(self)

        self.mount_smbfs()
        self.h = handler
        self.config()

    ###################################################################
    #
    ###################################################################
    def rename( self, old, new_path, filename ):

        mtpt = self.SMB_MTPT
        try:
            os.renames( mtpt + old, mtpt + new_path + filename )
        except OSError:
            self.prep_log_msg( ErrorMsg.RENAME_FAIL )

    ###################################################################
    #
    ###################################################################
    def update( self, VID_ID ):
        # parse html
        param_dict = self.handler.parse_html( VID_ID )
        old_stream = param_dict['txtStreamUrl']

        # build components of new stream url and build it
        filename, extension, new_path = self.filename_ext_new(
            param_dict, VID_ID
        )
        new_stream = new_path + filename + extension
        
        # is updating possible and necessary?
        valid = self.valid_url( old_stream, new_stream, VID_ID )

        if valid:
            try:
                self.rename( old_stream, new_path, filename + extension )
                self.update_note_field( param_dict )
                msg =  'Updating to \n"' + new_path + filename + '"'
                self.prep_log_msg( msg )

                param_dict['txtStreamUrl'] = new_stream
                param_dict['txtOffCampusStreamUrl'] = new_stream
                
                URL = "http://byugle.lib.byu.edu" \
                    + "/dbmod/dbEditVideoDataAdmin.php?vid=" \
                    + str(VID_ID)
                
                self.handler.post_form_data( URL, param_dict )

            except (OSError, Exception) as exc:
                self.prep_log_msg( repr(exc) )

        self.commit_log_msg()

    ###################################################################
    # Does the stream URL need updating, and is it possible to do so? #
    ###################################################################
    def valid_url( self, old_stream, new_stream, VID_ID ):
        self.log_date_time()
        msg = 'VID_ID:' + VID_ID  + ' - Stream URL update from\n"' \
            + old_stream + '"'
        self.prep_log_msg( msg )

        # will the new filepath be too long for Byugle?
        path_len = len( new_stream )
        if path_len > 150:
            msg = ErrorMsg.THUMB_LEN_WARN + str(path_len)
            self.prep_log_msg( msg )

        # do we have a URL we can use to find the video file?
        if old_stream == '':
            self.prep_log_msg( ErrorMsg.EMPTY_STREAM )
            return False
        
        elif new_stream != old_stream:
            return True
        
        elif new_stream == old_stream:
            msg = '"' + new_stream + '"\n' + ErrorMsg.SAME_URL
            self.prep_log_msg( msg )
            return False

    ###################################################################
    # Log the update in the "Notes" field
    ###################################################################
    def update_note_field( self, param_dict ):
        today, NULL = self.date_time()

        note_update = '\n' + today + ': Stream URL updated from:\n' + \
            param_dict['txtStreamUrl']

        if len( param_dict['txtNotes'] ) == 0:
            param_dict['txtNotes'] += note_update + '\n'
        else:
            param_dict['txtNotes'] += '\n' + note_update + '\n'


    ###################################################################
    # 
    ###################################################################
    def get_broadcast_date( self, param_dict ):
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
    # Create abbreviations for 
    ###################################################################
    def author_title( self, param_dict ):
        #TODO change function name
        regex = re.compile('[^a-zA-Z0-9]')
        author = param_dict['txtAuthor']
        author = regex.sub('',author)[:25]
        title = param_dict['txtTitle']
        title = regex.sub('',title)[:25]

        return author, title

    ###################################################################
    # Generate a new filename based on a predetermined format
    ###################################################################
    def filename_ext_new( self, param_dict, VID_ID ):
        col_dpts = self.h.col_dpts
        col_nums = self.h.col_nums
        dpt_num = param_dict['selDept']
        col_num = param_dict['selCollege']
        
        # https://stackoverflow.com/a/13149770/8878156
        for col, num in col_nums.items():
            if num == col_num:
                college = col

        for dpt_it, num in col_dpts[college].items():
            if num == dpt_num:
                dpt = dpt_it
        
        day, mon, yr = self.get_broadcast_date( param_dict )
        author, title = self.author_title( param_dict )

        old_stream = param_dict['txtStreamUrl']

        filename, extension = os.path.splitext(old_stream)

        dpt = self.abbrev(dpt)
        college = self.abbrev(college)
        
        # format of new filename
        # TODO: let the user decide this in the GUI
        filename = '{}{}{} - {} - {}_VID{}'.format( yr, mon, day, dpt, author,
                                                    VID_ID )
        new_path = 'BYU/' + college + '/' + dpt + '/' + yr + '/'

        return filename, extension, new_path

    #todo: what if a college has two departments with coinciding abbrevs?
    def abbrev( self, name ):
        # diff returns every element of l1 that is not found in l2
        diff = lambda l1,l2: [x for x in l1 if x not in l2]
        insig = ['&', 'and', 'of', 'for', 'to', 'the']
        subs = {
            'Science':'Sci',
            'Education':'Edu',
            'Center':'Ctr',
            'System':'Sys',
            'Systems':'Sys',
            'Biology':'Bio',
            'Engineering':'Eng',
            'Administration':'Admin',
            'School':'Sch',
            'Sciences':'Sci',
            'Technology':'Tech',
            'Mathematics':'Math',
            'Information':'Info',
            'Statistics':'Stat'
        }
        
        words = name.split()
        num_words = len(words)
        sig = diff(words,insig)
        num_sig_words = len(sig)

        abwords = []
        for word in words:
            if subs.get(word):
                word = subs[word]
            abwords.append(word)

        words = abwords
        abbrev_maxlen = 14
        abbrev = ''
        result = ''
        
        if num_words == 3:
            #todo - utilize all of the maximum length
            if words[1]=='and':
                # Spanish and Portuguese = SpanPort
                result = words[0][:4]+words[2][:4]
            elif words[0]=='Sch':
                # School of Technology = TechnolSch
                result = words[2][:abbrev_maxlen - len('Sch')]+words[0]
            else:
                for w in words:
                    abbrev += w[:1]
                result = abbrev

        elif num_words == 2:
            #Total length of end result will be 2 * max_word_len
            max_word_len = abbrev_maxlen // 2
            len0 = len(words[0])
            len1 = len(words[1])
            # if one word is less than max, give the difference to the other
            if len0 < max_word_len:
                diff = max_word_len - len0
                result = words[0] + words[1][:max_word_len + diff]
            elif len1 < max_word_len:
                diff = max_word_len - len1 
                result = words[0][:max_word_len + diff] + words[1]
            else:
                result = words[0][:max_word_len] + words[1][:max_word_len]
        
        elif num_sig_words == 1:
            # Neuroscience = Neuroscien
            result = words[0][:abbrev_maxlen]
        
        else:
            # Electrical and Computer Engineering = ECE
            # Romney Institute of Public Management = RIPM
            abbrev = ''
            for w in sig:
                abbrev += w[:1]
            result = abbrev

        result = result.replace('/','-')
        result = result.replace('\\','-')
        result = result.replace(':','-')
        
        valid = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = result
        result = ''.join(c for c in filename if c in valid)
        return result[:abbrev_maxlen]

    def test_abbrev( self ):
        col_dpts = self.h.col_dpts
        colleges = [i for i in col_dpts.keys()]
        dpts = [list(i.keys()) for i in list(col_dpts.values())]
        dpts.remove([]) #remove empty item from "Please select college" entry
        
        dpt_list = []
        for i in dpts:
            dpt_list += i

        print("COLLEGES")
        for col in colleges:
            col = col.replace('\r\n','')
            print("{} = {}".format(col, self.abbrev(col)))
            
        print("\nDEPARTMENTS")
        for i in dpt_list:
            print("{} = {}".format(i, self.abbrev(i)))

        
