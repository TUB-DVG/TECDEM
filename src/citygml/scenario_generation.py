# functions takes the Sheet generated from city gml and turns it into a District Generator Model 
#from districtgenerator.classes.datahandler import Datahandler 
# change import statement https://github.com/RWTH-EBC/districtgenerator/issues/6 
import os 
import pandas as pd 
import numpy as np


def create_scenario(sheet_file: str, scenario_name: str,
                    default_building_type: str ="SFH", 
                    scenario_folder: str = "src\districtgenerator\data\scenarios") -> str:
    """ 
    Takes the sheet name and creates a scenario 
    Calculates the area of a building
    Estimate the type, if non is conatained within the 
    gml file a default building type is used, options are [SFH, MFH, TH, AB]
    height of floors is considered 3.15 
    Expected output dataframe with content: id;building;year;retrofit;area
    """
    if not os.path.exists(sheet_file):
        raise FileNotFoundError(f"File not found: {sheet_file}")
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
    model_df["year"] = model_df["year"].astype("Int64")
    scenario_folder = scenario_folder
    scenario_path = os.path.join(scenario_folder, f'{scenario_name}.csv')   
    try: 
        model_df.to_csv(scenario_path, index=False, sep=";")
    except OSError:
        cwd_path = os.path.dirname(os.getcwd())
        scenario_folder = scenario_folder
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
    citygml_alkis = {
        31001_1000: ["SFH", "MFH", "TH", "AB"],
        31001_1010: ["SFH", "MFH", "TH", "AB"],
        31001_1120: ["SFH", "MFH", "TH", "AB"],
        31001_1130: ["SFH", "MFH", "TH", "AB"],
        31001_1022: ["IWU Health and Care"],
        31001_2000: ["IWU Trade Buildings"],
        31001_2010: ["IWU Trade Buildings"],
        31001_2020: ["IWU Office, Administrative or Government Buildings"],
        31001_2030: ["IWU Office, Administrative or Government Buildings"],
        31001_2050: ["IWU Office, Administrative or Government Buildings"],
        31001_2054: ["IWU Trade Buildings"],
        31001_2055: ["IWU Trade Buildings"],
        31001_2071: ["IWU Hotels, Boarding, Restaurants or Catering"],
        31001_2083: ["IWU Hotels, Boarding, Restaurants or Catering"],
        31001_2100: ["IWU Production, Workshop, Warehouse or Operations"],
        31001_2111: ["IWU Production, Workshop, Warehouse or Operations"],
        31001_2120: ["IWU Production, Workshop, Warehouse or Operations"],
        31001_2310: ["IWU Trade Buildings"],
        31001_2460: ["IWU Transport"],
        31001_2461: ["IWU Transport"],
        31001_2462: ["IWU Transport"],
        31001_2463: ["IWU Transport"],
        31001_2500: ["IWU Technical and Utility (supply and disposal)"],
        31001_2520: ["IWU Technical and Utility (supply and disposal)"],
        31001_2521: ["IWU Technical and Utility (supply and disposal)"],
        31001_2522: ["IWU Technical and Utility (supply and disposal)"],
        31001_2523: ["IWU Technical and Utility (supply and disposal)"],
        31001_2540: ["IWU Office, Administrative or Government Buildings"],
        31001_2571: ["IWU Technical and Utility (supply and disposal)"],
        31001_2591: ["IWU Technical and Utility (supply and disposal)"],
        31001_2600: ["IWU Technical and Utility (supply and disposal)"],
        31001_3010: ["IWU Office, Administrative or Government Buildings"],
        31001_3015: ["IWU Office, Administrative or Government Buildings"],
        31001_3020: ["IWU Research and University Teaching"],
        31001_3021: ["IWU School, Day Nursery and other Care"],
        31001_3023: ["IWU Research and University Teaching"],
        31001_3041: ["IWU Culture and Leisure"],
        31001_3044: ["IWU Culture and Leisure"],
        31001_3060: ["IWU Health and Care"],
        31001_3065: ["IWU School, Day Nursery and other Care"],
        31001_3211: ["IWU Sports Facilities"],
        51006_1440: ["IWU Sports Facilities"]
    }

    df_copy = df.copy()
    df_copy["building_type_gml"] = df_copy["building_type_gml"].astype(int)

    def get_building_type(row):
        gml_code = row["building_type_gml"]
        area = row["area"]

        if gml_code in gml_ids:
            if area <= 140:
                return gml_ids[gml_code][0]
            elif area <= 280:
                return gml_ids[gml_code][1]
            elif area <= 800:
                return gml_ids[gml_code][2]
            else:
                return gml_ids[gml_code][3]
        elif gml_code in alkis_ids:
            if gml_code == 1221 or gml_code == 1231:
                return alkis_ids[gml_code][0] if area <= 800 else alkis_ids[gml_code][1]
            else:
                return alkis_ids[gml_code][0]
        elif gml_code in citygml_alkis:
            if gml_code in [31001_1000, 31001_1010, 31001_1120, 31001_1130]:
                if area <= 140:
                    return citygml_alkis[gml_code][0]
                elif area <= 280:
                    return citygml_alkis[gml_code][1]
                elif area <= 800:
                    return citygml_alkis[gml_code][2]
                else:
                    return citygml_alkis[gml_code][3]
            else:
                return citygml_alkis[gml_code][0]
        else:
            return default_building_type

    df_copy["building"] = df_copy.apply(get_building_type, axis=1)

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



