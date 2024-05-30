# functions takes the Sheet generated from city gml and turns it into a District Generator Model 
#from districtgenerator.classes.datahandler import Datahandler 
# change import statement https://github.com/RWTH-EBC/districtgenerator/issues/6 
import os 
import pandas as pd 
import numpy as np 
from districtgenerator import Datahandler





def create_scenario(sheet_file: str, scenario_name: str,
                    default_building_type: str ="SFH") -> str:
    """ 
    Takes the sheet name and creates a scenario 
    Calculates the area of a building
    Estimate the type, if non is conatained within the 
    gml file a default building type is used, options are [SFH, MFH, TH, AB]
    height of floors is considered 3.15 
    Expected output dataframe with content: id;building;year;retrofit;area
    """
    df = pd.read_csv(sheet_file, na_values="")
    df = calculate_area(df)
    df = parse_building_types(df, default_building_type)

    model_df = df.filter(["dg_id", "building", "year_of_construction", "renovation_status", "retrofit", "area"]) 
    rename_dict = {
        "dg_id" : "id",
        "year_of_construction" : "year",
        "renovation_status": "retrofit",
    }
    model_df.rename(columns=rename_dict, inplace=True) 
    scenario_folder = 'src\districtgenerator\data\scenarios'
    scenario_path = os.path.join(scenario_folder, f'{scenario_name}.csv')   
    try: model_df.to_csv(scenario_path, index=False, sep=";")
    except OSError:
        cwd_path = os.path.dirname(os.getcwd())
        scenario_folder = 'src\districtgenerator\data\scenarios'
        scenario_path = os.path.join(cwd_path, scenario_folder, f'{scenario_name}.csv')
        model_df.to_csv(scenario_path, index=False, sep=";")

    return scenario_path

    
def calculate_area(df, floor_height:float = 2.8):
    # In DG is is assumed that the average floor height is 3.15 m 
    # https://de.wikipedia.org/wiki/Raumh%C3%B6he 
    # Assume 20cm for floor height and 260cm for minimum height -> 280cm is more realistic 
    # See also: https://www.immobiliensachverstaendige-netzwerk.de/immobilienbegriffe-verstaendlich-gemacht/geschosshoehe 
    floor_height = floor_height
    df_copy = df.copy()

    # Create a new column 'area' based on the conditions
    conditions = [
        df_copy['storeys_above_ground'].notna(),  # Check if storeys_above_ground is not NaN
        df_copy['height'].notna()        # Check if measured_height is not NaN
    ]

    choices = [
        df_copy['floor_area'] * df_copy['storeys_above_ground'],  # storeys_above_ground * floor_area
        df_copy['floor_area'] * round(df_copy['height'] / floor_height)       # measured_height * floor_area
    ]

    df_copy['area'] = np.select(conditions, choices, default=df_copy['floor_area'])
    
    return df_copy


def parse_building_types(df: pd.DataFrame, default_building_type: str ="SFH"):
    # Function returns the building type, according to GML / ALkis code and size (if code refers to two Tabula Archetypes)
    # Typical sizes according to Tabula are here: src\auxilary\building_sizes.csv 
    # The Alkis and GML Codes are provided in src\auxilary\building_function_data.csv 
    # To-Do Figure out Codes that are not included in Alkis or GML Functions, e.g. 1169 
    # 1169 = Sozialeinrichtung 
    gml_ids = {1000: ["TH", "SFH", "MFH", "AB"]}
    alkis_ids = {1121: ["TH"], 
                 1221: ["MFH", "AB"], 
                 1231: ["MFH", "AB"], 
                 1331: ["SFH"], 
                 1321: ["TH"]}
    
    df_copy = df.copy()
    # Fehler, da unterschiedliche types vorliegen, e.g. int64 oder float 
    
    conditions = [ ( df_copy["building_type_gml"] == 1000) & (df_copy["area"] <= 140),
                  (df_copy["building_type_gml"] == 1000) & (df_copy["area"] > 140) & (df_copy["area"] <= 280),
                  (df_copy["building_type_gml"] == 1000) & (df_copy["area"] > 280) & (df_copy["area"] <= 800),
                  (df_copy["building_type_gml"] == 1000) & (df_copy["area"] > 800),
                  ( df_copy["building_type_gml"] == 1121), 
                   ( df_copy["building_type_gml"] == 1221 ) &(df_copy["area"] <= 800),
                   ( df_copy["building_type_gml"] == 1221 ) &( 800 < df_copy["area"]),
                   ( df_copy["building_type_gml"] == 1231 ) &(df_copy["area"] <= 800),
                   ( df_copy["building_type_gml"] == 1231 ) &( 800 < df_copy["area"]),  
                   ( df_copy["building_type_gml"] == 1331),
                   ( df_copy["building_type_gml"] == 1321),
                     ] 
    
    choices = [gml_ids[1000][0],
               gml_ids[1000][1], 
               gml_ids[1000][2],
               gml_ids[1000][3], 
               alkis_ids[1121][0],
               alkis_ids[1221][0], 
               alkis_ids[1221][1],
               alkis_ids[1231][0], 
               alkis_ids[1231][1],
               alkis_ids[1331][0],
               alkis_ids[1321][0]]
    
    # As default, set the most likely type in a given model 
    df_copy["building"] = np.select(conditions, choices, default=default_building_type)


    return df_copy


def set_yoc(path:str, yoc:int, retrofit:int):
    df = pd.read_csv(path, na_values="", sep=";")
    df["year"] = yoc
    df["retrofit"] = retrofit 
    df.to_csv(path, index=False, sep=";")
    return None



if __name__ == '__main__':

    # Path to the CityGM'L file
    file_path = r'C:\Users\felix\Programmieren\tecdm\data\model_sheets\FZKHouseLoD3-ADE-results.csv'
    

    scenario = create_scenario(file_path, "FZK-Haus")

    #data = Model(sheet_path=file_path, scenario_name="FZK-Haus")


    #print(vars(data))

    #data.generateEnvironment()
    
    # ids.to_csv(r'C:\Users\felix\Programmieren\tecdm\data\model_sheets\partialMierendorffInselLoD2.gml', index=False)

    # Calculate and print the area
    #area = calculate_lod3_building_area(file_path)
    #print(f"The total area of the building at LoD3 is: {area} square units")
# Aus dem Sheet ein Model erstellen
# Berechnung der Informationen 



# Generate Environment for the District
# data.generateEnvironment()

# Initialize Buildings to the District
# data.initializeBuildings(scenario_name="example")

# 1. Custom district file:

# At first, we will create a new custom district. Therefor you have to open the prepared CSV-file with the name
# "example2.csv" in the "data/scenarios/" directory of the districtgenerator. You can open the file with a text editor
# or a spreadsheet software as Microsoft Excel. Make sure that the separation signs stay semicolons!
# Except for the header in the first line (with information to each column), each row represents a building. In the
# first column the IDs of the buildings are stored. They start with zero. Just add an ongoing ID to each building
# you add. The "building"-column shows the short versions of the building types.
# You can choose "SFH", "MFH", "TH" and  "AB" for "single_family_house", "multi_family_house", "terraced_house"
# and "apartment_block". Next comes the construction year.
# It follows a code for status of modernisation (retrofit level) and the size of the living space.
# For more information about the possible settings in this central CSV-file, have a look into the ReadMe file.

# Now it is your turn! Add or delete some building to the CSV-file. Have in mind that more buildings need more
# computation time. Try to use some different options. Then save the file.

# Next we generate more information about the buildings.
# To do this we use the TEASER tool. This tool returns more detailed information about an archetype building
# according to the web database "Tabula". This includes window- and wall sizes, materials and more.
# Based on this and in combination with the weather data from the environment we calculate e.g. the heat flow
# through walls and internal gains. With this information we can e.g. calculate information about the buildings
# design heat load. The design heat load is calculated with DIN EN 12831.
# The number of occupants is between 1 and 5.

# Generate a more detailed Building
#    data.generateBuildings()
# data.generateDistrictComplete(scenario_name='example2', calcUserProfiles=True, saveUserProfiles=False)



