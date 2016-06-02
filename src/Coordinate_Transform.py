"""
    Script to perform coordinate transforms for Dakota County
    Author: Bill Olsen 
            Dakota County
            2014-11-02

    Uses Proj4 and pyproj, which require special installation instructions:
    
        Download prebuilt binary for proj4 
            https://github.com/OSGeo/proj.4/wiki  *Probably this one.
            https://trac.osgeo.org/mapserver/wiki/WindowsProjHowto ?
            32bit version is the only one I have found pre-compiled
                T:\Config\Py_install\proj446_win32_bin.zip
        Install the binary in, for example, C:\Program Files\proj        
        Open Control panel to edit system vars.
            Start type 'system' in the run window
                Advanced system settings
                    Environment Variables
                        System variables:  add the following (using the location where you installed proj4
                            PROJ_DIR    C:\Program Files\proj
                            PROJ_LIB    C:\Program Files\proj\nad
            (You may have to re-boot after adding these)
        
        Download a python wheel (.whl) file for pyproj from Christian Gohlke's unofficial binary repo: 
                http://www.lfd.uci.edu/~gohlke/pythonlibs/    (search on 'pyproj')
            A recent(?) version is stored in the Config\Py_install folder:
                T:\Config\Py_install\pyproj-1.9.5-cp27-none-win32.whl
        
        Open a command console in the Python27\Scripts directory  (shift right click on the directory in Windows Explorer)
        Enter  >  pip install T:\Config\Py_install\pyproj-1.9.5-cp27-none-win32.whl
    

    Default County Projection definition used by AV3 Projection extension
        pj = Lambert.Make(Rect.Make(500000@100000,650000@250000))\n
        pj.SetLowerStandardParallel(44.516666667)\n
        pj.SetUpperStandardParallel(44.916666667)\n
        pj.SetCentralMeridian(-93.316666667)\n
        pj.SetreferenceLatitude(44.47194444444)\n
        pj.SetFalseEasting(152400.30480061)\n
        pj.SetFalseNorthing(30480.060960122)\n
        pj.SetDescription(\"Dakota County - 83\")\n\n
        if (av.GetVersion = \"2.1\")
            then\n  sp = pj.GetEllipsoid\n
        else\n  
          sp = pj.GetSpheroid\n
        end\n
        sp.SetMajorAndMinorAxes(6378421.9885700, 6357036.3471975)

    Internally, lon,lat usually passed around as fractional degrees, or as text strings.
    (check out https://pypi.python.org/pypi/LatLon/1.0.2)
"""
import numpy as np

class DCcoordinate_projector():
    def __init__(self):
        self.ft = 0.3048006096012912  # m / US survey ft
        try: 
            from pyproj import Proj 
            self.UTMprojstring = "+proj=utm +zone=15 +ellps=GRS80 +datum=NAD83 +units=m +no_defs"
            self.Dakprojstring  = "+proj=lcc +lat_1=44.51666666666667 +lat_2=44.91666666666666 +lat_0=44.47194444444445 +lon_0=-93.31666666666666 +x_0=152400.3048006096 +y_0=30480.06096012192 +a=6378421.989 +b=6357036.347 +units=us-ft +to_meter=0.3048006096012912 +no_defs" 
            self.projUTM = Proj(self.UTMprojstring)
            self._projDak = Proj(self.Dakprojstring)
            self.active = True
            self.bounding_boxes()
            
        except:
            self.active = False
    
    def projDak(self,a,b,inverse=None):
        ''' A thin wrapper around proj4.Proj() to convert DC coords to or from meters. '''
        if inverse:
            if 1: 
                a *= self.ft
                b *= self.ft
            lon,lat = self._projDak(a,b,inverse=inverse)
            return lon,lat
        else:
            x,y = self._projDak(a,b)
            if 1:   # one version of proj4.exe reports in m rather than ft.
                x /= self.ft
                y /= self.ft
            return x,y
    
    def bounding_boxes(self):   
        ''' define appx bounding box for dakota county in each coordinate system. '''
        self.lon1,  self.lat1 = -93.33, 44.47
        self.utmx1, self.utmy1 = self.projUTM(self.lon1,self.lat1)
        self.dakx1, self.daky1 = self.projDak(self.lon1,self.lat1)
        self.lon2,  self.lat2 = -92.73, 44.9235
        self.utmx2, self.utmy2 = self.projUTM(self.lon2,self.lat2)
        self.dakx2, self.daky2 = self.projDak(self.lon2,self.lat2)
    
    def strproj(self, proj=None):
        ''' pretty format the projection definitions '''
        if proj is None: proj = 'DC UTM'
        DC,UTM = '',''
        if 'DC' in proj:
            DC = 'Projection definition for Dakota County coordinates:' 
            DC += '\n    '.join(self.Dakprojstring.split('+'))
        if 'UTM' in proj:
            UTM = 'Projection definition for UTM coordinates:' 
            UTM += '\n    '.join(self.UTMprojstring.split('+'))
        return '\n'.join((DC,UTM))
            
    def strDak(self, x, y, err=None):
        ''' Pretty format dak coords if err is given: 
                integer if xyerr = -1  (code for int) 
                integer if xyerr > 2   (xyerr is in ft)
                %9.2f   if 0 < xyerr < 2 
                %s      if xyerr = 0 
        '''
        if err:
            if err > 2:
                return '%i, %i, +/-%sft'%(np.round(x,0), np.round(y,0),err)
            elif err==-1:
                return '%i, %i'%(np.round(x,0),np.round(y,0))
            else:
                return '%9.2f, %9.2f, +/-%sft'%(x,y,err)
        else:
            return '%s, %s'%(x,y)

    def strUTM(self, x, y, err=None):
        ''' Pretty format UTM coords '''
        if err:
            if err > 2:
                return '%i, %i, +/-%sm'%(x,y,err)
            elif err==-1:
                return '%6.1f, %6.1f'%(x,y)
            else:
                return '%6.2f, %6.2f, +/-%sm'%(x,y,err)
        else:
            return '%6.2f, %6.2f'%(x,y)
        
    def strDDddd(self,lon,lat):
        return '%9.9f, %9.9f'%(lon,lat)
    
    def _strDD_MMmmm(self,fracDeg):
        s = '-' if fracDeg < 0 else ''
        fracDeg = abs(fracDeg)
        Deg = int(fracDeg)
        fracMin = (fracDeg-Deg)*60.0
        return '%s%i %6.6f'''%(s,Deg,fracMin)
    
    def strDD_MMmmm(self,lon,lat):
        return '%s, %s'%(self._strDD_MMmmm(lon),self._strDD_MMmmm(lat) )
    
    def _strDD_MM_SSsss(self,fracDeg):
        s = '-' if fracDeg < 0 else ''
        fracDeg = abs(fracDeg)
        Deg = int(fracDeg)
        fracMin = (fracDeg-Deg)*60.0
        Min = int(fracMin)
        fracSec = (fracMin-Min)*60.0
        return '%s%i %i'' %6.3f"'%(s,Deg,Min,fracSec)
    
    def strDD_MM_SSsss(self,lon,lat):
        return '%s, %s'%(self._strDD_MM_SSsss(lon),self._strDD_MM_SSsss(lat) )
    
    def _all_from_one(self,dakx,daky,utmx,utmy,lon,lat,xyerr):   
        if xyerr:
            lonerr,laterr = self.projDak( dakx+xyerr, daky+xyerr, inverse=True)
            lonlaterr = max( abs(lon-lonerr), abs(lat-laterr) )
            utmxerr,utmyerr = self.projUTM(lonerr,laterr)
            utmerr = max( abs(utmx-utmxerr), abs(utmy-utmyerr) )
        else:
            lonlaterr = utmerr = None
       
        rv = '\n'.join(('Dakota Co:  %s'%self.strDak(dakx,daky,-1),
                        'Dakota Co:  %s'%self.strDak(dakx,daky,xyerr),
                        'UTM         :  %s'%self.strUTM(utmx,utmy,utmerr),
                        'D.d         :  %s'%self.strDDddd(lon,lat),
                        'D M.m     :  %s'%self.strDD_MMmmm(lon,lat),
                        'D M S.s  :  %s'%self.strDD_MM_SSsss(lon, lat)))
        return rv                
         
    def all_from_dak(self,dakx,daky,xyerr=None):
        lon,lat = self.projDak(dakx,daky,inverse=True)
        utmx,utmy = self.projUTM(lon,lat)
        return self._all_from_one(dakx, daky, utmx, utmy, lon, lat, xyerr)
        

    def all_from_UTM(self,utmx,utmy,xyerr=None):
        lon,lat = self.projUTM(utmx,utmy,inverse=True)
        dakx,daky = self.projDak(lon,lat)
        return self._all_from_one(dakx, daky, utmx, utmy, lon, lat, xyerr)

    def all_from_lonlat(self,lon,lat,xyerr=None):
        dakx,daky = self.projDak(lon,lat)
        utmx,utmy = self.projUTM(lon,lat)
        return self._all_from_one(dakx, daky, utmx, utmy, lon, lat, xyerr)
        
#                        
#     def _utm_2_dak(self,utmx,utmy):
#         try:
#             (ulon,ulat) = self.projUTM(utmx,utmy,inverse=True)
#             return self.projDak(ulon,ulat)
#         except:
#             return None

    def _textDegrees_2_fracDegrees(self,src):
        ''' convert Degrees in text field to decimal degrees.
            src is a single text string containing ONE VALUE, EITHER lon OR lat
            src may be in format DD.ddd, DD MM.mmm, or DD MM SS.sssss 
            text may hold lon or lat in either order and with or without sign on Longitude.
            Returns decimal degrees.
        '''        
        src = src.strip()
        toks = src.split()
        if len(toks)==1:
            return float(src)
        else:
            D = int(toks[0])
            s = np.sign(D)
            D = abs(D)
            
        if len(toks)==2:
            return s * (D + float(toks[1])/60.0)
        else:
            M = int(toks[1]) 
        if len(toks)==3:
            return s * (D + M/60. + float(toks[2])/3600.0)
        else:
            return None

    def textDegrees_2_fracDegrees(self,src):
        ''' convert Degrees in text field to decimal degrees.
            src is a single text string containing BOTH lon AND lat
            Returns decimal lon and lat, with correct sign in order: lon,lat
            uses knowledge that original coordinate is in Dakota County to resolve lon from lat and sign.
        '''
        #try:
        src = src.strip()
        toks = src.split(',')
        if len(toks) != 2:
            toks = src.split()
        if len(toks) != 2:
            return 'ERROR 1: Must format lat lon as "lon lat" , "lon,lat" or "l o n,l a t"' 
        a = self._textDegrees_2_fracDegrees(toks[0])
        b = self._textDegrees_2_fracDegrees(toks[1]) 
        if not (a and b):
            return 'ERROR 2: Must format lat,lon using "DD.ddd", "DD MM.mmm", or "DD MM SS.sss"'
        if (abs(self.lon2) <  abs(a) < abs(self.lon1) ) and (self.lat1 < b < self.lat2):
            return  -abs(a),b
        if (abs(self.lon2) <  abs(b) < abs(self.lon1) ) and (self.lat1 < a < self.lat2):
            return -abs(b),a
        else:
            msg = '\n'.join( ('ERROR 3: lon lat are not in Dakota bounding box', 
                              'lonlat2: (%s, %s)'%(self.lon2,self.lat2),
                              'text:          %s'%src,
                              'lonlat1: (%s, %s)'%(self.lon1,self.lat1)))
            return msg                  


    def txtCoord_2_coord(self,src,boundingbox=None):
        try:
            src = src.replace('(','').replace(')','').strip()
            if ',' in src: 
                toks = src.split(',')
            else:
                toks = src.split()
            a,b = float(toks[0]), float(toks[1]) 
            if not (a and b):
                return 'ERROR 4: Must format coords as number,number'
            if not boundingbox:
                return a,b
            (x1,y1,x2,y2) = boundingbox
            if ( x1 < a < x2 ) and ( y1 < b < y2 ):
                return a,b
            if ( x1 < b < x2 ) and ( y1 < a < y2 ):
                return b,a
            return 'ERROR 5: coordinate is not in Dakota County bounding box'
        except:
            return None

    def handle_unspecified_coords(self,src):
        ''' src is a coordinate pair in lat-lon, utm, or dakota county coords '''
        C = self.textDegrees_2_fracDegrees(src)
        if isinstance(C,tuple):
            return self.all_from_lonlat(C[0],C[1])
        C = self.txtCoord_2_coord(src,boundingbox=(self.dakx1,self.daky1,self.dakx2,self.daky2))
        if isinstance(C,tuple):
            return self.all_from_dak(C[0],C[1])
        C = self.txtCoord_2_coord(src,boundingbox=(self.utmx1,self.utmy1,self.utmx2,self.utmy2))
        if isinstance(C,tuple):
            return self.all_from_UTM(C[0],C[1])
        return 'ERROR coordinates not recognized or not within Dakota County\n  "%s"'%src

#     def handle_unspecified_coords(self,src):
#         ''' src is a coordinate pair in lat-lon, utm, or dakota county coords '''
#         D = self.textDegrees_2_fracDegrees(src)
#         if D:
#             lon,lat = D
#             dakx,daky = self.projDak(lon,lat)
#             utmx,utmy = self.projUTM(lon,lat)
#         else: 
#             C = self.txtCoord_2_coord(src,boundingbox=(self.dakx1,self.daky1,self.dakx2,self.daky2))
#             if C:
#                 dakx,daky = C
#                 lon,lat = self.projDak(dakx,daky,inverse=True)
#                 utmx,utmy = self.projUTM(lon,lat)
#             else:
#                 C = self.txtCoord_2_coord(src,boundingbox=(self.utmx1,self.utmy1,self.utmx2,self.utmy2))
#                 if C:
#                     utmx,utmy = C
#                     lon,lat = self.projUTM(utmx,utmy,inverse=True)
#                     dakx,daky = self.projDak(lon,lat)
#                 else:
#                     return 'ERROR coordinates not recognized or not within Dakota County\n  "%s"'%src
            
            
        
import unittest


class Test(unittest.TestCase):
    
    def test_handle_unspecified_coords(self):
        P = DCcoordinate_projector()
        print '\ntest from latlon:    -92 55 55.50, 44 33 33.50'
        print P.handle_unspecified_coords('-92 55 55.50, 44 33 33.50')
        print '\ntest from utm        505393.746153, 4933998.97307'
        print P.handle_unspecified_coords('505393.746153, 4933998.97307')
        print '\ntest from dak        600248.828523, 132087.725159'
        print P.handle_unspecified_coords('600248.828523, 132087.725159')
    
    def okestDegreeConversions(self):
         
        P = DCcoordinate_projector()
        print P.active
        lon,lat = -92 - 55./60.0 - 55.50/3600.0, 44 + 33.0/60. + 33.55/3600.0
        print 'A',(lon,lat)
        lon,lat
        print ' ',P.textDegrees_2_fracDegrees('-92 55 55.50, 44 33 33.50') 
        print ' ','-92 55 55.50, 44 33 33.50'
        print P.strDD_MM_SSsss(lon, lat)

        lon,lat = -92 - 55.5234/60.0, 44 + 33.5234/60. 
        print 'B',(lon,lat)
        lon,lat
        print ' ',P.textDegrees_2_fracDegrees('-92 55.5234, 44 33.5234') 
        print ' ',P.textDegrees_2_fracDegrees(' 92 55.5234, 44 33.5234') 
        print ' ',P.textDegrees_2_fracDegrees('44 33.5234, -92 55.5234 ') 
        print ' ',P.textDegrees_2_fracDegrees('  44 33.5234 , 92 55.5234 ') 
        print ' ','-92 55.5234, 44 33.5234'
        print P.strDD_MMmmm(lon, lat)
        
        lon,lat = -92.9523456, 44.6523456 
        print 'C',(lon,lat)
        lon,lat
        print ' ', P.textDegrees_2_fracDegrees('-92.9523456,44.6523456') 
        print ' ',P.textDegrees_2_fracDegrees(' 92.9523456,44.6523456') 
        print ' ',P.textDegrees_2_fracDegrees(' 44.6523456 ,  92.9523456 ') 
        print ' ',P.textDegrees_2_fracDegrees(' 44.6523456 , -92.9523456 ') 
        print ' ','-92.9523456,44.6523456'
        print P.strDDddd(lon, lat)
        
    def okest4(self):
        ''' Demonstrate whether +units or +to_meter have any effect at all.  Seems not.'''
        ft = 0.3048006096012912
        from pyproj import Proj
        lon,lat = -92.832918, 44.608116
        print lon,lat
        P = Proj("+proj=lcc +lat_1=44.51666666666667 +lat_2=44.91666666666666 +lat_0=44.47194444444445 +lon_0=-93.31666666666666 +x_0=152400.3048006096 +y_0=30480.06096012192 +a=6378421.989 +b=6357036.347 +units=us-ft +to_meter=0.3048006096012912 +no_defs")
        lon,lat = -92.832918, 44.608116
        x,y = P(lon,lat)
        print x/ft,y/ft
        print P(x,y,inverse=True)
        
        print '\npart2'
        Q = Proj("+proj=lcc +lat_1=44.51666666666667 +lat_2=44.91666666666666 +lat_0=44.47194444444445 +lon_0=-93.31666666666666 +x_0=152400.3048006096 +y_0=30480.06096012192 +a=6378421.989 +b=6357036.347 +units=us-ft +no_defs")
        lon,lat = -92.832918, 44.608116
        x,y = Q(lon,lat)
        print x/ft,y/ft
        print Q(x,y,inverse=True)

        print '\npart3'
        R = Proj("+proj=lcc +lat_1=44.51666666666667 +lat_2=44.91666666666666 +lat_0=44.47194444444445 +lon_0=-93.31666666666666 +x_0=152400.3048006096 +y_0=30480.06096012192 +a=6378421.989 +b=6357036.347 +units=m +to_meter=1.0 +no_defs")
        lon,lat = -92.832918, 44.608116
        x,y = R(lon,lat)
        print x/ft,y/ft
        print R(x,y,inverse=True)

        print '\npart4'
        R = Proj("+proj=lcc +lat_1=44.51666666666667 +lat_2=44.91666666666666 +lat_0=44.47194444444445 +lon_0=-93.31666666666666 +x_0=152400.3048006096 +y_0=30480.06096012192 +a=6378421.989 +b=6357036.347 +no_defs")
        lon,lat = -92.832918, 44.608116
        x,y = R(lon,lat)
        print x/ft,y/ft
        print R(x,y,inverse=True)

        
    def okest_dakProj(self):
        ''' Validate the projDak projection ''' 
        P = DCcoordinate_projector()
        lon,lat = -92.832918, 44.608116
        x,y = P.projDak(lon,lat)
        print '\nTest3:'
        print 'given    ', 625993, 150021
        print 'computed ', x,y
        print 'given    ', lon,lat
        print 'computed ', P.projDak(x,y,inverse=True)
    
    def test_strproj(self):
        P = DCcoordinate_projector()
        print 40*'='
        print P.strproj()
        print 40*'='
    def sest1(self):
        samppairs = [[[ 509132.0, 100002.0 ],[ 477595.83471, 4924331.43866 ],None],      # created by projection.apr
             [[ 557154.0, 264637.0 ],[ 492421.38297, 4974433.05610 ],None],      # created by projection.apr
             [[ 636263.0, 189661.0 ],[ 516434.23865, 4951496.82928 ],None],      # created by projection.apr
             [[ 528325, 194914],[483555.42, 4953225.09],[-93.20768, 44.73222]],  # taken from ArcGIS on-screen coords.
             [[ 625993, 150021],[513258.28,4939432.07],[-92.832918, 44.608116]]] # taken from ArcGIS on-screen coords.
        xyfmt = ' %16.6f, %16.6f '
        llfmt = ' %10.6f, %10.6f '
        dcfmt = ' %11.4f, %11.4f '
        mmfmt = ' %12.5f, %13.5f '

        P = DCcoordinate_projector()
        for i,pairs in enumerate(samppairs):
            if pairs[2] is None:
                # fill in the missing lat lon
                [utmx,utmy] = pairs[1]        
                ulon,ulat = P.projUTM(utmx,utmy,inverse=True)
                pairs[2] = [ulon,ulat]
                samppairs[i] = pairs
            if 1:
                # verify projUTM and lat lon by testing projUTM both forward and back:
                [utmx,utmy] = pairs[1]        
                ulon,ulat = P.projUTM(utmx,utmy,inverse=True)
                [dlon,dlat] = pairs[2]
                if 0: print 'pair %i, lonlat precision: %6.4e, %6.4e'%(i, abs(ulon-dlon), abs(ulat-dlat))
                assert abs(ulon-dlon)<5.e-6 
                assert abs(ulat-dlat)<5.e-6
                px,py = P.projUTM(dlon,dlat)
                if 0: print 'pair %i,    UTM precision: %6.4e, %6.4e'%(i,abs(utmx-px), abs(utmy-py))
                assert abs(utmx-px)<3.e-1
                assert abs(utmy-py)<3.e-1
                (px,py) = P.projDak(dlon,dlat) 
                dcx,dcy = pairs[0]
                if 1: print 'pair %i,   DC precision: %6.4e, %6.4e'%(i,abs(px-dcx),abs(py-dcy))
                print '  f(lonlat)', dcfmt%(px,py)

                if 1: print 'pair %i'%i, dcfmt%(px,py),mmfmt%(utmx,utmy),llfmt%(ulon,ulat)
        llfmt = ' %10.6f, %10.6f '
        dcfmt = ' %11.4f, %11.4f '
        mmfmt = ' %12.5f, %13.5f '

    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()