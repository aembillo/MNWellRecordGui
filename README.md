# MNWellRecordGui
A python GUI tool for accessing Well records and record images in Minnesota. 
Written in Python 2.7, and tested on Windows 7 only.

This library has dependencies on a number of non-standard python libraries, and you're on your own to install them.  The biggest ones are wx, numpy, pyodbc, and pyproj.  

pyodbc is used to query a SQLserver db (Wellman) to get well identifiers used for requesting images from the Dakota County image storage system (On-Base).

The GUI can use pyproj with proj4 (if installed on your computer) to perform coordinate transforms between Dakota County Coordinates, UTM Zone 15 Nad83, and lat-lon. Current code uses the assumption that points are in or near Dakota County in order to decide the input coordinate system and whether the coordinates are entered as x,y or y,x.  Includes a command line python interface that returns projection results on the system clipboard, which can be run from an Avenue script in ArcView.

Logins and private url's should not be included in this public project. Please request login information from the author; or, if you know the private information and can read Python, then you can figure out how to get it entered.
