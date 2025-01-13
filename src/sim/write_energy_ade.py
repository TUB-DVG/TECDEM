# Take the data form the model and  save it as gml file
# Necessary steps: 
# - create a model 
# - get data from the model
# - attach it to the gml file 
import numpy as np
import pandas as pd 
import os 
from lxml import etree  


# Define the namespaces used in the CityGML file
ns = {
        'core': "http://www.opengis.net/citygml/2.0",
        'gml': "http://www.opengis.net/gml",
        'bldg' : 'http://www.opengis.net/citygml/building/2.0',
        'energy' : 'http://www.sig3d.org/citygml/2.0/energy/1.0',
        # Add other necessary namespaces based on the file content
    }


def extract_energy_demand_for_analysis(gml_path):
    """
    Extracts 'EnergyDemand' data along with 'energy:values' and their 'uom' from a GML file,
    converting the values into a format suitable for analysis (e.g., numpy array).

    Parameters:
    gml_path (str): Path to the GML file.

    Returns:
    pandas.DataFrame: DataFrame containing the 'EnergyDemand' data along with values and units of measure.
    """

    # Parse the GML file
    tree = etree.parse(gml_path)
    root = tree.getroot()

    # Define the namespace map to simplify finding elements
    namespaces = {k if k is not None else 'default': v for k, v in root.nsmap.items()}

    # Find all 'EnergyDemand' elements
    energy_demand_elements = tree.xpath('//energy:EnergyDemand', namespaces=namespaces)


    # Extract relevant data from these elements
    data = []
    for elem in energy_demand_elements:
        energy_demand_data = {'gml_id': elem.get('{http://www.opengis.net/gml}id')}
        for child in elem.iterdescendants():
            if child.tag.endswith('acquisitionMethod'):
                energy_demand_data['acquisition_method'] = child.text
            elif child.tag.endswith('interpolationType'):
                energy_demand_data['interpolation_type'] = child.text
            elif child.tag.endswith('source'):
                energy_demand_data['source'] = child.text
            elif child.tag.endswith('thematicDescription'):
                energy_demand_data['thematic_description'] = child.text
            elif child.tag.endswith('beginPosition'):
                energy_demand_data['begin_position'] = child.text
            elif child.tag.endswith('endPosition'):
                energy_demand_data['end_position'] = child.text
            elif child.tag.endswith('uom'):
                energy_demand_data['unit_of_measure'] = child.text
            elif child.tag.endswith('values'):
                # Splitting the values string and converting to a numpy array of floats
                values = np.array(child.text.split(), dtype=float)
                energy_demand_data['energy_values'] = values

        data.append(energy_demand_data)

    # Convert the extracted data to a pandas DataFrame
    df = pd.DataFrame(data)
    return df


if __name__ == '__main__':

    # Path to the CityGM'L file
    file_path = r'C:\Users\felix\Programmieren\tecdm\data\examples\gml_data\FZKHouseLoD2-ADE-results.gml'
    # Example usage
    