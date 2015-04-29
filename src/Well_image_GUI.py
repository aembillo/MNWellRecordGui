# Get the GUI stuff
import wx

# We're going to be handling files and directories
import os

# for manipulating pdf files
from pyPdf import PdfFileWriter, PdfFileReader      # license: modified BSD 
import numpy as np
import webbrowser        

from Get_Well_Record_Image import Well_image_grabber

__id_counter = 100
def new_id():
    global __id_counter
    __id_counter+=1
    return 0+__id_counter

# Set up some button numbers for the menu
ID_ABOUT   = new_id()
ID_INIT    = new_id()
ID_PDFDIR  = new_id()
ID_EXIT    = new_id()
ID_HELP    = new_id()


class MyFileDropTarget(wx.FileDropTarget):
    """ Manage file dropping onto the data panel 
    
    """
    def __init__(self, window, file_dropped_method):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.file_dropped_method = file_dropped_method
 
    def OnDropFiles(self, x, y, filenames):
        for file in filenames:
            self.file_dropped_method(file)

class MainWindow(wx.Frame):
    def __init__(self,parent):
        #self.initfile = "WellRecordGui.ini"
        self.initfile = os.path.join(os.getcwd(),"WellRecordGui.ini")  #Better,  dumps it in the root source code folder
        print 'inifile:  %s'%self.initfile
        
        title = "MNWell Record Viewer"
        wx.Frame.__init__(self,parent,wx.ID_ANY, title)

#         # Let's give the app a little color
#         self.label_color  = '#AAFFEE'
#         self.logbtn_color = '#80FFE6'
#         self.pdfbtn_color = '#AAFFCC'
#         self.pdfbtn_color2= '#80FFB3'

        # Add text editor windows and a status bar
        # Each of these is within the current instance
        # so that we can refer to them later.
        self.loglist_win = wx.TextCtrl(self, 1, style=wx.TE_MULTILINE)
        self.loglist_win.Bind(wx.EVT_ENTER_WINDOW, self.Enter_imagelist_window)

        self.pdfpagelist_win = wx.TextCtrl(self, 1, style=wx.TE_MULTILINE)
        self.pdfpagelist_win.Bind(wx.EVT_ENTER_WINDOW, self.Enter_pdfpagelist_window)
        self.output_win = wx.TextCtrl(self, 1, style=wx.TE_MULTILINE)
        self.output_win.Bind(wx.EVT_ENTER_WINDOW, self.Enter_output_window)
        
        self.status_bar = self.CreateStatusBar() # A Statusbar in the bottom of the window

        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(14)
        self.pdfpagelist_win.SetFont(font)
        self.output_win.SetFont(font)


        # Setting up the menu. filemenu is a local variable at this stage.
        filemenu= wx.Menu()
        # The & character indicates the short cut key
        filemenu.Append(ID_HELP, "&Help"," Instructions for use")
        filemenu.Append(ID_ABOUT, "&About"," Information about this program")
        filemenu.Append(ID_INIT, "&Initialize"," Initialze site logins")
        filemenu.Append(ID_PDFDIR, "&pdfDirectory"," Set directory for pdf files")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        # Note - previous line stores the whole of the menu into the current object

        # Define the code to be run when a menu option is selected
        wx.EVT_MENU(self, ID_HELP, self.OnHelp)
        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, ID_INIT, self.OnInit)
        wx.EVT_MENU(self, ID_PDFDIR, self.OnPdfDir)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)

       # Let's give the app a little color, where we can
        self.label_color  = '#AAFFEE'  # pale blue
        # 
        #self.MDH_color    = '#DDFFEE'  # very pale blue, almost white
        #self.MDH_color    = '#FFFFFF'  # white
        #self.MDH_color    = '#FFFFBB'  # Light yellow 
        self.MDH_color    = '#55FFEE'  # Light yellow 
        self.MGS_color    = '#FfFFEE'  # a light blue
        #self.CWI_color    = '#BBFFEE'  # very pale blue,  
        self.CWI_color    = '#FFFFBB'  # Light yellow 
        self.onbase_color = '#11FFEE'  # pale blue
        self.local_color  = '#EEEEAA'  # Light yellow 
        self.project_color= '#BBFFEE'
        #self.project_color= '#FFFFBB'  # Light yellow 
        self.pdfbtn_color = '#AAFFCC'
        self.pdfbtn_color2= '#80FFB3'

        # Buttons on the right, arranged     vertically, that are for selecting Well Record images.
        self.logbtn_sizer = wx.BoxSizer(wx.VERTICAL)
        btnlistW = (
            ('  Get MDH image  ', self.ButtonMDHlog, "up to 10 listed well id's from MGS", self.MDH_color),
            ('Get MGS image', self.ButtonMGSlog, "a single well id from MGS", self.MGS_color),
            ('Get CWI log', self.ButtonCWIlog, "a well log from CWI-on-line", self.CWI_color),
            ('Get CWI strat', self.ButtonCWIstrat, "a well stratigraphy log from CWI", self.CWI_color),
            ('Get OnBase image', self.ButtonOnBaseWellid, "well docs in OnBase by well_id", self.onbase_color),
            ('Get OnBase Local PLS', self.ButtonOnBaseLocal, "Local File docs in OnBase by Unique No or Twp Rng Section", self.local_color),
            ('Get OnBase Project', self.ButtonOnBaseProject, "project docs in OnBase by Project Name", self.project_color),
            ('Get Project maps', self.ButtonOnBaseProjectMap, "Project maps & inspections in OnBase by Project Name", self.project_color),
            ('Get Project year', self.ButtonOnBaseProjectYear, 'Registered docs in OnBase by "Project Name Year" (e.g. "FHR 2010")', self.project_color),
            #('Get em ALL', self.ButtonALLlogs, "all related documents" ),
        )
        for label,method,tip,color in btnlistW:
            id = new_id()
            btn = wx.Button(self, id, label)
            btn.Bind(wx.EVT_BUTTON, method)
            btn.Bind(wx.EVT_ENTER_WINDOW, self.Enter_image_button_area)
            btn.SetToolTip(wx.ToolTip("Click to find %s"%tip))
            btn.SetBackgroundColour(color)
            self.logbtn_sizer.Add(btn,1,wx.EXPAND)


        # Buttons on the right, vertically, that are drop-file areas for existing pdf files.
        self.pdfbtnR_sizer = wx.BoxSizer(wx.VERTICAL)
        self.pdfbtnL_sizer = wx.BoxSizer(wx.VERTICAL)

        btnlist1 = (
            ('    Page 1    '  , self.ButtonP1, self.pdfbtnR_sizer ),
            ('Page 2', self.ButtonP2, self.pdfbtnR_sizer ),
            ('Page 3', self.ButtonP3, self.pdfbtnR_sizer ),
            ('Page 4', self.ButtonP4, self.pdfbtnR_sizer ),
            ('Custom', self.ButtonCustomRange, self.pdfbtnL_sizer ),
        )
        for label,method,sizer in btnlist1:
            id = new_id()
            btn = wx.Button(self, id, label)
            btn.Bind(wx.EVT_BUTTON, method)
            dt = MyFileDropTarget(self,method)
            btn.SetDropTarget(dt)
            btn.Bind(wx.EVT_ENTER_WINDOW, self.Enter_page_button_area)
            btn.SetBackgroundColour(self.pdfbtn_color)
            sizer.Add(btn,1,wx.EXPAND)

        # 4 more specialized buttons are needed for the pdf files:
        id = new_id()
        self.build_button = wx.Button(self, id, 'Build')
        self.build_button.Bind(wx.EVT_BUTTON, self.ButtonBuild)
        self.build_button.Bind(wx.EVT_ENTER_WINDOW, self.Enter_build_button_area)
        self.build_button.SetToolTip(wx.ToolTip("Click to begin building a merged document."))
        self.build_button.SetBackgroundColour(self.pdfbtn_color)
        self.pdfbtnL_sizer.Add(self.build_button,1,wx.EXPAND)
        
        id = new_id()
        self.publish_button = wx.Button(self, id, 'Publish')
        self.publish_button.Bind(wx.EVT_BUTTON, self.ButtonPublish)
        self.publish_button.Bind(wx.EVT_ENTER_WINDOW, self.Enter_build_button_area)
        #self.publish_button.SetToolTip(wx.ToolTip("Click to begin building a merged document."))
        self.publish_button.SetBackgroundColour(self.pdfbtn_color)
        self.pdfbtnL_sizer.Add(self.publish_button,1,wx.EXPAND)
        self.publish_button.Disable()

        id = new_id()
        self.cancel_button = wx.Button(self, id, 'CANCEL')
        self.cancel_button.Bind(wx.EVT_BUTTON, self.ButtonCancel)
        self.cancel_button.Bind(wx.EVT_ENTER_WINDOW, self.Enter_build_button_area)
        self.cancel_button.SetToolTip(wx.ToolTip("Click to Cancel and abort Build."))
        self.cancel_button.SetBackgroundColour(self.pdfbtn_color)
        self.pdfbtnL_sizer.Add(self.cancel_button,1,wx.EXPAND)
        self.cancel_button.Disable()

        self.pdfbtn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pdfbtn_sizer.Add(self.pdfbtnL_sizer ,0,wx.EXPAND)
        self.pdfbtn_sizer.Add(self.pdfbtnR_sizer ,0,wx.EXPAND)
        
        

        self.logio_sizer  = wx.BoxSizer(wx.VERTICAL)
        self.logio_sizer.Add(wx.StaticText(self, label="Enter well identifiers here"))
        self.logio_sizer.Add(self.loglist_win,2,wx.EXPAND)
        self.logio_sizer.Add(wx.StaticText(self, label="Output:"))
        self.logio_sizer.Add(self.output_win,3,wx.EXPAND)

        self.log_sizer= wx.BoxSizer(wx.HORIZONTAL)
        self.log_sizer.Add(self.logio_sizer ,1,wx.EXPAND)
        self.log_sizer.Add(self.logbtn_sizer,0,wx.EXPAND)
        
        #self.logio_sizer.Add(self.logoutput_win,1,wx.EXPAND)

        # Set up the overall frame vertically - text edit window above buttons
        # We want to arrange the buttons vertically below the text edit window

        
        self.pdfio_sizer  = wx.BoxSizer(wx.VERTICAL)
        label = "Drag a pdf file onto a button at the right to split off the indicated page.\nEnter custom pdf file page range below: e.g. 1,2,5-8,15"
        self.pdfio_sizer.Add(wx.StaticText(self, label=label))
        self.pdfio_sizer.Add(self.pdfpagelist_win,1,wx.EXPAND)

        self.pdf_sizer= wx.BoxSizer(wx.HORIZONTAL)
        self.pdf_sizer.Add(self.pdfio_sizer ,1,wx.EXPAND)
        self.pdf_sizer.Add(self.pdfbtn_sizer,0,wx.EXPAND)

        self.main_sizer= wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.log_sizer,2,wx.EXPAND)
        self.main_sizer.Add(self.pdf_sizer,1,wx.EXPAND)
        

        # Tell it which sizer is to be used for main frame
        # It may lay out automatically and be altered to fit window
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(1)
        self.main_sizer.Fit(self)
        self.SetSize((500,450))
        #self.SetBackgroundColour('#D5FFE6')
        self.SetBackgroundColour(self.label_color)
        #self.SetForegroundColour('#D5FFE6')
        #self.SetOwnBackgroundColour('#D5FFE6')

        # Show it !!!
        self.Show(1)
        
        
        # initialize message text and input and output window values
        self.prepare_messages()
        self.loglist_win.SetValue("<Unique numbers or well_id's here>")
        self.pdfpagelist_win.SetValue("<Enter custom pdf file page ranges here>")
        self.output_win.SetValue(self.help_text )
        self.output_status_text = 'Results display here'
        
        self.build_mode = False
        self.build_output = None

        self.image_grabber = Well_image_grabber(self.initfile)
        self._init_wellman_ids()
        self.init_wellman_projectnames()

        #  wx.StaticText(self, label="Your name :")

    def prepare_messages(self):
        import platform
        self.about_me_text = '\n'.join((
                   'MN Well Record Viewer version 0.1',
                   '  Graphical tools for',
                   '    accessing well records, and',   
                   '    splitting and merging pdf files.',
                   ' ',
                   '  Python version: %s'%platform.python_version(),
                   '  Based on the libraries:',
                   '    %s'%(PdfFileReader.__name__),
                   '    %s'%(PdfFileWriter.__name__),                  
                   ))
#         self.general_instruction_text = (
#             'Paste a valid checksum value in the upper window, and drag the file onto a button')
        self.specific_instruction_text = (
            'Enter a valid page range into the upper window, then drag a pdf file onto the Custom button.')
        self.help_text = (
            '   To retrieve well log images, or CWI database well logs, '+\
            'enter a unique number, well_id, or RELATEID in the top window, '+\
            'and select a button to the right.\n'+\
            '   Documents returned as pdf files can be modified with the pdf tools below. '+\
            'The tools perform split and merge of specified pages of pdf files. '+\
            'Drag an input file onto the one of the page range buttons, and it will split '+\
            'off the indicated page to a new file. '+\
            'New documents are named after the old one with a suffix indicating the page number.\n'+\
            '   Use the Custom button to split off 2 or more pages together; '+\
            'enter the page or page range in the lower window using commas and dashes.\n'+\
            '   Begin merging pages from two or more pdf files by pressing the Build button. '+\
            'Then add pages as described above, and press the Publish button to finish. '+\
            '(No pdf documents will be overwritten.)') 
        
        
#     def compute_checksum(self,fname,block_size=2**20,method='SHA1'):        
#         if   method=="MD5"    : hasher = hashlib.md5()  
#         elif method=="SHA1"   : hasher = hashlib.sha1()  
#         elif method=="SHA224" : hasher = hashlib.sha224()  
#         elif method=="SHA256" : hasher = hashlib.sha256()  
#         elif method=="SHA384" : hasher = hashlib.sha384()  
#         elif method=="SHA512" : hasher = hashlib.sha512()  
#         else: return "Hash method not recognized: %s"%method 
#     
#         try:
#             f = open( fname, 'r' )
#             while True:         
#                 data = f.read(block_size)         
#                 if not data:             
#                     break         
#                 hasher.update(data)   
#             f.close()  
#             return hasher.hexdigest() 
#         except:
#             return 'Unable to compute hash for file %s'%fname

#     def pdf_split_one_page(self,infile,outfile,pagenum):
#         # split off selected pagenum from infile as outfile.
#         # infile and outfile are .pdf.  the first page is pagenum=1
#         # Page 1 uses pagenum=1, and pythonic page number = 0
#         #fin = r"E:\bill\scratch\A.pdf"
#         input1 = PdfFileReader(file(infile, "rb"))
#         
#         infile_pages = input1.getNumPages()
#         if infile_pages < pagenum:
#             self.show_output("ERROR -- Document %s has only %i pages."%(infile, infile_pages))
#             return
#         
#         fout = r"E:\bill\scratch\Asplit.pdf"
#         output = PdfFileWriter()
#         
#         # add selected page from input1 to output document, unchanged
#         pypagenum = pagenum-1
#         output.addPage(input1.getPage(pypagenum))
# 
#         outputStream = file(outfile, "wb")
#         output.write(outputStream)
#         outputStream.close()
# 
#         self.show_output("Page %i of  %s \nwritten to  %s."%(pagenum,infile, outfile))
#         return
# 
#         
# #         # add page 2 from input1, but rotated clockwise 90 degrees
# #         output.addPage(input1.getPage(1).rotateClockwise(90))
# #         
# #         # add page 3 from input1, rotated the other way:
# #         output.addPage(input1.getPage(2).rotateCounterClockwise(90))
# #         # alt: output.addPage(input1.getPage(2).rotateClockwise(270))
# #        
#         # # add page 4 from input1, but first add a watermark from another pdf:
#         # page4 = input1.getPage(3)
#         # watermark = PdfFileReader(file("watermark.pdf", "rb"))
#         # page4.mergePage(watermark.getPage(0))
#         # 
#         # # add page 5 from input1, but crop it to half size:
#         # page5 = input1.getPage(4)
#         # page5.mediaBox.upperRight = (
#         #     page5.mediaBox.getUpperRight_x() / 2,
#         #     page5.mediaBox.getUpperRight_y() / 2
#         # )
#         # output.addPage(page5)
# #        
#         # print how many pages input1 has:
#         # print "%s has %s pages." % (fin,input1.getNumPages() )
# #        
#         # finally, write "output" to document-output.pdf
# #         outputStream = file(outfile, "wb")
# #         output.write(outputStream)
# #         outputStream.close()
# #         
# #         print "%s has been written"%fout
# 
#     def pdf_split_n_pages(self,infile,outfile,pagelist):
#         input1 = PdfFileReader(file(infile, "rb"))
#         
#         infile_pages = input1.getNumPages()
#         if infile_pages < np.max(pagelist):
#             self.show_output("ERROR -- Document %s has only %i pages."%(infile, infile_pages))
#             return
#         
#         fout = r"E:\bill\scratch\Asplit.pdf"
#         output = PdfFileWriter()
#         
#         # add selected page from input1 to output document, unchanged
#         pypagenum = pagenum-1
#         output.addPage(input1.getPage(pypagenum))
# 
#         outputStream = file(outfile, "wb")
#         output.write(outputStream)
#         outputStream.close()
# 
#         self.show_output("Page %i of  %s \nwritten to  %s."%(pagenum,infile, outfile))
#         return
#         

    def _init_wellman_ids(self, fname=r'T:\Wells\ImageViewerData\well_ids.csv'):
        f = open(fname)
        rows = f.read()
        f.close
        self.wellman_ids = {}
        for row in rows.split('\n')[:-1]:
            row = row.split(',')
            self.wellman_ids[row[0][1:-1].strip()] = row[1].strip()   
        print 'Initialized well ids from %s.\n    %i records read into dictionary.'%(fname,len(self.wellman_ids) )             
    
    def init_wellman_projectnames(self,fname = r'T:\Wells\ImageViewerData\projectnames.csv'):
        f = open(fname)
        rows = f.read()
        f.close
        self.wellman_projectnames = []
        for row in rows.split('\n'):
            val = row[1:-1].strip()
            if val:
                self.wellman_projectnames.append(val)

    def _split_dropped_file(self,infname, pagelist=None, rotates=None):
        # pages is a string like '1,2,None' meaning from page 1 to page 2 rotate None
        if pagelist is None:
            return
        if str(type(infname)) == "<class 'wx._core.CommandEvent'>":
            # catch a button click as opposed to a dropped file event.
            self.show_output("Drag source file onto this button to extract page(s) %s"%pagelist)
            return
        self.clear_txt_win(self.output_win)
        if not type(infname) == type(u'a'): 
            self.output_win.SetBackgroundColour('white')
            self.show_output("Unable to interpret filename: %s"%infname)
            return
        try:
            input1 = PdfFileReader(file(infname, "rb"))
        except:
            self.show_output('Error. Input file may have corruption: %s'%infname)
            return
       
        # validate page range
        infile_pages = input1.getNumPages()
        if (np.min(pagelist) <= 0) or (infile_pages < np.max(pagelist)):
            self.show_output("ERROR -- Document %s has %i pages. Cannot print range %s"%(infname, infile_pages, pagelist))
            return
        
        # Validate that input file has extension pdf, and get the base name
        basename,ext = os.path.splitext(infname)
        if not ext == '.pdf':  
            self.output_win.SetBackgroundColour('white')
            self.show_output("Input file is not a pdf file")
            return

        # Create the output name: concatination of basename and output pages
        outfname = "%s_%s.pdf"%(basename, "_".join(str(p) for p in pagelist) )
        
        self.show_output("Preparing to split out pages %s\nfrom file   %s"%(pagelist,infname))

        output = PdfFileWriter()
        
        # add selected page from input1 to output document, (first page has index 0)
        for p in pagelist:
            output.addPage(input1.getPage(p-1))
            
        outputStream = file(outfname, "wb")
        output.write(outputStream)
        outputStream.close()

        self.show_output("Reading:   %s  Writing: %s\n  Page(s): %s"%(infname, outfname, pagelist))
        return
        
    def _append_dropped_file(self,infname, pagelist=None, rotates=None):
        # pages is a string like '1,2,None' meaning from page 1 to page 2 rotate None
        if str(type(infname)) == "<class 'wx._core.CommandEvent'>":
            # catch a button click as opposed to a dropped file event.
            self.show_output("Drag source file onto this button to extract page(s) %s"%pagelist)
            return
        print '_append_dropped_file (%s)'%infname
        if pagelist is None:
            return
        if not type(infname) == type(u'a'): 
            self.output_win.SetBackgroundColour('white')
            #self.show_output("\nUnable to interpret filename:: %s"%infname, append=True)
            return
        input1 = PdfFileReader(file(infname, "rb"))
       
        # Validate that input file has extension pdf, and get the base name
        basename,ext = os.path.splitext(infname)
        if not ext == '.pdf':  
            self.output_win.SetBackgroundColour('white')
            self.show_output("Input file is not a pdf file", append=True)
            return
        self.basedir = os.path.dirname(infname)
        
        # validate page range
        infile_pages = input1.getNumPages()
        if (np.min(pagelist) <= 0) or (infile_pages < np.max(pagelist)):
            self.show_output("\nERROR -- Document has %i pages. Cannot print range %s"%(infile_pages, pagelist), append=True)
            return
        
        if len(pagelist) == 1:
            #self.build_pages += 1
            self.show_output("Appending page %s from %s"%(pagelist,infname), append=True)
        else:
            #self.build_pages += len(pagelist)
            self.show_output("Appending pages %s from %s"%(pagelist,infname), append=True)
        
        # add selected page from input1 to output document, (first page has index 0)
        for p in pagelist:
            self.build_output.addPage(input1.getPage(p-1))
            self.build_pagecount += 1


    def _publish(self):
        if self.build_output:
            if not self.build_pagecount > 0:
                self.show_output("There are no pages to publish")
                return False
            dlg = wx.FileDialog(self, "Choose destination file",
                                self.basedir, style=wx.SAVE | wx.OVERWRITE_PROMPT, 
                                wildcard="PDF files (*.pdf)|*.pdf" )
            if dlg.ShowModal() == wx.ID_OK:
                outfname = dlg.GetPath()
                os.path.splitext(outfname)
                if not os.path.splitext(outfname)[1]:
                    outfname += ".pdf"
                elif not (os.path.splitext(outfname)[1] == ".pdf"):
                    outfname = os.path.splitext(outfname)[0] + ".pdf"
                #print "dlg OK: fname = %s"%outfname
            else:
                #print "dlg not OK"
                return False
            dlg.Destroy()
            #except:
            #    return
            outputStream = file(outfname, "wb")
            self.build_output.write(outputStream)
            outputStream.close()

            self.build_output = None
            self.build_mode = False
            self.show_output("Written to:  %s"%(outfname))
            self.build_pagecount = 0
            
            return True
                
    def _read_log_win_plain(self):
        rv = self.loglist_win.GetValue()     
        return rv
           
    def _read_log_win(self):
        text_list = self.loglist_win.GetValue()
        text_list.replace(',',' ')
        loglist = text_list.split()
        if (loglist.count>0):
            return loglist
        else:
            return None

    def ButtonMDHlog(self,event):
        #print 'ButtonMDHlog'
        loglist = self._read_log_win()
        #print 'MDH loglist:',loglist
        OK,fname = self.image_grabber.get_MDH_image(loglist)
        if OK: 
            self.show_output('MDH image: \n%s'%fname, append=False)
            webbrowser.open_new_tab(fname) 
        else:
            self.show_output(fname, append=False)   
    def ButtonMGSlog(self,event):
        #print 'ButtonMGSlog'        
        loglist = self._read_log_win()
        #print 'MGS loglist:',loglist[0]
        OK,fname = self.image_grabber.get_MGS_image(loglist[0])
        if OK: 
            self.show_output('MGS image: "%s"'%fname, append=False)
            webbrowser.open_new_tab(fname)    
        else:
            self.show_output('MGS image "%s" not found'%loglist[0])
            
            
    def ButtonCWIlog(self,event):
        #print 'ButtonCWIlog'        
        loglist = self._read_log_win()
        #print 'loglist:',loglist
        url = self.image_grabber.get_CWI_log(loglist[0])
        #print 'url= "%s"'%url
        if (url):
            self.show_output('CWI log found: "%s"'%loglist[0], append=False)
            webbrowser.open_new_tab(url) 
    def ButtonCWIstrat(self,event):
        #print 'ButtonCWIstrat'        
        loglist = self._read_log_win()
        url = self.image_grabber.get_CWI_log(loglist[0],Type="STRAT")
        if (url):
            self.show_output('CWI strat log found: "%s"'%loglist[0], append=False)
            webbrowser.open_new_tab(url) 
    def ButtonOnBaseWellid(self,event):
        #print 'ButtonCWIstrat'        
        loglist = self._read_log_win()
        try:
            id = loglist[0].strip()
            print 'searching OnBase for id "%s"'%id,
            wid = self.wellman_ids.get(id,id)  #if id is found in the wellman_ids dictionary, then return the associated id.
            print ', mapped to id "%s"'%wid
            url = self.image_grabber.get_OnBase_images(wid,'DAKCO_OnBase_well_id_url') 
        except:
            self.show_output('Well id must be an integer', append=False)
        if (url):
            self.show_output('OnBase docs found: "%s"'%loglist[0], append=False)
            webbrowser.open_new_tab(url) 

        
    def ButtonOnBaseLocal(self,event):
        #print 'ButtonOnBaseLocal'        
        ''' if txt is Twp Rng Section, e.g. "27 19 2", change to std fmt "027 09 02"
            otherwise assume it is a unique number.
        '''
        txt = self._read_log_win_plain()
        try:
            t,r,s = txt.strip().replace('-',' ').split()
            PLS = '%03d+%02d+%02d'%(int(t),int(r),int(s))
            assert len(PLS) == 9 
            url = self.image_grabber.get_OnBase_images(PLS,'DAKCO_OnBase_twp_rng_sec_url')
            txt = PLS
            msg = 'OnBase Local docs found by Unique: %s'%txt + '\n' +url
        except:
            txt = txt.strip().split()[0] 
            if len(txt) <= 7:
                url = self.image_grabber.get_OnBase_images(txt,'DAKCO_OnBase_well_unique_url')
                msg =  'OnBase Local records found for Twp Rng Section: %s '%txt + '\n' +url
            else:
                self.show_output('Must enter Unique number, or Twp Rng Sec as "27 22 4"', append=False)
                return
        if (url):
            self.show_output(msg, append=False)
            print url
            print 'http://EDWEB3/AppNet/docpop/docpop.aspx?KT942_0_0_0=027+23+09&clienttype=activex&keytype='
            OK = webbrowser.open_new_tab(url) 
            print 'webbrowser.open_new_tab(url) = %s'%(OK)

    def ButtonOnBaseProject(self,event):
        #print 'ButtonCWIstrat'        
        projectname = self._read_log_win_plain()
        if not projectname:
            return
        url = self.image_grabber.get_OnBase_project(projectname, projectyear=None, doctype=None)  
        print url
        if (url):
            self.show_output('OnBase docs found for"%s"'%projectname, append=False)
            webbrowser.open_new_tab(url) 
        else:
            self.show_output('No OnBase docs for "%s"'%projectname, append=False)

    def ButtonOnBaseProjectMap(self,event):
        #print 'ButtonOnBaseProjectMap'        
        projectname = self._read_log_win_plain()
        if not projectname:
            return

        url = self.image_grabber.get_OnBase_project(projectname, projectyear=None, doctype="MAP")  
        print url        
        if (url):
            self.show_output('OnBase docs found for"%s"'%projectname, append=False)
            webbrowser.open_new_tab(url) 
        else:
            self.show_output('No OnBase Project Maps for "%s"'%projectname, append=False)

    def ButtonOnBaseProjectYear(self,event):
        try:
            args = self._read_log_win_plain().split()
            projectyear = args[-1]
            projectname = ' '.join(args[:-1])
        except:
            return
        url = self.image_grabber.get_OnBase_project(projectname, projectyear=projectyear, doctype=None)  
        print url        
        if (url):
            self.show_output('OnBase docs found for"%s"'%projectname, append=False)
            webbrowser.open_new_tab(url) 
        else:
            self.show_output('No OnBase Project Maps for "%s"'%projectname, append=False)
            
            
#     def ButtonProject(self,event):
#         self.show_output('Project not implemented', append=False)
#         return 
#         loglist = self._read_log_win()
#         url = self.image_grabber.get_OnBase_images(loglist[0]) 
#         if (url):
#             self.show_output('OnBase docs found: "%s"'%loglist[0], append=False)
#             webbrowser.open_new_tab(url) 
# 
#     def ButtonProjectMap(self,event):
#         self.show_output('Project-Map not implemented', append=False)
#         return 
#         loglist = self._read_log_win()
#         url = self.image_grabber.get_OnBase_images(loglist[0]) 
#         if (url):
#             self.show_output('OnBase docs found: "%s"'%loglist[0], append=False)
#             webbrowser.open_new_tab(url) 
# 
#     def ButtonProjectYear(self,event):
#         self.show_output('Project-Year not implemented', append=False)
#         return 
#         loglist = self._read_log_win()
#         url = self.image_grabber.get_OnBase_images(loglist[0]) 
#         if (url):
#             self.show_output('OnBase docs found: "%s"'%loglist[0], append=False)
#             webbrowser.open_new_tab(url) 


    def ButtonALLlogs(self,event):
        print 'ButtonALLlogs'        

    def ButtonP1(self,fname):
        if self.build_mode: self._append_dropped_file(fname, pagelist=[1])
        else:                self._split_dropped_file(fname, pagelist=[1])

    def ButtonP2(self,fname):
        if self.build_mode: self._append_dropped_file(fname, pagelist=[2])
        else:                self._split_dropped_file(fname, pagelist=[2])
   
    def ButtonP3(self,fname):
        if self.build_mode: self._append_dropped_file(fname, pagelist=[3])
        else:                self._split_dropped_file(fname, pagelist=[3])
   
    def ButtonP4(self,fname):
        if self.build_mode: self._append_dropped_file(fname, pagelist=[4])
        else:                self._split_dropped_file(fname, pagelist=[4])

    def ButtonCustomRange(self,fname):
        """ Comma separated list of pages or ascending page ranges. A range is created with a dash.
            e.g. "1" or "1,3-8" or "1,2,5-8,12-25,9"    
            Not OK: "8-6" (a descending range)
        """ 
        try:
            user_pages = self.pdfpagelist_win.GetValue()
            ranges = (x.split("-") for x in user_pages.split(","))
            pagelist = np.array([i for r in ranges for i in range(int(r[0]), int(r[-1]) + 1)])
        except:
            self.show_output('Unable to interpret page list, no action taken:\n"%s"'%user_pages)
        
        try:    
            if self.build_mode: 
                self._append_dropped_file(fname, pagelist=pagelist)
            else:                
                self._split_dropped_file(fname, pagelist=pagelist)
        except:
            print "shouldnt get here", fname
            

            

    def ButtonBuild(self,event):
        if not self.build_mode:
            self.show_output("Begin adding pages by dragging documents onto Page buttons.")
            self.build_mode = True
            self.build_pagecount = 0
            self.build_output = PdfFileWriter()
            self.publish_button.Show()
            self.build_button.Disable()
            self.cancel_button.Enable()
            self.publish_button.Enable()
            self.cancel_button.SetBackgroundColour(self.pdfbtn_color2)
            self.publish_button.SetBackgroundColour(self.pdfbtn_color2)

    def ButtonCancel(self,event):
        if self.build_mode:
            self.show_output("Build canceled.")
            self.build_mode = False
            self.build_pagecount = 0
            self.build_output = None
            self.build_button.Enable()
            self.cancel_button.Disable()
            self.publish_button.Disable()
            self.cancel_button.SetBackgroundColour(self.pdfbtn_color)
            self.publish_button.SetBackgroundColour(self.pdfbtn_color)
#             
#         else:
#             self.show_output("Begin adding pages by dragging documents onto Page buttons.")
#             self.build_mode = True
#             self.build_output = PdfFileWriter()
#             self.publish_button.Show()

    def ButtonPublish(self,event):
        if self.build_mode:
            self.show_output("Publishing.",append=True)
            if self._publish():
                self.build_mode = False
                self.build_output = None
                self.build_button.Enable()
                self.cancel_button.Disable()
                self.publish_button.Disable()
                self.cancel_button.SetBackgroundColour(self.pdfbtn_color)
                self.publish_button.SetBackgroundColour(self.pdfbtn_color)
        else:
            self.show_output("No action. Not in Build mode.")

    
    def Enter_imagelist_window(self,event):
        self.status_bar.SetStatusText('Well record number(s) or well_id')
        event.Skip()

    def Enter_pdfpagelist_window(self,event):
        self.status_bar.SetStatusText('Enter page numbers to split out or merge')
        event.Skip()

#     def Enter_target_dir_window(self,event):
#         self.status_bar.SetStatusText('Change the destination directory')
#         event.Skip()

    def Enter_image_button_area(self,event):
        self.status_bar.SetStatusText('Search for the well record numbers in the search window.')
        
    def Enter_output_window(self,event):
        self.status_bar.SetStatusText(self.output_status_text)
        event.Skip()
        
    def Enter_page_button_area(self, event):
        if self.build_mode:
            self.status_bar.SetStatusText('Drag the file onto the button to APPEND indicated pages.')
        else:
            self.status_bar.SetStatusText('Drag the file onto the button to SPLIT OFF indicated pages.')
        event.Skip()

    def Enter_build_button_area(self, event):
        if self.build_mode:
            self.status_bar.SetStatusText('Build mode ON. CANCEL to abort. Publish to finish.')
        else:
            self.status_bar.SetStatusText('Split mode ON. Click on Build to start build mode.')
        event.Skip()


    #text_list = self.pdfpagelist_win.GetValue()
    def show_output(self,new_txt,append=False):
        #print ' append = %s'%append
        #print 'new_txtA = "%s"'%new_txt
        if append:
            old_txt = self.output_win.GetValue()
            #print 'old_txt  = "%s"'%old_txt
            new_txt = '%s\n%s'%(old_txt,new_txt)
        #print 'new_txtB = "%s"'%new_txt
        self.output_win.SetValue(new_txt)

#     def _get_pagelist(self):
#         in_txt = self.pdfpagelist_win.GetValue()
#         for d in ' ,':
#             if d in in_txt:
#                 pagelist = np.array(s.split(d),dtype=int)
#                 return pagelist

    def clear_txt_win(self, thewin):
        thewin.SetValue("")
            
    def write_to_clipboard(self,thetext):
        if not wx.TheClipboard.IsOpened():  # may crash, otherwise
            clipdata = wx.TextDataObject()
            clipdata.SetText(thetext)
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()

    def OnHelp(self,e):
        self.show_output(self.help_text)

    def OnAbout(self,e):
        self.aboutme = wx.MessageDialog( self, self.about_me_text, "About Well_Image_GUI.py", wx.OK)
        self.aboutme.ShowModal() 

    def OnInit(self,e):
        """ we'll use the log window to read in the initialization strings, but we will not parse it 
            the usual way, so we'll read it in raw
        """
        initstring = self.loglist_win.GetValue()
        OK,msg = self.image_grabber.initialze_logins(initstring)
        self.show_output(msg, append=False)

    def OnPdfDir(self,e):
        """ user selects the directory for dumping pdf files  
            
            default name is obtained from the image_grabber (which reads it from the .ini file)
            new name is sent to the image_grabber to manage.
        """
        pdfdir = self.image_grabber.get_pdfdir()
#         pdfdir = self.image_grabber.userdict[pdfdirkey]
#         pdfdir = self.prefix
        if not pdfdir:
            pdfdir = os.curdir

        dlg = wx.FileDialog(self, "Choose directory for downloaded images that are pdf files.",
                    pdfdir, style=wx.FD_CHANGE_DIR, 
                    wildcard="Temp dir for PDF files (*.*)|*.*" )
        if dlg.ShowModal() == wx.ID_OK:
            print 'dlg.GetPath()',dlg.GetPath()
            #pdfpath = os.path(dlg.GetPath())
            pdfdir = os.path.dirname(dlg.GetPath())
            self.image_grabber.userdict["temp_file_path"] = pdfdir
            self.image_grabber.prefix = pdfdir
            print "dlg OK: fname = %s"%pdfdir
        else:
            print "dlg not OK"
            return False
        dlg.Destroy()
        msg = self.image_grabber.set_pdfdir(pdfdir)
        if msg:
            self.show_output(msg, append=False)

    def OnExit(self,e):
        # Exit without comment or double check
        self.Close(True)  # Closes out this simple application



# Set up a window based app, and create a main window in it
app = wx.PySimpleApp()
view = MainWindow(None)
# Enter event loop
app.MainLoop()