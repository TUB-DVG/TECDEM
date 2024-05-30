
# files contains all function to gather data from the provided GML files 
import lxml.etree as ET
import pandas as pd 
# from shapely.geometry import Polygon


# Define the namespaces used in the CityGML file
ns = {
        'core': "http://www.opengis.net/citygml/2.0",
        'gml': "http://www.opengis.net/gml",
        'bldg' : 'http://www.opengis.net/citygml/building/2.0',
        'energy' : 'http://www.sig3d.org/citygml/2.0/energy/1.0',
        # Add other necessary namespaces based on the file content
    }


def get_ids(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings at LoD3
    buildings = root.findall('.//bldg:Building', ns)
    print(buildings)
    gml_ids = []
    for building in root.findall('.//{*}Building'):
            # Get all IDs 
            gml_ids.append(building.get('{http://www.opengis.net/gml}id'))
    return gml_ids 


def get_address(file_path):
    """
    Parameters

    file_path: A string representing the path to the XML file to be parsed.
    
    Returns

    A list of tuples, where each tuple consists of:
        A building ID as a string.
        The associated address as a string. If the address is not found, an empty string is returned for that building.
    """
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings 
    buildings = root.findall('.//bldg:Building', ns)
    print(buildings)
    address_list = []
    for building in root.findall('.//{*}Building'):
        # Get all IDs 
        building_id = building.get('{http://www.opengis.net/gml}id')
        address_node = building.find('.//{*}address', ns)
        if address_node is None:
            address = ""
        else:
            # Code taken and adapted from 
            # https://simstadt.hft-stuttgart.de/attachments/scripts/list_building_ids_and_addresses.py 
            every_address_info = [text.strip() for text in address_node.itertext()]
            address_info = [text for text in every_address_info if text]
            address = (','.join(address_info))
            address_list.append((building_id, address))
                    
    return address_list

def get_yoc(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings
    yoc_list = []
    for building in root.findall('.//{*}Building'):
        # Get all IDs and yoc 
        building_id = building.get('{http://www.opengis.net/gml}id')
        yoc_node = building.find('.//{*}yearOfConstruction', ns)
        if yoc_node is None:
            yoc = ""
        else:
            yoc = building.find('bldg:yearOfConstruction', ns).text
        yoc_list.append((building_id, yoc))
                
    return yoc_list


def get_building_type(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings
    building_type_list = []
    for building in root.findall('.//{*}Building'):
        # Get all IDs and building types 
        building_id = building.get('{http://www.opengis.net/gml}id')
        bt_node = building.find('.//{*}function', ns)
        if bt_node is None:
            building_type = ""
        else:
            building_type = building.find('bldg:function', ns).text
        building_type_list.append((building_id, building_type))
                
    return building_type_list 


def get_floor_area(file_path):
    """" 
    Parameters: 

    file_path: A string representing the path to the XML file containing the building data.
    
    Returns

    floor_list: A list of tuples, where each tuple consists of a building identifier and its corresponding floor area. 
    The floor area is either a float representing the calculated area or an empty string if the area cannot be determined.
    """
     # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Find all buildings and get the data 
    floor_list = []
    for building in root.findall('.//{*}Building'):
        # Get all IDs and yoc 
        building_id = building.get('{http://www.opengis.net/gml}id')
        # 
        gs_node = building.find('.//{*}GroundSurface', ns)
        if gs_node is None:
                floor_area = ""
        else:
            pos_tags = gs_node.findall('.//gml:pos', ns)
            if len(pos_tags) == 0:
                # Try if the posList is used instead
                pos_list_tag = gs_node.find('.//gml:posList', ns)
                pos_list_text = pos_list_tag.text.strip()
                pos_list_values = pos_list_text.split(' ')
                # Convert the list of strings to the correct types (float or int)
                pos_list = [float(value) if '.' in value else int(value) for value in pos_list_values]
                #pos_tags =pos_tags_1.text
                polygon_data_str = [pos_list[i:i + 3] for i in range(0, len(pos_list), 3)]
                floor_area = polygon_area(polygon_data_str)
            else: 
                polygon_data_str = [pos.text.strip() for pos in pos_tags]
                polygon_data_flattened =  [float(num) for elem in polygon_data_str for num in elem.split(' ')]
                polygon_data_grouped = [polygon_data_flattened[i:i + 3] for i in range(0, len(polygon_data_flattened), 3)]
                floor_area = polygon_area(polygon_data_grouped)
            floor_list.append((building_id, floor_area))
                
    return floor_list 

def get_storeys_above(file_path):
    # Get the number of storeys above ground 
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings
    building_height_list = []
    for building in root.findall('.//{*}Building'):
        # Get all IDs and yoc 
        building_id = building.get('{http://www.opengis.net/gml}id')
        sag_node = building.find('.//{*}storeysAboveGround', ns)
        if sag_node is None:
            storeys_above_ground = ""
        else:
            storeys_above_ground = building.find('bldg:storeysAboveGround', ns).text
        building_height_list.append((building_id, storeys_above_ground))
                
    return building_height_list 

def get_height(file_path):
     # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings
    building_height_list = []
    for building in root.findall('.//{*}Building'):
        # Get all IDs and yoc 
        building_id = building.get('{http://www.opengis.net/gml}id')
        height_node = building.find('.//{*}measuredHeight', ns)
        if height_node is None:
            building_height = ""
        else:
            building_height = building.find('bldg:measuredHeight', ns).text
        building_height_list.append((building_id, building_height))
                
    return building_height_list

# Function to calculate the area of a polygon given its vertices
def polygon_area(coords):
    """
    Calculate the area of a polygon given its vertices.

    The function uses the 'Shoelace formula' to compute the area of a non-self-intersecting polygon
    whose vertices are described by a list of coordinates. The coordinates are provided as a list
    of lists or tuples, where each inner list or tuple contains the x and y coordinates of a vertex.

    Parameters:
    coords (list): A list of [x, y z] representing each vertex of the polygon, in order.

    Returns:
    float: The absolute area of the polygon.
    """
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    area = abs(area) / 2.0
    return area 


def addLoD0FootPrint(targetElement, nss, geomIndex, coordinates):
    # ToDo, figure out how this function really works 
    """ Function taken from: 
    https://gitlab.e3d.rwth-aachen.de/e3d-software-tools/cityldt/-/blob/main/LDTtransformation.py?ref_type=heads#L4 
    
    adds a LoD0 footprint form the coordinates to the target element using the namespaces"""
    footPrint_E = ET.Element(ET.QName(nss["bldg"], 'lod0FootPrint'))
    multiSurface_E = ET.SubElement(footPrint_E, ET.QName(nss["gml"], 'MultiSurface'))
    surfaceMember_E = ET.SubElement(multiSurface_E, ET.QName(nss["gml"], 'surfaceMember'))
    polygon_E = ET.SubElement(surfaceMember_E, ET.QName(nss["gml"], 'Polygon'))
    exterior_E = ET.SubElement(polygon_E, ET.QName(nss["gml"], 'exterior'))
    linearRing_E = ET.SubElement(exterior_E, ET.QName(nss["gml"], 'LinearRing'))
    for point in coordinates:
        # converting floats to string to join
        stringed = [str(j) for j in point]
        ET.SubElement(linearRing_E, ET.QName(nss["gml"], 'pos')).text = ' '.join(stringed)
    targetElement.insert(geomIndex, footPrint_E)


# Function to parse the CityGML file and calculate the area of a building at LoD3
def calculate_lod3_building_area(file_path):
    # Define the namespaces used in the CityGML file
    ns = {
        'core': "http://www.opengis.net/citygml/2.0",
        'gml': "http://www.opengis.net/gml",
        'bldg' : 'http://www.opengis.net/citygml/building/2.0',
        'energy' : 'http://www.sig3d.org/citygml/2.0/energy/1.0',
        # Add other necessary namespaces based on the file content
    }

    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all buildings at LoD3
    buildings = root.findall('.//bldg:Building', ns)
    print(buildings)
    gml_ids = []
    for building in root.findall('.//{*}Building'):
            gml_ids.append(building.get('{http://www.opengis.net/gml}id'))
    print(gml_ids)

    total_area = 0

    # Based on the ID 
    # Possible to return something 
    for building in buildings:
        # Find the geometry at LoD3
        lod3_multi_surface = building.find('.//bldg:lod3MultiSurface', ns)
        print(lod3_multi_surface)
        if lod3_multi_surface is not None:
            # Extract polygon coordinates and calculate area
            for surface_member in lod3_multi_surface.findall('.//gml:Polygon', ns):
                # Extract coordinates from the Polygon and create a Shapely polygon
                coordinates = []
                for pos_list in surface_member.findall('.//gml:posList', ns):
                    coords = [float(coord) for coord in pos_list.text.split()]
                    # Assuming coordinates are in the form [x1, y1, x2, y2, ..., xn, yn]
                    coordinates = list(zip(coords[::3], coords[1::3]))  # Extract only x, y
                polygon = Polygon(coordinates)
                total_area += polygon.area

    return total_area

     

if __name__ == '__main__':
   #  Test functions 
    file_path = r'C:\Users\felix\Programmieren\tecdm\data\examples\partialMierendorffInselLoD2.gml'
    

    ids = get_ids(file_path)
    print(f"The IDs are: {ids}")

    # Calculate and print the area
    area = calculate_lod3_building_area(file_path)
    print(f"The total area of the building at LoD3 is: {area} square units")