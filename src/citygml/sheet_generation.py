
# Function reads the GML Files and creates a basic model Sheet
# Data is saved in /data
# Model sheet can than be ued for Basic Modelling of the district 
# In this file all function that make assumptions or parse gml data are generated 
import pandas as pd 
import numpy as np
import os 
from pathlib import Path 
from file_handling import get_ids
from file_handling import get_address 
from file_handling import get_yoc 
from file_handling import get_building_type
from file_handling import get_floor_area 
from file_handling import get_height
from file_handling import get_storeys_above

# BASE PATH: "src"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = str(Path(ROOT_DIR).parents[0])
#RES_DIR = os.path.join(PROJECT_DIR, 'results')
#DATA_DIR = os.path.join(PROJECT_DIR, 'data') 

def create_sheet(file_path:str):
    """
    returns a Pandas DataFrame with:
        - gml_id: ID Of the GML-Building
        - dg_id: ID used for Modelling within the District generator, starts with 0
        - address: Address of the Building 
        - building_type_gml: Type the Building is commonly used for, e.g. Housing 
        - year_of_construction: the year of construction of the building 
        - renovation_status: currently Unclear 
        - floor_area: floor area of the building, according to the ground floor 
        - height: measured height in the building 
    """

    #Extract data from the provided GML file 
    list_ids = get_ids(file_path)
    print(list_ids)
    address_tuple = get_address(file_path)
    yoc_tuple = get_yoc(file_path)
    type_tuple = get_building_type(file_path) 
    # currently unclear where to get the information from
    renovations_status = ""
    floor_area = get_floor_area(file_path)
    height = get_height(file_path)
    storeys_above_ground = get_storeys_above(file_path)

    # Set up a dictionary and map the attributes based on the gml_id 
    # Data is parsed from the GML File 
    df = pd.DataFrame({"gml_id":list_ids})
    df["dg_id"] = df.index 
    df["address"] = df["gml_id"].map(dict(address_tuple))
    df["building_type_gml"] = df["gml_id"].map(dict(type_tuple))
    df["year_of_construction"] = df["gml_id"].map(dict(yoc_tuple))
    # To do figure out how to get reneovation data -> Not present in ADE 
    # df["renovation_status"] = df["gml_id"].map(dict(yoc_tuple))
    df["renovation_status"] = ""
    df["floor_area"] = df["gml_id"].map(dict(floor_area))
    df["height"] = df["gml_id"].map(dict(height))
    df["storeys_above_ground"] = df["gml_id"].map(dict(storeys_above_ground))
    
    print(df.head())
    # Fuctions to caluclate data or assume data 
    # get the average floor height 
    df = get_average_floor_height(df)
    

    # Idea if data not present here but in the final sheet add term - Estimated 
    return df 

def get_average_floor_height(df):
    """
    Calculates the average floor height of buildings based on total height and number of storeys.

    Parameters:
        df (pd.DataFrame): DataFrame containing the building heights and storeys.

    Returns:
        pd.DataFrame: Updated DataFrame with the 'average_floor_height' column added.
    """
    # Set a default floor height assumption
    default_floor_height = 2.8

    # Ensure 'height' and 'storeys_above_ground' are numeric and handle missing data
    df['height'] = pd.to_numeric(df['height'], errors='coerce')
    df['storeys_above_ground'] = pd.to_numeric(df['storeys_above_ground'], errors='coerce')

    # Calculate average floor height with a conditional fallback to the default
    df['average_floor_height'] = df.apply(
        lambda x: x['height'] / x['storeys_above_ground'] if pd.notnull(x['height']) and pd.notnull(x['storeys_above_ground']) else default_floor_height,
        axis=1
    )

    return df


if __name__ == '__main__':

    # Path to the CityGM'L file
    file_path = r'C:\Users\felix\Programmieren\TECDEM\data\berlin\LoD2_33_384_5820_1_BE.xml'
    

    ids = create_sheet(file_path)
    ids.to_csv(r'C:\Users\felix\Programmieren\tecdm\data\model_sheets\partialMierendorffInselLoD2.csv', index=False)

    # Calculate and print the area
    #area = calculate_lod3_building_area(file_path)
    #print(f"The total area of the building at LoD3 is: {area} square units")