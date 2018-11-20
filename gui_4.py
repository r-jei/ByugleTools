import sys
import Handler
import Renamer
from tkinter import _setit
from tkinter import *
from tkinter.filedialog import askopenfilename
import re
import shutil
import os

CHOOSE_COL = '*Please select your college'

class App:

    def __init__( self, root, un, pw ):
        self.h = Handler.Handler(un,pw)
        self.rn = Renamer.Renamer( self.h )

        
        self.top_frame = Frame(root)
        self.top_frame.pack()
        self.top_level( self.top_frame )
        
        self.l_frame = Frame( self.top_frame )
        self.r_frame = Frame( self.top_frame )
        
        self.l_frame.pack( side = LEFT )
        self.r_frame.pack( side = RIGHT )

        self.left_frame()

        self.right_frame()

    def top_level( self, top_frame ):
        self.ok_butt = Button( top_frame, text='ok', width=5, height=2,
                               command=lambda: print(self.build_dict()))
        self.ok_butt.pack( side=BOTTOM )

        star_txt = '* Indicates required fields'
        self.star_notice = Label( top_frame, text=star_txt, anchor='s' )
        self.star_notice.pack( side=BOTTOM )
        
        welcome = 'Access rules must be specified via the website.'
        lab = Label( top_frame, text = welcome )
        lab.pack()
        
    def right_frame( self ):
        self.citations, _ = self.entry_setup( self.r_frame, 'Citations:' )

        # "searchable until" date fields 
        su_frame = Frame( self.r_frame )
        
        su_frame.pack( side=TOP )
        su_date_lab = Label( su_frame, text = 'Searchable Until:' )
        su_date_lab.pack( side=LEFT )

        self.su_day_sv = StringVar()
        self.su_day_e = Entry( su_frame, textvariable=self.su_day_sv )

        self.su_mon_sv = StringVar()
        self.su_mon_e = Entry( su_frame, textvariable=self.su_mon_sv )

        self.su_yr_sv = StringVar()
        self.su_yr_e = Entry( su_frame, textvariable=self.su_yr_sv )

        self.temp_entry_setup( self.su_day_e, self.su_day_sv, su_frame, 'DD' )
        self.temp_entry_setup( self.su_mon_e, self.su_mon_sv, su_frame, 'MM' )
        self.temp_entry_setup( self.su_yr_e, self.su_yr_sv, su_frame, 'YYYY' )

        # "broadcast date" fields
        br_frame = Frame( self.r_frame )
        br_frame.pack( side=TOP )
        br_date_lab = Label( br_frame, text = 'Broadcast Date:' )
        br_date_lab.pack( side = LEFT )
        
        self.br_day_sv = StringVar()
        self.br_day_e = Entry( br_frame, textvariable=self.br_day_sv )

        self.br_mon_sv = StringVar()
        
        self.br_mon_e = Entry( br_frame, textvariable=self.br_mon_sv )

        self.br_yr_sv = StringVar()
        self.br_yr_e = Entry( br_frame, textvariable=self.br_yr_sv )
        
        self.temp_entry_setup( self.br_day_e, self.br_day_sv, br_frame, 'DD' )
        self.temp_entry_setup( self.br_mon_e, self.br_mon_sv, br_frame, 'MM' )
        self.temp_entry_setup( self.br_yr_e, self.br_yr_sv, br_frame, 'YYYY' )

        # "notes" field 
        notes_label = Label( self.r_frame, text='Notes:' )
        notes_label.pack( side=TOP )
        self.notes = Text( self.r_frame, borderwidth=3,relief=SUNKEN )
        self.notes.pack( side=TOP )

        # video file chooser 
        self.str_url, self.str_frame = self.entry_setup( self.r_frame,
                                                         'Video file:' )
        self.str_url.config( state=NORMAL )
        self.str_butt = Button( self.str_frame, text='Choose video file',
                                bg='gray63', height=2,
                                command = lambda entry=self.str_url:
                                self.open_file(entry) )
        self.str_butt.pack( side=LEFT )

        # "off-campus" streaming url 
        self.off_url, _ = self.entry_setup( self.r_frame,
                                         'Off-Campus Streaming URL:' )

        # thumbnail file chooser 
        self.thum_url, self.thum_frame = self.entry_setup( self.r_frame,
                                                            'Thumbnail file:' )
        self.thum_url.config( state=NORMAL)
        self.thum_butt = Button( self.thum_frame, text='Choose thumbnail file',
                                 bg='gray63', height=2,
                                 command = lambda entry=self.thum_url:
                                 self.open_file(entry))
        self.thum_butt.config( bg='gray63' )
        self.thum_butt.pack( side=LEFT )

        
        # episode metadata 
        self.episode, _ = self.entry_setup( self.r_frame, 'Episode Name:' )
        self.ep_no, _ = self.entry_setup( self.r_frame, 'Episode Number:' )
        
    def left_frame( self ):
        # CR approval
        self.cra_yes_butt, self.cra_no_butt, self.cra_var \
            = self.approval_radio_setup( self.l_frame )

        # CR approval number
        self.cr_no, _ = self.entry_setup( self.l_frame,
                                          'Copyright Approval #:' )

        # CR holder
        self.cr_holder, _ = self.entry_setup( self.l_frame,
                                              '*Copyright Holder:' )

        # title
        self.title, _ = self.entry_setup( self.l_frame, '*Title:' )

        # CR year
        self.cr_yr, _ = self.entry_setup( self.l_frame, '*Copyright Year:' )

        # author
        self.author, _ = self.entry_setup( self.l_frame, '*Author:' )

        # description field
        desc_label = Label( self.l_frame, text='*Description:' )
        desc_label.pack( side=TOP )
        self.desc = Text( self.l_frame, borderwidth=3, relief=SUNKEN )
        self.desc.pack( side=TOP )

        # duration time fields
        dur_frame = Frame( self.l_frame )
        dur_frame.pack( side=TOP )
        dur_date_lab = Label( dur_frame, text = '*Duration:' )
        dur_date_lab.pack( side = LEFT )
        
        self.dur_hr_sv = StringVar()
        self.dur_hr_e = Entry( dur_frame, textvariable=self.dur_hr_sv )

        self.dur_min_sv = StringVar()
        self.dur_min_e = Entry( dur_frame, textvariable=self.dur_min_sv )

        self.dur_sec_sv = StringVar()
        self.dur_sec_e = Entry( dur_frame, textvariable=self.dur_sec_sv )
        
        self.temp_entry_setup( self.dur_hr_e,
                               self.dur_hr_sv, dur_frame, 'HH' )
        self.temp_entry_setup( self.dur_min_e,
                               self.dur_min_sv, dur_frame, 'MM' )
        self.temp_entry_setup( self.dur_sec_e,
                               self.dur_sec_sv, dur_frame, 'SS' )

        # use constraints 
        self.constraints, _ = self.entry_setup( self.l_frame,
                                                'Use Constraints:' )

        # college options menu 
        self.col_var = StringVar()
        self.col_var.set( CHOOSE_COL )

        self.col_nums, self.col_dpts = self.h.get_col_info()
        
        popup_menu = OptionMenu(
            self.l_frame, self.col_var, *list(self.col_dpts.keys()),
            command = self.on_col_select
        )
        popup_menu.pack( side=TOP )

        # department options menu 
        self.dpt_var = StringVar()

        self.dpt_var.set( CHOOSE_COL )
        self.dpt_menu = OptionMenu(
            self.l_frame, self.dpt_var, ''
        )
        self.dpt_menu.pack( side=TOP )
        
    def on_col_select( self, col ):
        # reset var and delete old department list
        self.dpt_var.set('')
        self.dpt_menu['menu'].delete(0,'end')
        
        dpt_options = list(self.col_dpts[col].keys())

        if len(dpt_options) > 0:
            self.dpt_var.set(dpt_options[0])
            
        # insert list of new options
        for choice in dpt_options:
            self.dpt_menu['menu'].add_command(
                label=choice,
                command=_setit(
                    self.dpt_var,
                    choice
                )
            )
        
    def open_file( self, entry ):
        new = askopenfilename()
        if new:
            entry.delete(0,END)
            entry.insert( 0, new )
        
    def approval_radio_setup( self, parent ):
        cra_frame = Frame( parent )
        cra_frame.pack( side=TOP )
        cra_label = Label( cra_frame, text = '*Copyright Approval:' )
        cra_label.pack( side=LEFT )
        
        cra_var = IntVar(None,0)
        cra_yes_butt = Radiobutton( cra_frame, text='Yes', variable=cra_var,
                                   value=1 )
        cra_yes_butt.pack( side=LEFT )
        
        cra_no_butt = Radiobutton( cra_frame, text='No', variable=cra_var,
                                  value=0 )
        cra_no_butt.pack( side=RIGHT )
        return cra_yes_butt, cra_no_butt, cra_var
    
    def entry_setup( self, parent, title ):
        e_frame = Frame( parent )
        e_frame.pack( side=TOP )
        e = Entry( e_frame )
        tit = Label( e_frame, text = title )
        tit.pack( side=LEFT )
        e.pack( side=LEFT )
        return e, e_frame
        
    def temp_entry_setup( self, entry, sv, parent, temp_txt, digits=-1 ):
        if digits == -1:
            digits = len(temp_txt)
        if len(temp_txt) > digits:
            print('Note: length of temp_txt > field width')
                
        sv.set(temp_txt)
        
        sv.trace( 'w', lambda name, index, mode,
                    sv = sv: self.limit_chars( sv, digits ))
        
        entry.bind('<FocusIn>', lambda event, entry = entry, 
                    sv = sv: self.on_focus( entry, sv ))
        
        entry.bind('<FocusOut>', lambda event, entry = entry,
                    sv = sv: self.lose_focus( entry, sv, temp_txt))
        
        entry.config( fg='light gray', width = digits )
        entry.pack(side = LEFT)
        return entry, sv
        
    def limit_chars( self, sv, no_chars ):
        c = sv.get()[0:no_chars]
        digits_only = re.sub('[^0-9]','',c)
        sv.set( digits_only )
        
    def on_focus( self, entry, sv ):
        c = sv.get()
        digits_only = re.sub('[^0-9]','',c)
        sv.set( digits_only )
        entry.config( fg = 'black' )

    def lose_focus( self, entry, sv, txt ):
        if( len( sv.get() ) == 0 or sv.get() in ['DD','MM','YYYY'] ):
            sv.set(txt)
            entry.config( fg = 'light gray' )

    def build_dict( self ):
        dictionary = {}

        dictionary['radCopyright'] = self.cra_var.get()
        
        dictionary['txtAuthor'] = self.author.get()

        dictionary['txtBroadcastDay'] = self.br_day_sv.get()

        dictionary['txtBroadcastMon'] = self.br_mon_sv.get()

        dictionary['txtBroadcastYr'] = self.br_yr_sv.get()

        dictionary['txtCitations'] = self.citations.get()

        dictionary['txtConstraints'] = self.constraints.get()

        dictionary['txtCrApproveNum'] = self.cr_no.get()

        dictionary['txtCrHolder'] = self.cr_holder.get()

        dictionary['txtCrYear'] = self.cr_yr.get()

        dictionary['txtDescription'] = self.desc.get(1.0,END)

        dictionary['txtDurHrs'] = self.dur_hr_sv.get()

        dictionary['txtDurMin'] = self.dur_min_sv.get()

        dictionary['txtDurSec'] = self.dur_sec_sv.get()

        dictionary['txtEpisode'] = self.episode.get()

        dictionary['txtEpisodeNum'] = self.ep_no.get()

        dictionary['txtExpiresDay'] = self.su_day_sv.get()

        dictionary['txtExpiresMon'] = self.su_mon_sv.get()

        dictionary['txtExpiresYr'] = self.su_yr_sv.get()

        dictionary['txtNotes'] = self.notes.get(1.0,END)

        dictionary['txtTitle'] = self.title.get()

        college = self.col_var.get()
        dpt = self.dpt_var.get()
        
        dictionary['selCollege'] = self.col_nums[ college ]
        
        dictionary['selDept'] = self.col_dpts[college][dpt]
        
        dictionary['txtStreamUrl'] = self.str_url.get()
        vid_id = int(self.rn.PREV_VIDID) + 1
        filename, stream_ext, new_path = self.rn.filename_ext_new(
            dictionary, str(vid_id)
        )
        strm = new_path + filename + stream_ext
        dictionary['txtStreamUrl'] = strm

        dictionary['txtOffCampusStreamUrl'] = self.off_url.get()
        if not dictionary['txtOffCampusStreamUrl']:
            dictionary['txtOffCampusStreamUrl'] = \
                dictionary['txtStreamUrl']
        
        # TODO upload file to server, use its name
        PREFIX = 'http://videoweb.lib.byu.edu/images/'
        THUMB_DIR = 'BYU_thumbs'
        thumb = self.thum_url.get()
        thumb_ext = os.path.splitext(thumb)[1]
        dictionary['txtThumbUrl'] = PREFIX + new_path.replace('BYU',THUMB_DIR)\
            + filename + thumb_ext

        return dictionary

root = Tk()
root.resizable(0,0)
app = App(root,sys.argv[1],sys.argv[2])
root.mainloop()
