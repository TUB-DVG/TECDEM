
# files contains all function to gather data from the provided GML files 
import lxml.etree as ET
import pandas as pd 
import shapely
from shapely.geometry import Polygon
try: 
    import citygml.geometric_strings as gs
except ModuleNotFoundError: 
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
    """Extract year of construction from CityGML file."""
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
    """
    Extract floor area for buildings, including interior and exterior surfaces.
    
    Parameters: 
    file_path: A string representing the path to the XML file containing the building data.
    
    Returns:
    floor_list: A list of tuples, where each tuple consists of a building identifier and its corresponding floor area. 
    The floor area is either a float representing the calculated area or an empty string if the area cannot be determined.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    floor_list = []
    
    for building in root.findall('.//{*}Building'):
        building_id = building.get('{http://www.opengis.net/gml}id')
        total_area = 0
        
        # Process main building
        total_area += calculate_building_area(building)
        
        # Process building parts
        for bp_element in building.findall('.//{*}consistsOfBuildingPart', ns):
            bp = bp_element.find('.//{*}BuildingPart', ns)
            total_area += calculate_building_area(bp)
        
        floor_list.append((building_id, total_area))
    
    return floor_list

def calculate_building_area(element):
    """
    Calculate the area of a building or building part, including interior and exterior surfaces.
    """
    area = 0
    ground_surface = element.find('.//{*}boundedBy/.//{*}GroundSurface', ns)
    
    if ground_surface is not None:
        area += calculate_surface_area(ground_surface)
    
    # Process all other surfaces (including interior)
    for surface in element.findall('.//{*}boundedBy/.//{*}Surface', ns):
        area += calculate_surface_area(surface)
    
    return area

def calculate_surface_area(surface_element):
    """
    Calculate the area of a single surface element.
    """
    polygon = surface_element.find('.//gml:Polygon', ns)
    if polygon is None:
        return 0
    
    exterior = polygon.find('.//gml:exterior', ns)
    interior = polygon.findall('.//gml:interior', ns)
    
    area = 0
    if exterior is not None:
        area += calculate_ring_area(exterior)
    
    for inner_ring in interior:
        area -= calculate_ring_area(inner_ring)
    
    return area

def calculate_ring_area(ring_element):
    """
    Calculate the area of a single ring (exterior or interior).
    """
    coords = []
    pos_list = ring_element.find('.//gml:posList', ns)
    if pos_list is not None:
        coords = gs.get_3dPosList_from_str(pos_list.text)
    else:
        pos_elements = ring_element.findall('.//gml:pos', ns)
        for pos in pos_elements:
            coords.append([float(x) for x in pos.text.split()])
    
    if coords:
        return polygon_area(coords)
    return 0

def get_storeys_above(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    building_height_list = []
    for building in root.findall('.//{*}Building'):
        building_id = building.get('{http://www.opengis.net/gml}id')
        sag_node = building.find('.//{*}storeysAboveGround', ns)
        storeys_above_ground = sag_node.text if sag_node is not None else ""
        building_height_list.append((building_id, storeys_above_ground))
                
    return building_height_list 

def get_height(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    building_height_list = []
    for building in root.findall('.//{*}Building'):
        building_id = building.get('{http://www.opengis.net/gml}id')
        height_node = building.find('.//{*}measuredHeight', ns)
        building_height = height_node.text if height_node is not None else ""
        building_height_list.append((building_id, building_height))
                
    return building_height_list

def polygon_area(coords):
    """
    Calculate the area of a polygon given its vertices.

    Parameters:
    coords (list): A list of [x, y, z] representing each vertex of the polygon, in order.

    Returns:
    float: The absolute area of the polygon.
    """
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    return abs(area) / 2.0

def getGroundSurfaceCoorOfBuild(element, nss):
    """
    Returns the ground surface coordinates from an element in a CityGML file.
    Adapted from: https://gitlab.e3d.rwth-aachen.de/e3d-software-tools/cityldt/-/blob/main/LDTselection.py
    """
    if element is None:
        return ''

    # Check LoD0
    for tagName in ['bldg:lod0FootPrint', 'bldg:lod0RoofEdge']:
        LoD_zero_E = element.find(tagName, nss)
        if LoD_zero_E is not None:
            return extract_coordinates(LoD_zero_E, nss)

    # Check GroundSurface
    groundSurface_E = element.find('.//{*}boundedBy/.//{*}GroundSurface', nss)
    if groundSurface_E is not None:
        return extract_coordinates(groundSurface_E, nss)

    # Check LoD1
    geometry = element.find('bldg:lod1Solid', nss)
    if geometry is not None:
        return extract_lod1_coordinates(geometry, nss)

    return ''

def extract_coordinates(element, nss):
    posList_E = element.find('.//{*}gml:posList', nss)
    if posList_E is not None:
        return gs.get_3dPosList_from_str(posList_E.text)
    
    pos_Es = element.findall('.//{*}gml:pos', nss)
    if pos_Es:
        polygon = [pos_E.text for pos_E in pos_Es]
        polyStr = ' '.join(polygon)
        return gs.get_3dPosList_from_str(polyStr)
    
    return ''

def extract_lod1_coordinates(geometry, nss):
    poly_Es = geometry.findall('.//gml:Polygon', nss)
    all_polygons = []
    for poly_E in poly_Es:
        polyStr = extract_polygon_string(poly_E, nss)
        if polyStr:
            all_polygons.append(gs.get_3dPosList_from_str(polyStr))
    
    if all_polygons:
        return find_lowest_polygon(all_polygons)
    
    return ''

def extract_polygon_string(poly_E, nss):
    posList_E = poly_E.find('.//gml:posList', nss)
    if posList_E is not None:
        return posList_E.text
    
    pos_Es = poly_E.findall('.//gml:pos', nss)
    if pos_Es:
        return ' '.join([pos_E.text for pos_E in pos_Es])
    
    return ''

def find_lowest_polygon(polygons):
    averages = [sum(point[2] for point in polygon) / len(polygon) for polygon in polygons]
    return polygons[averages.index(min(averages))]

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