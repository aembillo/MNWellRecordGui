""" 2015-07-23
    
    Perform coordinate conversions from the command line.

    Uses 
"""
import argparse
import pyperclip

# p1 = argparse.ArgumentParser()
# p1.add_argument('x')
# print p1.parse_args(['123'])
# 
# p2 = argparse.ArgumentParser()
# p2.add_argument('-d', action='store_const',const='dak')
# print p2.parse_args(['-d'])
# 
# p3 = argparse.ArgumentParser()
# p3.add_argument('-d', action='store_const',const='dak')
# p3.add_argument('x')
# p3.add_argument('y')
# print p3.parse_args(['-d','1','2'])


#p1.add_argument(

from Coordinate_Transform import DCcoordinate_projector
# # 
# # parser = argparse.ArgumentParser()
# # parser.add_argument("coord_1")
# # parser.add_argument("coord_2")  
# # args = parser.parse_args()  
# # x,y = args.coord_1, args.coord_2
# 
def coord_convert():
     
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dak', action='store_const', const='dak', help="return Dakota County coords on clipboard")
    parser.add_argument('-u','--utm', action='store_const', const='utm', help="return UTM NAD 83, Zone 15 coords on clipboard")
    parser.add_argument('x')
    parser.add_argument('y')
    args = parser.parse_args()
    print 'args=',args
    coordtext = '%s,%s'%( args.x, args.y)
     
    Cprojector = DCcoordinate_projector()
    cliptext = Cprojector.handle_unspecified_coords(coordtext)
    #print outtext 
    try:
        if args.dak:
            cliptext = '%4.2f,%4.2f'%(Cprojector.dakx,Cprojector.daky)
            #print 'returning dakx,daky to clipboard "%s"'%cliptext
        elif args.utm:
            cliptext = '%4.2f,%4.2f'%(Cprojector.utmx,Cprojector.utmy)
            #print 'returning utmx,utmy to clipboard "%s"'%cliptext    
    except:
        pass 
    pyperclip.copy(cliptext)
    pyperclip.paste()
    
    return cliptext 
 
def test_parse_args():
    import sys
    sys.argv = ["prog", '-d', "93.0444", "44.5926"]
    rv = coord_convert()
    print '>>\n'+ str(rv) +'\n================'

    sys.argv = ["prog", '--utm', "93.0444", "44.5926"]
    rv = coord_convert()
    print '>>\n'+ str(rv) +'\n================'
     
if __name__ == '__main__':
    #test_parse_args()
    coord_convert()
    
'''
ERROR coordinates not recognized or not within Dakota County
  "570931,1441"

496475.91,4937695.85

Dakota Co:  570931, 144108
Dakota Co:  570931.0, 144108.0
UTM         :  496475.91, 4937695.85
D.d         :  -93.044399765, 44.592598646
D M.m     :  -93 2.663986, 44 35.555919
D M S.s  :  -93 2 39.839", 44 35 33.355"'''