'''
Created on July 24, 2015

@author: bomj8
'''
import unittest
import pyodbc

class WellmanConnection():
    def __init__(self):
        """ Here we define sql statements that create tables, queries, etc. """
        self.odbc_connection_string = 'DRIVER={SQL Server Native Client 11.0};SERVER=DB12;DATABASE=Wellwater_DB;UID=WellwaterRO;PWD=Drill&Fill;'
        self.connection_open = False
    
    def open_wellman_connection(self):
        self.con = pyodbc.connect(self.odbc_connection_string)
        self.cur = self.con.cursor()
        self.connection_open = True
    def close_wellman_connection(self):
        self.cur.close()
        self.con.close()
        self.connection_open = False
        
    def get_wellman_values(self):
        self.open_wellman_connection()
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
            G.well_id_type_value, 
            G.well_id 
        FROM
            PWP_WELL_ID_GROUP_RC AS G 
        WHERE
            ((NOT(G.well_id_type_value LIKE 'CWI*')  AND
            (G.well_id_type_value)<>'000000')  AND
            ((G.well_id_type)<>19) AND
            ((G.well_id_type)<>18) AND
            ((G.well_id_type)<>6)) 
        ORDER BY
            G.well_id_type_value, 
            G.well_id;        
        """
        return dict( self.cur.execute(sql).fetchall() )
    
    def get_wellman_projectname_list(self):
        sql = """
        SELECT 
            P.project_name
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
        sql = """
        SELECT
            WID.well_id_type_value, 
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
            
class Test(unittest.TestCase):
    def test_WellmanConnection(self):
         
        W = WellmanConnection() 
        id_dict,project_list = W.get_wellman_values()
        
        assert id_dict.get("627088") == 7125
        assert 'FHR' in project_list
        
    def test_query_wellman_well_project(self):
        W = WellmanConnection() 
        project_name = W.query_wellman_well_project("608391")
        assert project_name == "FAA monitoring"
        

 
if __name__ == "__main__":
    unittest.main()