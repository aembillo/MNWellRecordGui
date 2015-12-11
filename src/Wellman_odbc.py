'''
Created on July 24, 2015

@author: bomj8
'''
import unittest
import pyodbc
import os

class WellmanConnection():
    def __init__(self,well_project_fname=None):
        """ Here we define sql statements that create tables, queries, etc. """
        self.odbc_connection_string = 'DRIVER={SQL Server Native Client 11.0};SERVER=DB12;DATABASE=Wellwater_DB;UID=WellwaterRO;PWD=Drill&Fill;'
        self.connection_open = False
        self.well_project_fname = well_project_fname
        self.open_wellman_connection()
        self.close_wellman_connection()
    
    def open_wellman_connection(self):
        if self.connection_open:
            return True
        try:
            self.con = pyodbc.connect(self.odbc_connection_string)
            self.cur = self.con.cursor()
            self.connection_open = True
            self.ODBC_available = True
            return True
        except:
            self.connection_open = False
            self.ODBC_available = False
            self.read_Project_text_file(self.well_project_fname)
            return False
            
    def close_wellman_connection(self):
        try:
            self.cur.close()
            self.con.close()
            self.connection_open = False
        except:
            pass
        
    def get_wellman_values(self):
        if self.open_wellman_connection():
            id_dict = self.get_wellman_id_dict()
            project_list = self.get_wellman_projectname_list()
            self.close_wellman_connection()
            return id_dict,project_list
    
    def get_wellman_id_dict(self):
        ''' Queries Wellman for a list of well identifier values, with their well_id's
        
            We exclude types 
                18 (unused unique)           Because we don't want them.
                19 (wrong unique)            Because we don't want them.
                 6 (County Disclosure id)    Because they confound with well_id.
                            
        
        TODO:    
            We might like a more sophisticated query capability, say with ability to choose the identifier type,
            but this logic is not up to that: using the native llist=>dict method.  Might think of copying the 
            the wellman data to a local SQLite, or even just keeping the cursor open and using ODBC queries for
            every individual query: so no need for local dict object at all!
        '''
        sql = """
        SELECT
            RTRIM(G.well_id_type_value), 
            G.well_id 
        FROM
            PWP_WELL_ID_GROUP_RC AS G 
        WHERE
            ((NOT(G.well_id_type_value LIKE 'CWI%')  AND
            (G.well_id_type_value)<>'000000')  AND
            ((G.well_id_type)<>19) AND
            ((G.well_id_type)<>18) AND
            ((G.well_id_type)<>6)) 
        ORDER BY
            G.well_id_type_value, 
            G.well_id;        
        """
        # Note that Access uses "*" as wild card, while ODBC uses "%"
        return dict( self.cur.execute(sql).fetchall() )
    
    def get_wellman_projectname_list(self):
        """ Return the full and alphabetized list of  project_names  from Wellman. """
        sql = """
        SELECT 
            RTRIM(P.project_name)
        FROM 
            PWP_PROJECT_RC as P
        ORDER BY 
            P.project_name;
        """
        wellman_projectnames = []
        for rec in self.cur.execute(sql).fetchall():
            wellman_projectnames.append(rec[0].strip())
        return wellman_projectnames

    def query_wellman_well_project(self,identifier):
        """ Return the project name for a given well unique number. 
        
            If there is more than one project, return the first one.
            It there is no project, return 'None'.
        """
        sql = """
        SELECT
            RTRIM(WID.well_id_type_value), 
            P.project_name 
        FROM
            ( PWP_WELL_ID_GROUP_RC AS WID 
                LEFT JOIN PWP_WELL_PROJECT_RC AS WP 
                    ON WID.well_id = WP.well_id) 
                LEFT JOIN PWP_PROJECT_RC AS P 
                    ON WP.project_id = P.project_id 
        WHERE
            (WID.well_id_type_value='%s'); """%(identifier)
        print sql
        self.open_wellman_connection()
        rv = self.cur.execute( sql ).fetchone()
        self.close_wellman_connection()
        if len(rv)==2:
            if len(rv[1])>1:
                return rv[1]
        return None

    def get_project_name(self,well_id):
        """ return project_name for well identifier using ODBC if available, or else well_project.csv file """
        if self.ODBC_available:
            project_name = self.query_wellman_well_project(well_id)
        else:
            project_name = self.dict_well_project.get(well_id,"")
        return project_name
            
    def write_wellman_well_project_file(self,fname):
        """ Create a file listing project names for each well. 
        
            Format is determined by fname, only .csv is implemented.
            .csv format is: <Unique_no>,"<Project_name>".
        """
        sql = """
        SELECT
            RTRIM(WID.well_id_type_value), 
            P.project_name 
        FROM
            ( PWP_WELL_ID_GROUP_RC AS WID 
                LEFT JOIN PWP_WELL_PROJECT_RC AS WP 
                    ON WID.well_id = WP.well_id) 
                LEFT JOIN PWP_PROJECT_RC AS P 
                    ON WP.project_id = P.project_id 
        WHERE (   (P.project_name IS NOT NULL)
           AND NOT(WID.well_id_type_value= '000000')
           AND    (WID.well_id_type IN (1,2,10,11,12,17,21,24,22)) )
        ORDER BY
            WID.well_id_type_value; """
        print sql
        self.open_wellman_connection()
        data = self.cur.execute( sql ).fetchall()
        self.close_wellman_connection()
        
        rv = False
        if len(data)>=1:
            import csv
            f = open(fname, mode='w')
            if f:
                writer = csv.writer( f )
                writer.writerows(data)
                f.close()
                rv = True
        return rv

    def read_Project_text_file(self, fname=None): 
        """ Read the static csv file  Unique,"Project_Name"  into a saved dictionary.
        
            Will overwrite previously saved dict. Sets dict to None if file not found. Saves fname
            Not robust for poorly formatted file.
        """
        if fname:
            self.well_project_fname = fname
        if not(os.path.exists(self.well_project_fname)):
            self.dict_well_project = None
            return None
        import csv
        f = open(self.well_project_fname,mode='r')
        reader = csv.reader( f )
        self.dict_well_project = {rows[0]:rows[1] for rows in reader}  
        f.close()
               
class Test(unittest.TestCase):
    def get_well_project_fname(self):
        import os
        for dir in (r"C:\Bill\Git\Dakota_EDD\work",
                    r"C:\Git\Dakota_EDD\work"):
            if os.path.exists(dir):
                fname = os.path.join(dir,'well_projects.csv')
                return fname
        return None
    
    def test_WellmanConnection(self):
         
        W = WellmanConnection() 
        id_dict,project_list = W.get_wellman_values()
        
        assert id_dict.get("627088") == 7125
        assert 'FHR' in project_list
        
    def test_query_wellman_well_project(self):
        W = WellmanConnection() 
        project_name = W.query_wellman_well_project("608391")
        assert project_name == "FAA monitoring"
        
    def test_write_wellman_well_project_file(self):
        fname = self.get_well_project_fname()
        print "\nUnittest:  write_wellman_well_project_file(%s)"%fname
        W = WellmanConnection()
        OK = W.write_wellman_well_project_file(fname)
        assert OK
        print "well-project file written to: %s"%fname
        import os
        assert os.path.exists(fname)
        
    def test_read_Project_text_file(self):
        fname = self.get_well_project_fname()
        print "\nUnittest:  read_Project_text_file(%s)"%fname
        W = WellmanConnection()
        W.read_Project_text_file(fname)
        assert W.dict_well_project['608391']=='FAA monitoring'
        
        if 0:  # print out the project dictionary
            project_dict = W.project_dict
            assert project_dict is not None
            for key,value in project_dict.iteritems():
                print key,'\t>\t',value 

    def test_get_project_name(self):
        fname = self.get_well_project_fname()
        print "\nUnittest:  test_get_project_name()"
        W = WellmanConnection(fname)
        assert W.get_project_name('608391')=='FAA monitoring' 
        W.ODBC_available = False
        W.read_Project_text_file()
        assert W.get_project_name('608391')=='FAA monitoring' 
       
if __name__ == "__main__":
    unittest.main()