
# files contains all function to gather data from the provided GML files 
import lxml.etree as ET
import pandas as pd 
from shapely.geometry import Polygon
import geometric_strings as gs


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
        if bt_node is not None:
            building_type = bt_node.text
        else:
            building_type = ""
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
        building_id = building.get('{http://www.opengis.net/gml}id')
        bp_gC = getGroundSurfaceCoorOfBuild(building, ns)
        bp_gC_2d = [(x, y) for x, y, z in bp_gC]
        polygon = Polygon(bp_gC_2d)
        floor_area = polygon.area 

        
        for co_bp_E in building.findall('.//{*}consistsOfBuildingPart', ns):
            bp_E = co_bp_E.find('.//{*}BuildingPart', ns)
            bp_gC = getGroundSurfaceCoorOfBuild(bp_E, ns)
            building_part_id = bp_E.get('{http://www.opengis.net/gml}id')
            bp_gC_2d = [(x, y) for x, y, z in bp_gC]
            polygon = Polygon(bp_gC_2d)
            floor_area += polygon.area
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
        if height_node is not None:
            building_height = height_node.text
        else:
            building_height = ""
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


def getGroundSurfaceCoorOfBuild(element, nss):
    """returns the ground surface coordinates from an element in a citygml file
    Function take and adapted from: https://gitlab.e3d.rwth-aachen.de/e3d-software-tools/cityldt/-/blob/main/LDTselection.py?ref_type=heads
    """

    # LoD0
    if element is not None:
        for tagName in ['bldg:lod0FootPrint', 'bldg:lod0RoofEdge']:
            LoD_zero_E = element.find(tagName, nss)
            if LoD_zero_E != None:
                posList_E = LoD_zero_E.find('.//{*}gml:posList', nss)
                
                if posList_E != None:
                    return gs.get_3dPosList_from_str(posList_E.text)

                else:                           # case hamburg lod2 2020
                    pos_Es = LoD_zero_E.findall('.//{*}gml:pos', nss)
                    polygon = []
                    for pos_E in pos_Es:
                        polygon.append(pos_E.text)
                    polyStr = ' '.join(polygon)
                    return gs.get_3dPosList_from_str(polyStr)

        groundSurface_E = element.find('.//{*}boundedBy/.//{*}GroundSurface', nss)
        if groundSurface_E != None:
            posList_E = groundSurface_E.find('.//gml:posList', nss)       # searching for list of coordinates

            if posList_E != None:           # case aachen lod2
                return gs.get_3dPosList_from_str(posList_E.text)
                
            else:                           # case hamburg lod2 2020
                pos_Es = groundSurface_E.findall('.//gml:pos', nss)
                polygon = []
                for pos_E in pos_Es:
                    polygon.append(pos_E.text)
                polyStr = ' '.join(polygon)
                return gs.get_3dPosList_from_str(polyStr)
    
        #  checking if no groundSurface element has been found
        else:               # case for lod1 files
            geometry = element.find('bldg:lod1Solid', nss)
            if geometry != None:
                poly_Es = geometry.findall('.//gml:Polygon', nss)
                all_poylgons = []
                for poly_E in poly_Es:
                    polygon = []
                    posList_E = element.find('.//gml:posList', nss)       # searching for list of coordinates
                    if posList_E != None:
                        polyStr = posList_E.text
                    else:
                        pos_Es = poly_E.findall('.//gml:pos', nss)        # searching for individual coordinates in polygon
                        for pos_E in pos_Es:
                            polygon.append(pos_E.text)
                        polyStr = ' '.join(polygon)
                    coor_list = gs.get_3dPosList_from_str(polyStr)
                    all_poylgons.append(coor_list)
                
                # to get the groundSurface polygon, the average height of each polygon is calculated and the polygon with the lowest average height is considered the groundsurface
                averages = []
                for polygon in all_poylgons:
                    # need to get polygon with lowest z coordinate here
                    average = 0
                    for i in range(len(polygon)-1):
                        average -=- polygon[i][2]
                    averages.append(average/(len(polygon)-1))

                return all_poylgons[averages.index(min(averages))]
            else:
                return ''

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

if __name__ == '__main__':
   #  Test functions 
    file_path = r'C:\Users\felix\Programmieren\tecdm\data\examples\partialMierendorffInselLoD2.gml'
    

    ids = get_ids(file_path)
    print(f"The IDs are: {ids}")

    # Calculate and print the area
    area = calculate_lod3_building_area(file_path)
    print(f"The total area of the building at LoD3 is: {area} square units")