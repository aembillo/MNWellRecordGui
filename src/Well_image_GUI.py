'''
    Modified 2016-01-19 to latest MWI urls.  
        Added 'INDEX' option
        coded 'MAP' option, but it does not work, so commented out.
'''
# Get the GUI stuff
import wx

# We're going to be handling files and directories
import os

# for manipulating pdf files
from pyPdf import PdfFileWriter, PdfFileReader      # license: modified BSD 
import webbrowser        

from Get_Well_Record_Image import Well_image_grabber
from Wellman_odbc import WellmanConnection

#TODO notes
# controlling the browser zoom problem
#  problem noted:  http://stackoverflow.com/questions/28370725/wpf-web-browser-control-inheriting-internet-explorer-zoom-level
#  use mechanize?:  http://www.pythonforbeginners.com/mechanize/browsing-in-python-with-mechanize/

# VERSION_NUMBER = '0.3  2015'
VERSION_NUMBER = '1.2  2016-05-04'

__id_counter = 100
def new_id():
    global __id_counter
    __id_counter+=1
    return 0+__id_counter

# Set up some button numbers for the menu
ID_ABOUT   = new_id()
ID_INIT    = new_id()
ID_PASS    = new_id()
ID_PDFDIR  = new_id()
ID_EXIT    = new_id()
ID_HELP    = new_id()
ID_HELP_PDF    = new_id()
ID_HELP_COORDS = new_id()
ID_DEBUG   = new_id()


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
        self.DEBUG = False
        self.initfile = os.path.join(os.getcwd(),"WellRecordGui.ini")  #Better,  dumps it in the root source code folder
        print 'inifile:  %s'%self.initfile
        startup_msg = 'Startup messages:\n'
        
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


        # Setting up the menu. mainmenu is a local variable at this stage.
        mainmenu= wx.Menu()
        helpmenu= wx.Menu()
        # The & character indicates the short cut key
        helpmenu.Append(ID_HELP, "&Help"," Instructions for use")
        helpmenu.Append(ID_HELP_PDF, "Help with &PDF files"," Instructions for use")
        helpmenu.Append(ID_HELP_COORDS, "&Help with &Coordinate Transformations"," Instructions for use")
        helpmenu.Append(ID_ABOUT, "&About"," Information about this program")
        #helpmenu.Append(ID_DEBUG, "&Debug"," Toggle Debugging")
        mainmenu.Append(ID_PASS, "&Logins"," Initialze Site logins")
        mainmenu.Append(ID_INIT, "&Re-Initialize"," Re-read initialization files")
        mainmenu.Append(ID_PDFDIR, "&pdfDirectory"," Set output directory for MDH and MGS pdf files")
        mainmenu.AppendSeparator()
        mainmenu.Append(ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(mainmenu,"&Main") # Adding the "mainmenu" to the MenuBar
        menuBar.Append(helpmenu,"&Help") # Adding the "helpmenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        # Note - previous line stores the whole of the menu into the current object

        # Define the code to be run when a menu option is selected
        wx.EVT_MENU(self, ID_HELP, self.OnHelp)
        wx.EVT_MENU(self, ID_HELP_PDF, self.OnHelpPDF)
        wx.EVT_MENU(self, ID_HELP_COORDS, self.OnHelpCoords)
        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, ID_DEBUG, self.OnDebug)
        
        wx.EVT_MENU(self, ID_PASS, self.OnPass)
        wx.EVT_MENU(self, ID_INIT, self.OnInit)
        wx.EVT_MENU(self, ID_PDFDIR, self.OnPdfDir)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)

       # Let's give the app a little color, where we can
        self.label_color  = '#AAFFEE'  # pale blue
        # 
        #self.MDH_color    = '#DDFFEE'  # very pale blue, almost white
        self.MDH_color    = '#FFFFFF'  # white
        #self.MDH_color    = '#FFFFBB'  # Light yellow 
        #self.MDH_color    = '#11FFEE'  # medium blue 
        self.CWI_color    = '#FfFFEE'  # a light blue
        #self.CWI_color    = '#BBFFEE'  # very pale blue,  
        self.MWI_color    = '#11FFEE'  # medium blue # '#FFFFFF'  # white
        self.MGS_color    = '#EEEEAA'  # Light yellow
        self.onbase_color = '#43FFFF'  # '#43DCFF'  #  #55CCFF'  # pale blue
        self.local_color  = '#FFFFBB'  # Light yellow  
        self.project_color= '#EEBBEE'
        self.disclosure_color= '#FFD8B1' # light tan
        self.disclosure_color= '#FFE0C2' # white
        self.fieldnote_color = '#FFC3C2'  # pink  (Well field notes)
        #self.project_color= '#FFFFBB'  # Light yellow 
        
        self.projbtn_color = '#FFCCBB' #?
        
        self.pdfbtn_color = '#AAFFCC'
        self.pdfbtn_color2= '#80FFB3'

        # Buttons on the right, arranged     vertically, that are for selecting Well Record images.
        self.logbtn_sizer = wx.BoxSizer(wx.VERTICAL)
        btnlistW = (
            ('  Get MDH image  ', self.ButtonMDHlog, "up to 10 listed well id's from MGS", self.MDH_color),
            ('Get MGS image', self.ButtonMGSlog, "a single well id from MGS", self.MGS_color),
            ('Get MWI index', self.ButtonCWIindex, "well index page from MWI-on-line", self.MWI_color),
#             ('Get MWI map', self.ButtonCWImap, "opens the MWI-on-line map", self.CWI_color),
            ('Get MWI log', self.ButtonCWIlog, "a well log from MWI-on-line", self.CWI_color),
            ('Get MWI strat', self.ButtonCWIstrat, "a well stratigraphy log from MWI", self.CWI_color),
            ('Get OnBase image', self.ButtonOnBaseWellid, "well docs in OnBase by well_id", self.onbase_color),
            ('Get OnBase Local PLS', self.ButtonOnBaseLocal, "Local File docs in OnBase by Unique No or Twp Rng Section", self.local_color),
            ('Get Disclosure Number', self.ButtonOnBaseDisclosureNum, 'Disclosure certificates in OnBase by Dak.Co. Number")', self.disclosure_color),
            ('Get Well Field Note', self.ButtonOnBaseWellFieldNote, 'Well Field Notes by OnBase Link ID")', self.fieldnote_color),
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

        #########################################################
        ###         coordinate conversion functions           ###
        #########################################################
        try:
            from Coordinate_Transform import DCcoordinate_projector
        except:
            self.can_project = False
            startup_msg += "Unable to import Coordinate_Transform module.\n"
           
        try:
            self.Cprojector = DCcoordinate_projector()
            self.can_project = self.Cprojector.active 
            startup_msg += self.Cprojector.active_msg + '\n'
        except: 
            self.can_project = False
            startup_msg += "Unable to initialize Coordinate_Transform class.\n"
            
        if self.can_project:
            self.projbtn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            btnlistp = (('Convert coords',self.ButtonConvertCoords),
            )   
            for label,method in btnlistp:
                id = new_id()
                btn = wx.Button(self, id, label)
                btn.Bind(wx.EVT_BUTTON, method)
                btn.Bind(wx.EVT_ENTER_WINDOW, self.Enter_coordinate_button_area)
                btn.SetBackgroundColour(self.projbtn_color)
                self.projbtn_sizer.Add(btn,1,wx.EXPAND)


        #########################################################
        ###                    pdf tools                      ###
        #########################################################
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
        label = "Drag a pdf file onto a button at the right to split off\nthe indicated page.Enter custom pdf file page range\nbelow:   e.g. 1,2,5-8,15"
        self.pdfio_sizer.Add(wx.StaticText(self, label=label))
        self.pdfio_sizer.Add(self.pdfpagelist_win,1,wx.EXPAND)

        self.pdf_sizer= wx.BoxSizer(wx.HORIZONTAL)
        self.pdf_sizer.Add(self.pdfio_sizer ,1,wx.EXPAND)
        self.pdf_sizer.Add(self.pdfbtn_sizer,0,wx.EXPAND)

        self.main_sizer= wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.log_sizer,2,wx.EXPAND)
        if self.can_project:
            self.main_sizer.Add(self.projbtn_sizer,0,wx.EXPAND)
        self.main_sizer.Add(self.pdf_sizer,1,wx.EXPAND)
        

        # Tell it which sizer is to be used for main frame
        # It may lay out automatically and be altered to fit window
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(1)
        self.main_sizer.Fit(self)
        self.SetSize((450,500))
        #self.SetBackgroundColour('#D5FFE6')
        self.SetBackgroundColour(self.label_color)
        #self.SetForegroundColour('#D5FFE6')
        #self.SetOwnBackgroundColour('#D5FFE6')

        # Show it !!!
        self.Show(1)
        
        
        # initialize message text and input and output window values
        self.prepare_messages()
        #self.loglist_win.SetValue("<Unique numbers or well_id's here>")
        #self.pdfpagelist_win.SetValue("<Enter custom pdf file page ranges here>")
        #self.output_win.SetValue(self.help_text )
        self.output_status_text = 'Results display here'
        
        self.build_mode = False
        self.build_output = None
        self.show_output(startup_msg)

        self.image_grabber = Well_image_grabber(self.initfile)

        # Transitioning from reading static csv files to direct ODBC connection.
        #self.wellman_connection = WellmanConnection()
        self.wellman_connection = None  # will be created in a try: structure in init_wellman_values() 
        self.init_wellman_values()
#         self._init_wellman_ids()
#         self.init_wellman_projectnames()

        #  wx.StaticText(self, label="Your name :")

    def prepare_messages(self):
        import platform
        self.about_me_text = '\n'.join((
                   'MN Well Record Viewer version %s'%VERSION_NUMBER,
                   '  Graphical tools for',
                   '    accessing well records, and',   
                   '    splitting and merging pdf files.',
                   ' ',
                   '  Python version: %s'%platform.python_version(),
                   '  Using libraries: '
                   '    wx, pyodbc, webbrowser, mechanize, cookielib, urllib2',
                   '    keyring, getpass, base64',
                   '  pdf editing tools are based on the libraries:',
                   '    %s'%(PdfFileReader.__name__),
                   '    %s'%(PdfFileWriter.__name__),                  
                   ))
        self.specific_instruction_text = (
            'Enter a valid page range into the upper window, then drag a pdf file onto the Custom button.')
        self.help_text = (
            'WELCOME\n'+\
            '   To retrieve well log images, or CWI database well logs, '+\
            'enter a unique number, well_id, or RELATEID in the top window, '+\
            'and select a button to the right.\n'+\
            '   Note that some "local" files can be retrieved only using the "Get OnBase image" button, '+\
            'and some only using the "Get OnBase Local PLS" button.'+\
            '   To retrieve "project" files, click one of the "Get Project" buttons '+\
            'and select the project name from the pop up list.\n'+\
            '   To retrieve Dakota County scanned disclosure docs, enter the Dakota County disclosure number.\n'+\
            '   Documents returned as pdf files can be modified with the pdf tools below.\n'+\
            '\n'+\
            'TROUBLESHOOTING\n'+\
            '   DocPop web pages may open with the page appearing empty or with the table of contents unable to open a doc.'+\
            ' This can be due to having ANOTHER BROWSER WINDOW ALREADY OPEN and ZOOMED IN or OUT.'
            ' Try opening your browser to any web page and readjusting the magnification before executing the tool.\n'+\
            '   DocPop web pages have a table of contents panel at the top, and a document viewer panel below.'+\
            ' The divider between the panels can be dragged up and down with the mouse.'+\
            ' If your browser is open and zoomed in before the tool executes, the top panel may be compressed to 0 height,'+\
            ' so you only see the empty lower panel - You might be able to pull the divider down.'+\
            ' If your browser is open and zoomed out before the tool executes, the bottom panel may be compressed to 0 height,'+\
            ' and the browser window may be extremely wide - you may not be able to pull the divider up.')
        
        self.helpPDF_text = (
            'PDF tools for splitting and merging pdf files.\n'+\
            '   The pdf tools operate by dragging pdf files and dropping them onto on of the buttons. '+\
            'The number on the buttons indicate page number to be operated on.  '+\
            'To operate on a page not shown, or a page range, enter the page number or range in the '+\
            'pdf window, and drag the file onto the Custom button. '+\
            'Enter page ranges using commas and dashes.\n'+\
            '   To split off a page or pages, drag a pdf file onto one of the page range buttons, and it will split '+\
            'off the indicated page(s) to a new file. '+\
            'The new document is put in the same directory as the original. '+\
            'The new document is named after the old one with a suffix indicating the page number(s).\n'+\
            '   To merge pages from two or more pdf files into one pdf file, begin by pressing the Build button. '+\
            'Then add pages as described above, and press the Publish button to finish. '+\
            '(No pdf documents will be overwritten.)\n'+\
            '\n'+\
            'TROUBLESHOOTING\n'+\
            '   If the pdf file is reported to be corrupt, try opening it and '+\
            're-saving it in your pdf viewer.')

        if self.can_project:
            self.helpCoords_text = (
                'Coordinate transformations are performed using the Proj4 library. '+\
                'It appears that these transformations may differ from transformations in ArcGIS by less than about a foot. '+\
                'The reason is probably somewhere in the definitions of the ellipses, datums, or grid corrections.\n'+\
                '   Entering coordinates:\n'+\
                '      Enter Dakota county coordinates or UTM coordinates as x,y pairs.\n'+\
                '      Ordering x,y or y,x is optional.\n'+\
                '      Separate with a space or a comma.\n'+\
                '      One coordinate pair only is recognized, on the first row.\n'+\
                '   Entering Lat lon:\n'+\
                '      Ordering lat,lon or lon,lat is optional.\n'+\
                '      Minus sign on the longitude is optional.\n'+\
                '      Decimal degrees can be separated with a space or a comma:\n'+\
                '         e.g. "-93.3162,44.4713" or "-93.3162 44.4713"\n'+\
                '      Minutes and seconds should be separated with spaces.\n'+\
                '         If used, separate lat and lon with a comma.\n'+\
                '         e.g. "-92 55.925000, 44 33.558333"\n'+\
                '         e.g. "-92 55 55.500, 44 33 33.500"\n'+\
                '      DO NOT enter the minutes (\') or seconds (") marks.\n'+\
                'Below are the Proj4 definition arguments for the transformations.'+\
                self.Cprojector.strproj() )
        else:
            self.helpCoords_text = (
                'Coordinate transformations are not installed. '+\
                'See your installation administrator to install the Proj4 libraries')
                   


    def init_wellman_values(self): 
        try:
            #assert False
            if not self.wellman_connection:
                self.wellman_connection = WellmanConnection()
            self.wellman_ids,self.wellman_projectnames = self.wellman_connection.get_wellman_values()
            print 'Initialized well ids from Wellman through ODBC.\n    %i records read into dictionary.'%(len(self.wellman_ids) )             

        except:
            fname=r'T:\Wells\ImageViewerData\well_ids.csv'
            f = open(fname)
            rows = f.read().upper()
            f.close
            self.wellman_ids = {}
            for row in rows.split('\n')[:-1]:
                row = row.split(',')
                self.wellman_ids[row[0][1:-1].strip()] = row[1].strip()   
            print 'Initialized well ids from %s.\n    %i records read into dictionary.'%(fname,len(self.wellman_ids) )             
         
            fname = r'T:\Wells\ImageViewerData\projectnames.csv'
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
        if (min(pagelist) <= 0) or (infile_pages < max(pagelist)):
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
        if (min(pagelist) <= 0) or (infile_pages < max(pagelist)):
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
        text_list = self.loglist_win.GetStringSelection()
        if len(text_list) > 0:
            #print 'text= ',text
            self.loglist_win.SetSelection(0,0)
        else:
            text_list = self.loglist_win.GetValue()

        text_list.replace(',',' ')
        loglist = text_list.split()
        if (loglist.count>0):
            return loglist
        else:
            self.show_output("Please enter search criteria in the top window")
            return None

    def ButtonMDHlog(self,event):
        loglist = self._read_log_win()
        if not (loglist): return
        OK,fname = self.image_grabber.get_MDH_image(loglist)
        if OK: 
            self.show_output(                'MDH image: \n%s'%fname, append=False)
            webbrowser.open_new_tab(fname) 
        else:
            self.show_output(fname, append=False)   
    def ButtonMGSlog(self,event):
        #print 'ButtonMGSlog'        
        loglist = self._read_log_win()
        if not (loglist): return
        #print 'MGS loglist:',loglist[0]
        OK,fname = self.image_grabber.get_MGS_image(loglist[0])
        if OK: 
            self.show_output('MGS image: "%s"'%fname, append=False)
            webbrowser.open_new_tab(fname)    
        else:
            self.show_output('MGS image "%s" not found'%loglist[0])
            
    def OpenCWI(self,Type="INDEX"):
        loglist = self._read_log_win()
        if not (loglist): return
        #print 'loglist:',loglist
        url = self.image_grabber.get_CWI_log(loglist[0],Type=Type)
        print 'url= "%s"'%url
        if (url):
            self.show_output('MWI record found: "%s"'%loglist[0], append=False)
            webbrowser.open_new_tab(url) 
    def ButtonCWIindex(self,event):
        self.OpenCWI(Type="INDEX")
#     def ButtonCWImap(self,event):   #call to Map page is not working from Python.
#         self.OpenCWI(Type="MAP")
    def ButtonCWIlog(self,event):
        self.OpenCWI(Type="LOG")
    def ButtonCWIstrat(self,event):
        self.OpenCWI(Type="STRAT")
#         #print 'ButtonCWIlog'        
#         loglist = self._read_log_win()
#         if not (loglist): return
#         #print 'loglist:',loglist
#         url = self.image_grabber.get_CWI_log(loglist[0],Type="INDEX")
#         #print 'url= "%s"'%url
#         if (url):
#             self.show_output('CWI log found: "%s"'%loglist[0], append=False)
#             webbrowser.open_new_tab(url) 
#     def ButtonCWIlog(self,event):
#         #print 'ButtonCWIlog'        
#         loglist = self._read_log_win()
#         if not (loglist): return
#         #print 'loglist:',loglist
#         url = self.image_grabber.get_CWI_log(loglist[0],Type="LOG")
#         #print 'url= "%s"'%url
#         if (url):
#             self.show_output('CWI log found: "%s"'%loglist[0], append=False)
#             webbrowser.open_new_tab(url) 
#     def ButtonCWIstrat(self,event):
#         #print 'ButtonCWIstrat'        
#         loglist = self._read_log_win()
#         if not (loglist): return
#         url = self.image_grabber.get_CWI_log(loglist[0],Type="STRAT")
#         if (url):
#             self.show_output('CWI strat log found: "%s"'%loglist[0], append=False)
#             webbrowser.open_new_tab(url) 

    def ButtonOnBaseWellid(self,event):
        #print 'ButtonOnBaseWellid'        
        loglist = self._read_log_win()
        if not (loglist): return
        val = loglist[0].strip().upper()
        print 'searching OnBase for id "%s"'%val,
        id = self.wellman_ids.get(val,val)  #if val is not found in the wellman_ids dictionary, then just use val.
        if id==val:
            idmsg = 'Well id %s'%val
        else:
            idmsg = 'Well identifier %s (id %s)'%(val,id)
        print ', mapped to id "%s"'%id
        url = self.image_grabber.get_OnBase_images(id,'DAKCO_OnBase_well_id_url') 
        if (url):
            self.show_output('Requesting OnBase docs for %s'%idmsg, append=False)
            webbrowser.open_new_tab(url) 
            print 'url = '+url
        else:
            self.show_output('Well unique no or id not found: %s, %s'%(val,id), append=False)

        
    def ButtonOnBaseLocal(self,event):
        #print 'ButtonOnBaseLocal'        
        ''' if txt is Twp Rng Section, e.g. "27 19 2", change to std fmt "027 09 02"
            otherwise assume it is a unique number.
        '''
        txt = self._read_log_win_plain()
        try:
            t,r,s = txt.strip().replace('-',' ').replace('/',' ').replace(',',' ').split()
            PLS = '%03d+%02d+%02d'%(int(t),int(r),int(s))
            assert len(PLS) == 9 
            url = self.image_grabber.get_OnBase_images(PLS,'DAKCO_OnBase_twp_rng_sec_url')
            msg =  'Requesting OnBase Local records by Twp Rng Section: %s '%PLS + '\n' +url
        except:
            val = txt.strip().split()[0] 
            if (len(val) >= 4) and (len(val) <= 7):
                url = self.image_grabber.get_OnBase_images(val,'DAKCO_OnBase_well_unique_url')
                msg = 'Requesting OnBase Local records by Unique: %s'%val + '\n' +url
            else:
                self.show_output('Must enter Unique number, or Twp Rng Sec as "27 22 4" or "027 22 04"', append=False)
                return
        if (url):
            self.show_output(msg, append=False)
            OK = webbrowser.open_new_tab(url) 

    def _project_picker(self):
        dlg = wx.SingleChoiceDialog(self, 'Project Names', 'Select project:', self.wellman_projectnames, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            projectname = dlg.GetStringSelection()
            self.SetStatusText('You chose: %s\n' % projectname)
        else:
            projectname = None
        dlg.Destroy()
        return projectname
        
    def ButtonOnBaseProject(self,event):
        projectname = self._project_picker()
        if not projectname:
            return
        url = self.image_grabber.get_OnBase_project(projectname, projectyear=None, doctype=None)  
        print url
        if (url):
            self.show_output('Requesting OnBase docs for"%s"'%projectname, append=False)
            webbrowser.open_new_tab(url) 
        else:
            self.show_output('No OnBase docs for "%s"'%projectname, append=False)

    def ButtonOnBaseProjectMap(self,event):
        #print 'ButtonOnBaseProjectMap'        
        projectname = self._project_picker()
        if not projectname:
            return

        url = self.image_grabber.get_OnBase_project(projectname, projectyear=None, doctype="MAP")  
        print url        
        if (url):
            self.show_output('OnBase Project Maps found for"%s"'%projectname, append=False)
            webbrowser.open_new_tab(url) 
        else:
            self.show_output('No OnBase Project Maps for "%s"'%projectname, append=False)

    def ButtonOnBaseProjectYear(self,event):
        try:
            projectyear = '%s'%(int(self._read_log_win_plain()))
            assert len(projectyear)==4
            assert int(projectyear) > 1900
        except:
            self.show_output('Please enter the 4-digit permit year in the top window first.') 
            return
        projectname = self._project_picker()
        if not projectname:
            return
        
        url = self.image_grabber.get_OnBase_project(projectname, projectyear=projectyear, doctype=None)  
        print url        
        if (url):
            self.show_output('Requesting OnBase docs for "%s %s"'%(projectname,projectyear), append=False)
            webbrowser.open_new_tab(url) 
        else:
            self.show_output('No OnBase Project docs found for "%s %s"'%(projectname,projectyear), append=False)
            
    def ButtonOnBaseDisclosureNum(self,event):
        numlist = self._read_log_win()
        val = numlist[0].strip()
        if 1: #try:
            id = int(val)
            url = self.image_grabber.get_OnBase_images(id,'DAKCO_OnBase_disclosure_id_url') 
            if (url):
                self.show_output('Requesting OnBase Disclosures for: "%s"'%val, append=False)
                webbrowser.open_new_tab(url) 
            else:
                self.show_output('Disclosure number not found: %s, %s'%(val,id), append=False)
        else: #except:
            self.show_output('Error. Did you enter a numeric disclosure number? Entered: "%s"'%val, append=False)
        
        
        #DAKCO_OnBase_disclosure_id_url

    def ButtonOnBaseWellFieldNote(self,event):
        numlist = self._read_log_win()
        val = numlist[0].strip()
        if 1: #try:
            id = int(val)
            url = self.image_grabber.get_OnBase_images(id,'DAKCO_OnBase_wellfieldnote_id_url') 
            if (url):
                self.show_output('Requesting OnBase Disclosures for: "%s"'%val, append=False)
                webbrowser.open_new_tab(url) 
            else:
                self.show_output('Disclosure number not found: %s, %s'%(val,id), append=False)
        else: #except:
            self.show_output('Error. Did you enter a numeric disclosure number? Entered: "%s"'%val, append=False)


    def ButtonConvertCoords(self,event):
        ''' test values:
            Dakota Co: 600248.828523, 132087.725159
            UTM      : 505393.746153, 4933998.97307
            D.d      : -92.932083333, 44.559305556
            D M.m    : -92 55.925000, 44 33.558333
            D M S.s  : -92 55 55.500", 44 33 33.500
        '''   
        coordtext = self._read_log_win_plain()
        if not coordtext:
            return
        outtext = self.Cprojector.handle_unspecified_coords(coordtext)
        self.show_output(outtext)

        





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
            pagelist = [i for r in ranges for i in range(int(r[0]), int(r[-1]) + 1)]
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

    def Enter_coordinate_button_area(self,event):
        self.status_bar.SetStatusText('Enter coordinate pair to transform')
    
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
            self.output_win.SetValue('%s\n%s'%(new_txt,old_txt))
        else:
            self.output_win.SetValue(new_txt)

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

    def OnHelpPDF(self,e):
        self.show_output(self.helpPDF_text)

    def OnHelpCoords(self,e):
        self.show_output(self.helpCoords_text)

    def OnAbout(self,e):
        self.aboutme = wx.MessageDialog( self, self.about_me_text, "About Well_Image_GUI.py", wx.OK)
        self.aboutme.ShowModal() 
        
    def OnDebug(self,e):
        self.DEBUG = not(self.DEBUG)

    def OnPass(self,e):
        """ we'll use the log window to read in the initialization strings, but we will not parse it 
            the usual way, so we'll read it in raw
        """
        initstring = self.loglist_win.GetValue()
        OK,msg = self.image_grabber.initialze_logins(initstring)
        self.show_output(msg, append=False)

    def OnInit(self,e):
        """ re-read the initialization files.
        """
        self.init_wellman_values()
#         self._init_wellman_ids()
#         self.init_wellman_projectnames()
        msg = self.image_grabber.read_initfile() 
        msg = 'Re-initialized wellman-ids, project names, and urls \n%s'%msg
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