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

print "based on   http://stockrt.github.io/p/emulating-a-browser-in-python-with-mechanize/"

import mechanize
import cookielib
import webbrowser
import os
import urllib2

print "imports done"
import keyring
import getpass
import base64
class PasswordKeeper(object):
    """ A simple and only lightly obfuscating password manager.
        Do not use this class for critical passwords.
        Passwords are stored using the OS keyring service (?) and can be accessed in subsequent launches.
    """
    
    def __init__(self, ringname):
        """ initialization requires naming of a keyring service. 
            However, later calls allow using a differently named service 'ringname', but there is not yet a call to alter the stored ringname.
            The only allowed user name is the system user name.
        """
        self.ringname = ringname
        self.username = getpass.getuser()
        print 'ringname = "%s"'%self.ringname
        print 'username = "%s"'%self.username
    
    def set(self, ringname=None, password=None, prompt=None):
        """ The pasword is obfuscated using base64.b64encode, and stored in a keyring """
#         ringname = kwargs.pop('ringname', self.ringname)
#         password = kwargs.pop('password', None)
#         prompt = kwargs.pop('prompt', None)
        if not ringname:
            ringname = self.ringname
        if password:
            keyring.set_password( ringname, self.username, base64.b64encode(password) )
            return True
        elif prompt:
            keyring.set_password( self.ringname, self.username, base64.b64encode( getpass.getpass(prompt).strip() ) )
            return True
        else:
            return False
            
    def get(self,ringname=None):
        """ The pasword is extracted from the keyring, and returned in clear """
        if not ringname:
            ringname = self.ringname
        p = keyring.get_password(ringname,self.username)
        if p:  return base64.b64decode(p)
        else:  return None
            
    def clear(self,ringname=None):
        if not ringname:
            ringname = self.ringname
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
    def __init__(self,prefix=None):
        # Determine the file location for placing the image files.
        if not prefix:
            for prefix in ('C:/_OnBase_scan_temp_folder/scratch_images','E:/bill/scratch/images','xxx'):
                if os.path.exists(prefix):
                    break
        assert prefix != 'xxx'
        self.prefix = prefix
        self.DBGmode = False
        self.passwordkeeper = PasswordKeeper(ringname='MDH well record image retrieval')

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

    def get_OnBase_images(self,well_id):
        oburl = "http://EDWEB1/AppNet/docpop/docpop.aspx?KT636_0_0_0=%s&clienttype=activex&cqid=1017"%well_id
        return oburl
    
    def get_MGS_image(self,UniqueNo):
        """ the UniqueNo should be formatted as 6 character text, e.g. "123456", rather than as a RelateID
        """
        if self.DBGmode:
            return os.path.join(self.prefix,"190471.pdf")

#        print 'get_MGS_image, UniqueNo ="%s"'%UniqueNo
#         if UniqueNo.upper() == "MGSLOGIN":
#             if len(UniqueNo) != 2:
#                 return (False,'Initialize MGS login: "MGSLOGIN <url_pattern>"')
#             self.passwordkeeper.set(ringname='MGS well record image url',password=UniqueNo)
#             return (False, 'MGSLOGIN has been initialized')
        
        mgsurl = self.passwordkeeper.get(ringname='MGS_well_record_image_url') #'http://mgsweb2.mngs.umn.edu/welllogs/%s.pdf'%UniqueNo
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
        
    def get_MDH_image(self,well_list):
        """ the UniqueNos should be formatted as 6 character text, e.g. "123456", rather than as a RelateID
            up to 10 different unique nos can be passed.  They should be a single splittable string.
            The web bit is pretty tedious.  
        """
        if self.DBGmode:
            return os.path.join(self.prefix,"190471.pdf")
        #well_list = UniqueNos.replace("\t"," ").replace("\n"," ").replace(","," ").replace("/"," ").split()

#         print WellList
#         for n,w in enumerate(WellList):     
#         #well1,well2 = '766413','766414'
#             print ["wellnbr_%i"%(n+1)], w
#         return
    
        #MDH:
#         if well_list[0].upper() == "MDHLOGIN":
#             if len(well_list) != 4:
#                 return (False,'Initialize MDH login: "MDHLOGIN <user> <password> <url_pattern>"')
#             self.passwordkeeper.set(ringname='MDH well record image user',password=well_list[1])
#             self.passwordkeeper.set(ringname='MDH well record image password',password=well_list[2])
#             self.passwordkeeper.set(ringname='MDH well record image url',password=well_list[3])
#             return (False, 'MDHLOGIN has been initialized')
# #                         prompt='Enter password for MDH well record image retrieval:')
        
#         self.passwordkeeper.set(ringname='MDH well record image user',password=mdhuser)
#         self.passwordkeeper.set(ringname='MDH well record image password',password=mdhpassword)
#         self.passwordkeeper.set(ringname='MDH well record image url',password=mdhurl)
        ringuser = 'MDH_well_record_image_user'
        ringpass = 'MDH_well_record_image_password'
        ringurl  = 'MDH_well_record_image_url'
        mdhuser     = self.passwordkeeper.get(ringname=ringuser)
        mdhpassword = self.passwordkeeper.get(ringname=ringpass)
        mdhurl      = self.passwordkeeper.get(ringname=ringurl )
        
        for key,ring in  ((mdhuser,ringuser),(mdhpassword,ringpass),(mdhurl,ringurl)):
            if key is None:
                return False,'Missing initialization value for "%s"'%ring
#         if (mdhuser is None) or (mdhpassword is None) or (mdhurl is None):
#             return (False,'Initialize MDH login: "MDHLOGIN <user> <password> <url_pattern>"')

#         print mdhurl
#         print mdhuser
#         print mdhpassword
#         print '=================='
#         assert False
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
        #br.form["password"] = mdhpassword    
        br.form["password"] =  self.passwordkeeper.get(ringname='MDH well record image retrieval')
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
        W = Well_image_grabber()
        if 1:
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

        elif 1:
            UniqueNo = "207689" #"190471"
            print W.prefix
            print W._get_new_filename(UniqueNo,"pdf")
            OK,fname = W.get_MGS_image(UniqueNo)
            print OK, fname
            if OK: 
                webbrowser.open_new_tab(fname)
            
        elif 0:
            wellid = 15340  
            url = W.get_OnBase_images(wellid) 
            if (url):
                webbrowser.open_new_tab(url)  
                  
        elif 0:
            #UniqueNos = "678244" #"420967"
            well_list = ["678244"]
            fname = W.get_MDH_image(well_list)
            if fname is not None: 
                print fname
                webbrowser.open_new_tab(fname[1])
            
        elif 0:
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



