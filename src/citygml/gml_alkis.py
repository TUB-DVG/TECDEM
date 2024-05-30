# To Do, copy code from C:\Users\felix\Programmieren\tecdm\experiments\92_model_preparation.ipynb 
# and put it into a function in this file 
import pandas as pd 
import os
import lxml.etree as ET

# Define the namespaces used in the CityGML file
ns = {
        'core': "http://www.opengis.net/citygml/2.0",
        'gml': "http://www.opengis.net/gml",
        'bldg' : 'http://www.opengis.net/citygml/building/2.0',
        'energy' : 'http://www.sig3d.org/citygml/2.0/energy/1.0',
        # Add other necessary namespaces based on the file content
    }



def get_block(gml_file):
    """ 
    Returns the block number for all specific 
    """
    relative_file_path_block_data = r'data\berlin\09_GML_blocka.csv'
    working_dir = os.path.dirname(os.getcwd())
    file_path_block_data =  os.path.join(working_dir, relative_file_path_block_data)
    gml_bldg = pd.read_csv(file_path_block_data)
    groundsurface_list = get_groundsurfes(gml_file)

    gml_district = gml_bldg.loc[gml_bldg["gmlid"].isin([uid for bldg, uid in groundsurface_list])]
    blknr = gml_district["blknr"].unique().tolist()


    return blknr

def get_groundsurfes(file_path):
    """
    file_path: path to gml_file
    """
    groundsurface_list = []
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Find all buildings and get the data 
    for building in root.findall('.//{*}Building'):
        # Get all IDs and yoc 
        building_id = building.get('{http://www.opengis.net/gml}id')
        gs_node = building.find('.//{*}GroundSurface', ns)
        if gs_node is None:
            surface_id = ""
        else:
            surface_id =gs_node.get('{http://www.opengis.net/gml}id')
        groundsurface_list.append((building_id, surface_id))
    
    return groundsurface_list


if __name__ == '__main__':

    # Path to the CityGM'L file
    wd = os.path.dirname(os.getcwd())
    test_file = r'tecdm\data\examples\gml_data\20240216_PartialMierendorff.gml'
    file_path = os.path.join(wd, test_file)
    data = get_block(file_path)
    print(data)
    # Example usage
    