'''
Created on July 24, 2015

@author: bomj8
'''
import unittest

class WellmanConnection():
    def __init__(self):
        """ Here we define sql statements that create tables, queries, etc. """
        self.odbc_connection_string = 'DRIVER={SQL Server Native Client 11.0};SERVER=DB12;DATABASE=Wellwater_DB;UID=WellwaterRO;PWD=Drill&Fill;'
        pass
    
    def get_wellman_values(self):
        import pyodbc
        con = pyodbc.connect(self.odbc_connection_string)
        self.cur = con.cursor()
        id_dict = self.get_wellman_id_dict()
        project_list = self.get_wellman_projectname_list()
        self.cur.close()
        con.close()
        return id_dict,project_list
    
    def get_wellman_id_dict(self):
        sql = """
        SELECT
            G.well_id_type_value, 
            G.well_id 
        FROM
            PWP_WELL_ID_GROUP_RC AS G 
        WHERE
            ((NOT(G.well_id_type_value LIKE 'CWI*')  AND
            (G.well_id_type_value)<>'000000')  AND
            ((G.well_id_type)<>19  AND
            (G.well_id_type)<>18)) 
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

class Test(unittest.TestCase):
    def test_WellmanConnection(self):
         
        W = WellmanConnection() 
        id_dict,project_list = W.get_wellman_values()
        
        assert id_dict.get("627088") == 7125
        assert 'FHR' in project_list
 
if __name__ == "__main__":
    unittest.main()