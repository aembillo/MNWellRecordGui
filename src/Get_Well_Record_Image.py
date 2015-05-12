"""
    Script to open scanned well logs from MGS or MDH
    Author: Bill Olsen 
            Dakota County
            2014-11-02

    Uses keyring library to store passwords and private url strings.
    
    ToDo:
        consider simplifying using the Requests library:
            http://docs.python-requests.org/en/latest/index.html
    Language Python 2.7
"""
from cgitb import html

#print "based on   http://stockrt.github.io/p/emulating-a-browser-in-python-with-mechanize/"

import mechanize
import cookielib
import webbrowser
import os
import urllib2

#print "imports done"
import keyring
import getpass
import base64

class PasswordKeeper(object):
    """ A simple and only lightly obfuscating password manager.
        Do not use this class for critical passwords.
        Passwords are stored using the OS keyring service (?) and can be accessed in subsequent launches.
    """
    
    def __init__(self):
        """ initialization requires naming of a keyring service. 
            However, later calls allow using a differently named service 'ringname', but there is not yet a call to alter the stored ringname.
            The only allowed user name is the system user name.
        """
        #self.ringname = ringname
        self.username = getpass.getuser()
        #print 'ringname = "%s"'%self.ringname
        #print 'username = "%s"'%self.username
    
    def set(self, ringname=None, password=None, prompt=None):
        """ The pasword is obfuscated using base64.b64encode, and stored in a keyring """
#         ringname = kwargs.pop('ringname', self.ringname)
#         password = kwargs.pop('password', None)
#         prompt = kwargs.pop('prompt', None)
        if not ringname:
            return False
        if password:
            keyring.set_password( ringname, self.username, base64.b64encode(password) )
            return True
        elif prompt:
            keyring.set_password( ringname, self.username, base64.b64encode( getpass.getpass(prompt).strip() ) )
            return True
        else:
            return False
            
    def get(self,ringname=None):
        """ The pasword is extracted from the keyring, and returned in clear """
        if not ringname:
            return None
            #ringname = self.ringname
        p = keyring.get_password(ringname,self.username)
        if p:  return base64.b64decode(p)
        else:  return None
            
    def clear(self,ringname=None):
        if not ringname:
            return None
            #ringname = self.ringname
        keyring.delete_password(ringname, self.username)



class Well_image_grabber():
    """ Hard coded methods for getting well record images from on-line sources.
        The urls return images as html that is written to a file with extension .pdf, and can be opened by a pdf application or a browser.
        The images are assumed suitable for archiving - but that should be validated.
        
        Hard coded methods include:
            MDH images: for up to 10 unique numbers, from 1990 to present.  Returned as a single pdf document.
            MGS images: for 1 unique number at a time. Working back from 1989.
            Dakota Co. images: for 1 well id at a time.
    
        The url methods for MDH images differ because of the secure log in protocol.
    """     
#     def __init__(self,prefix=None):
    def __init__(self,initfile):
        """ the init file should have key:value pairs separated by whitespace on each line.
            the init file should have the following keys:
                MDH_well_record_image_url    
                MGS_well_record_image_url    
                DAKCO_OnBase_well_id_url    
                DAKCO_OnBase_project_url     
                DAKCO_OnBase_project_map_url
                DAKCO_OnBase_project_year_url
                temp_file_path  <Where pdf files are dumped.  Multiple paths can be specified, the last one that exists will be used.>
        """   
        self.initfile = initfile 
        assert os.path.exists(initfile), "Init file not found: "+initfile
        f = open(initfile,'r')
        rows = f.read()
        f.close()
#         print rows
#         print 80*';'
        self.userdict = {}
        self.pdfdirkey = "temp_file_path"
        for keyvalue in rows.split('\n'):
#             print 'A ',keyvalue
            if not len(keyvalue)>2:
                continue
            key,value = keyvalue.split()
#             print 'B ',key,value
            if key == self.pdfdirkey:
                if os.path.exists(value):
                    self.userdict[key] = value
            else:
                self.userdict[key] = value
        self.prefix = self.userdict.get('temp_file_path')
        self.DBGmode = False
        self.passwordkeeper = PasswordKeeper() #ringname='MDH well record image retrieval')
#         for key,value in self.userdict.iteritems():
#             print key,value
            
    def get_pdfdir(self):
        return self.userdict.get(self.pdfdirkey, None)
    
    def set_pdfdir(self,pdfdir):
        if not os.path.exists(pdfdir):
            return False
        self.userdict[self.pdfdirkey] = pdfdir
        fname = self.write_initfile()
        if fname:
            msg = 'Edited initfile: %s\nSet pdf file directory to "%s"'%(fname,pdfdir)
            return msg

    def write_initfile(self):
        f = open(self.initfile,'w')
        fmt = "%s\t%s\n"
        for key,value in sorted(self.userdict.iteritems()):
            f.write(fmt%(key,value))
        f.close()                
        return f.name
    

    def initialze_logins(self, initstring): 
        """ login information and private url strings are kept in a ring server. """
        print 'initialze_logins(%s)'%( initstring)
        OKlist = []
        for ring_value in initstring.split('\n'):
            if ring_value:
                try:
                    #print 'ring_value = %s'%ring_value
                    ring, value = ring_value.split()
                    #print 'ring, value = %s, %s'%(ring,value)
                    self.passwordkeeper.set(ringname=ring, password=value)
                    OKlist.append(ring)
                    #print 'set them OK'
                except:
                    print 'exception raised'
                    continue
                    return False, 'Unable to parse "%s"'%ring_value
        print '... All done with initializing ...'
        return True, 'Logins stored for \n  ' + ('\n  '.join(OKlist))
    

#         if UniqueNo.upper() == "MGSLOGIN":
#             if len(UniqueNo) != 2:
#                 return (False,'Initialize MGS login: "MGSLOGIN <url_pattern>"')
#             self.passwordkeeper.set(ringname='MGS well record image url',password=UniqueNo)
#             return (False, 'MGSLOGIN has been initialized')    
           
    def _get_new_filename(self,basename="test",extension="pdf"):
        # Get a unique filename based on basename
        # First, try something formatted like test_001.pdf. After _999 use the Tempfile module
        n = 1
        basename = os.path.join( self.prefix, basename )
        while True:
            fname = "%s_%003u.%s"%(basename,n,extension)
            if not os.path.exists(fname):
                return fname
            n += 1
            
        import tempfile
        fname = tempfile.NamedTemporaryFile(basename+"_", suffix='.pdf', delete=False)
        return fname

    def get_OnBase_images(self,value,key='DAKCO_OnBase_well_id_url'):
        oburl = self.userdict.get(key)
        oburl = oburl%value.upper()
        return oburl

    def get_OnBase_project(self,projectname,projectyear=None, doctype=None):
        """ Query OnBase for documents indexed to project name or project name and year.
        
            There are 3 options for the query:
                Project Name         - All doctypes
                Project Name         - Map doctypes only (also includes inspections)
                Project Name & year  - All doctypes
            Note that the project name has to be re-formatted for the url
            e.g. MPCA BUNNY'S SERVICE CENTER => MPCA+BUNNY%27S+SERVICE+CENTER
            Note that the url's do not appear to be case sensitive, but we'll upper case the project name for clarity.
        """
        # Some ASCII characters are not permitted in the url, and must be replaced with the ASCII HEX Codes.
        # E.G. replace "#" with "%23".   A list of codes can be found at:  http://www.ascii-code.com/    
        projectname = projectname.strip().upper().replace(" ","+").replace("'","%27").replace("#","%23").replace("&","%26").replace("@","%40")
        if (projectyear is None) and (doctype is None):
            oburl = self.userdict.get('DAKCO_OnBase_project_url')
            url = oburl%projectname
        elif (projectyear is None) and (doctype == "MAP"):
            oburl = self.userdict.get('DAKCO_OnBase_project_map_url')
            url = oburl%projectname
        elif (projectyear) and (doctype is None):
            oburl = self.userdict.get('DAKCO_OnBase_project_year_url')
            try:
                yr = int(projectyear)
                assert (yr>1949) and (yr<2020)
                url = oburl%(projectname,yr)
            except:
                return None
        return url
    
    def get_MGS_image(self,UniqueNo):
        """ the UniqueNo should be formatted as 6 character text, e.g. "123456", rather than as a RelateID
        """
        if self.DBGmode:
            return os.path.join(self.prefix,"190471.pdf")

        mgsurl = self.userdict.get('MGS_well_record_image_url')
        #print 'mgsurl ="%s"'%mgsurl
        if not mgsurl:
            return (False, 'Initialize MGS login: "MGS_well_record_image_url <url_pattern>"') 
        
        mgsurl = mgsurl%UniqueNo
        #print 'mgsurl ="%s"'%mgsurl
        html = "x"
        try:
            html = urllib2.urlopen(mgsurl).read()
        except(urllib2.HTTPError):
            msg = "Well Record image %s not found at MGS"%UniqueNo
            return False, msg
        # A valid return value for html is a pdf file having html[:5] == '%PDF-'
        # A not found Unique throws HTTPError
        # An invalid Unique throws HTTPError too. 
        # Write the gibberish to a file, and opens it in a browser. 
        fname = self._get_new_filename(UniqueNo, 'pdf')
        print 'opening MSGS image file: "%s"'%fname
        f = file(fname, 'w+b')
        f.write(html)
        f.flush()
        f.close()
        return True,fname

    def get_CWI_log(self,UniqueNo,Type="LOG"):
        """ the UniqueNo should be formatted as 6 character text, e.g. "123456", rather than as a RelateID
            e.g. 678244
        """
        print 'get_CWI_log: ' + UniqueNo
        Unique = UniqueNo.strip().upper()
        
        L = Unique[0]
        if Unique[0]=="H":
            return None
        elif Unique[0]=="W":
            RelateID = "19W" + ("0000000%s"%(Unique[1:]))[-8:]
        else: 
            RelateID = ("000000000%s"%Unique)[-10:]
        
        if Type=="STRAT":
            cwiurl = 'http://mdh-agua.health.state.mn.us/cwi/strat_report.asp?wellid=%s'%RelateID
        else:
            cwiurl = 'http://mdh-agua.health.state.mn.us/cwi/well_log.asp?wellid=%s'%RelateID
        return cwiurl
        #webbrowser.open_new_tab(cwiurl)
        
    def get_MDH_image(self,well_list,verbose=False):
        """ the UniqueNos should be formatted as 6 character text, e.g. "123456", rather than as a RelateID
            up to 10 different unique nos can be passed.  They should be a single splittable string.
            The web bit is pretty tedious.  
        """
        if self.DBGmode:
            return os.path.join(self.prefix,"190471.pdf")

        ringuser = 'MDH_well_record_image_user'
        ringpass = 'MDH_well_record_image_password'
        ringurl  = 'MDH_well_record_image_url'
        mdhuser     = self.passwordkeeper.get(ringname=ringuser)
        mdhpassword = self.passwordkeeper.get(ringname=ringpass)
        mdhurl      = self.passwordkeeper.get(ringname=ringurl )
        
        for key,ring in  ((mdhuser,ringuser),(mdhpassword,ringpass),(mdhurl,ringurl)):
            if verbose:
                print "%s %s"%(ring,key)
            if key is None:
                return False,'Missing initialization value for "%s"'%ring

        # Browser
        br = mechanize.Browser()
        
        # Cookie Jar
        cj = cookielib.LWPCookieJar()
        br.set_cookiejar(cj)
        
        # Browser options
        br.set_handle_equiv(True)
        #br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        
        # Follows refresh 0 but not hangs on refresh > 0
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        
        # Want debugging messages?
        #br.set_debug_http(True)
        #br.set_debug_redirects(True)
        #br.set_debug_responses(True)    
        
        #br.add_password(mdhurl, mdhuser, mdhpassword)
        r = br.open(mdhurl)
        html = r.read()
        
        if 0:
            # Show the source
            print "\n =============== show source ==============\n"
            print html
            # or
            print br.response().read()
            
            # Show the html title
            print "\n =============== show title ==============\n"
            print br.title()
            
            # Show the response headers
            print "\n =============== show info ==============\n"
            print r.info()
            # or
            print br.response().info()
            
            # Show the available forms
            for j,f in enumerate(br.forms()):
                print 'MDH form no [%i]:'%j
                print "%s\n"%f
                 
        
        # try filling in the form:    
        # http://stackoverflow.com/questions/14722309/filling-up-a-login-form-using-mechanize-python 
        #print "\n =============== log in ==============\n"
        br.select_form(nr=0)               # Find first form of web page
        br.form["username"] = mdhuser
        br.form["password"] = mdhpassword    
        br.submit()                    # submit
    
    #    print "\n =============== log in response ==============\n"
    
        html = br.response().read()
        if "The username or password is invalid." in html:
            return (False,'MDH password missing or incorrect.  Request MDH log as "Password <password>"')
                
        if 0:    
            print "\n =============== on the Select Unique no page ==============\n"
             
            for f in br.forms():
                print "\n =============== show form ==============\n"
                print f

        # Choose the right form on the web page using it's index
        br.select_form(nr=1)
        for n,w in enumerate(well_list):     
        #well1,well2 = '766413','766414'
            br.form["wellnbr_%i"%(n+1)] = w
    
        print "\n =============== Submitting unique  ==============\n"
        br.submit()                    # submit
    
        print "\n =============== Submitted unique Response ==============\n"
        html = br.response().read()    
        
        # check that we have received a pdf document, and not a message of no images found
        if html.split()[0] == "<!DOCTYPE":
            msg = "No images for record(s) %s found at MDH"%(", ".join(well_list))
            return False, msg
#         print 80*"#"    
#         for row in html.split('\n'):
#             print row
#         print 80*"#"    
        
        # use tempfile, to avoid file lock conflicts when repeating calls 
        fname = self._get_new_filename(well_list[0], "pdf")
        f = file(fname, 'w+b')
        f.write(html)
        f.flush()
        f.close()
        return True, fname

import unittest
class Test(unittest.TestCase):

    def testGrabbing(self):
        import webbrowser
        W = Well_image_grabber("WellRecordGui.ini")
        if 0:
            UniqueNo = "x207689" #"190471"
            url = W.get_CWI_log(UniqueNo)
            #print 80*"*" + "\n%s\n"%url + 80*"*"
            if (url):
                #webbrowser.open_new_tab(url) 
#                 print 'url = ',url
#                 response = urllib2.urlopen(url)
#                 print 'response.info() = ',response.info()
#                 html = response.read()
#                 print 'response.read()=' +'\n %s \n'%html[:100] +80*"*"
#                 # do something
#                 response.close()  # best practice to close the file
                try: 
                    webbrowser.open_new_tab(url)
                except webbrowser.Error:
                    print 'webbrowser.Error', webbrowser.Error.message

        if 0:
            UniqueNo = "207689" #"190471"
            print W.prefix
            print W._get_new_filename(UniqueNo,"pdf")
            OK,fname = W.get_MGS_image(UniqueNo)
            print OK, fname
            if OK: 
                webbrowser.open_new_tab(fname)
            
        if 0:
            wellid = 15340  
            url = W.get_OnBase_images(wellid) 
            if (url):
                webbrowser.open_new_tab(url)  
                  
        if 1:
            #UniqueNos = "678244" #"420967"
            well_list = ["678244"]
            fname = W.get_MDH_image(well_list,verbose=True)
            if fname is not None: 
                print fname
                webbrowser.open_new_tab(fname[1])
            
        if 0:
            #UniqueNos = "268045" #"420967"
            well_list = ["268045"]
            fname = W.get_MDH_image(well_list)
            if fname is not None: 
                print fname
                webbrowser.open_new_tab(fname)
            fname = W.get_MGS_image(well_list[0])
            if fname is not None: 
                print fname
                webbrowser.open_new_tab(fname)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



