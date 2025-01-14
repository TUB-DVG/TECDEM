import pandas as pd
import logging as log

import os 
import pandas as pd 
import numpy as np
import re
from collections import Counter
from typing import Optional


# Building Functions obtained from https://www.berlin.de/sen/sbw/_assets/service/rechtsvorschriften/bereich-geoportal/liegenschaftskataster/alkis-ok_berlin.pdf
BUILDING_FUNCTIONS = {
    1000: ["TH", "SFH", "MFH", "AB"],
    1010: ["TH", "SFH", "MFH", "AB"],
    1121: ["TH"],
    1221: ["MFH", "AB"],
    1231: ["MFH", "AB"],
    1331: ["SFH"],
    1321: ["TH"],
    1022: ["IWU Health and Care"],

    2000: ["IWU Trade Buildings"],
    2010: ["IWU Trade Buildings"],
    2020: ["IWU Office, Administrative or Government Buildings"],
    2030: ["IWU Office, Administrative or Government Buildings"],
    2050: ["IWU Office, Administrative or Government Buildings"],
    2054: ["IWU Trade Buildings"],
    2055: ["IWU Trade Buildings"],
    2071: ["IWU Hotels, Boarding, Restaurants or Catering"],
    2083: ["IWU Hotels, Boarding, Restaurants or Catering"],
    2100: ["IWU Production, Workshop, Warehouse or Operations"],
    2111: ["IWU Production, Workshop, Warehouse or Operations"],
    2120: ["IWU Production, Workshop, Warehouse or Operations"],
    2160: ["IWU Research and University Teaching"],
    2200: ["IWU Generalized (2) Production buildings", "IWU Production, Workshop, Warehouse or Operations"],
    2310: ["IWU Trade Buildings"],
    2460: ["IWU Transport"],
    2461: ["IWU Transport"],
    2462: ["IWU Transport"],
    2463: ["IWU Transport"],
    2500: ["IWU Technical and Utility (supply and disposal)"],
    2520: ["IWU Technical and Utility (supply and disposal)"],
    2521: ["IWU Technical and Utility (supply and disposal)"],
    2522: ["IWU Technical and Utility (supply and disposal)"],
    2523: ["IWU Technical and Utility (supply and disposal)"],
    2540: ["IWU Office, Administrative or Government Buildings"],
    2571: ["IWU Technical and Utility (supply and disposal)"],
    2591: ["IWU Technical and Utility (supply and disposal)"],
    2600: ["IWU Technical and Utility (supply and disposal)"],
    2620: ["IWU Technical and Utility (supply and disposal)"],
    3010: ["IWU Office, Administrative or Government Buildings"],
    3015: ["IWU Office, Administrative or Government Buildings"],
    3020: ["IWU Research and University Teaching"],
    3021: ["IWU School, Day Nursery and other Care"],
    3023: ["IWU Research and University Teaching"],
    3041: ["IWU Culture and Leisure"],
    3044: ["IWU Culture and Leisure"],
    3060: ["IWU Health and Care"],
    3065: ["IWU School, Day Nursery and other Care"],
    3211: ["IWU Sports Facilities"],
    1440: ["IWU Sports Facilities"], 
}

def create_scenario(sheet_file: str, scenario_name: str,
                    default_building_type: str ="SFH", 
                    scenario_folder: str = "src/districtgenerator/data/scenarios") -> str:
    """ 
    Takes the sheet name and creates a scenario 
    Calculates the groundArea of a building
    Estimate the type, if non is conatained within the 
    gml file a default building type is used, options are [SFH, MFH, TH, AB]
    height of floors is considered 3.15 
    Expected output dataframe with content: id;building;year;retrofit;groundArea
    """
    if not os.path.exists(sheet_file):
        raise FileNotFoundError(f"File not found: {sheet_file}")
    df = pd.read_csv(sheet_file, na_values="", sep=",", decimal=".")
    df = calculate_groundArea(df)
  
    df = parse_building_types(df, default_building_type)
    df = heated_groundArea(df)
    

    model_df = df.filter(["dg_id", "building", "yearOfConstruction",
                          "renovation_status", "retrofit", "area", 
                          "groundArea", "heated_groundArea", "gml_id"])
    rename_dict = {
        "dg_id" : "id",
        "yearOfConstruction" : "year",
        "renovation_status": "retrofit",
        "gml_id" : "gml_id"
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


def calculate_groundArea(df, floor_height:float = 2.8):
    # In DG is is assumed that the average floor height is 3.15 m 
    # https://de.wikipedia.org/wiki/Raumh%C3%B6he 
    # Assume 20cm for floor height and 260cm for minimum height -> 280cm is more realistic 
    # See also: https://www.immobiliensachverstaendige-netzwerk.de/immobilienbegriffe-verstaendlich-gemacht/geschosshoehe 
    df_copy = df.copy()
    # Log which calculation method is being used for each building
    original_areas = df_copy[~(
        df_copy['storeysAboveGround'].notna() |
        (df_copy['measuredHeight'].notna() & df_copy['storeyHeightsAboveGround'].notna()) |
        df_copy['measuredHeight'].notna()
    )]
    if not original_areas.empty:
        log.info(f"{len(original_areas)} buildings using original groundArea")
        
    # conditions for the groundArea calculation
    conditions = [
        df_copy['storeysAboveGround'].notna(),  # Check if storeys_above_ground is not NaN
        (df_copy['measuredHeight'].notna() & df_copy['storeyHeightsAboveGround'].notna()), # Check if both height values exist
        df_copy['measuredHeight'].notna() # Check if only measured height exists
    ]
    
    choices = [
        df_copy['groundArea'] * df_copy['storeysAboveGround'],  # storeys_above_ground * floor_groundArea
        df_copy['groundArea'] * (df_copy['measuredHeight'] / df_copy['storeyHeightsAboveGround']).round(), 
        df_copy['groundArea'] * (df_copy['measuredHeight'] / floor_height).round()  # measured_height * floor_groundArea
    ]

    # Keep original groundArea as default if no conditions are met
    # TODO: this leads to incorrect area cacluation in case of buildings, that have building parts, as they have no measuredHeight or storeysAboveGround
    df_copy['floorArea'] = np.select(conditions, choices, default=df_copy['groundArea'])
    return df_copy

def heated_groundArea(df: pd.DataFrame):
    """
    Calculates the heated groundArea of a building, based on the groundArea and the type of building. 
    Factors are provided in src/auxilary/heated_groundArea.csv
    Factors are calculated on DATA NWG, where the factor is EBF (Energiebezugsfläche) / NRF (Nettoraumfläche). 
    Net floor groundArea is calculated after Kaden
    """
    df_copy = df.copy()
    df_copy.rename(columns={'groundArea': 'groundArea'}, inplace=True)
    # How to calculate net floor groundArea? 
    # After Kaden: https://mediatum.ub.tum.de/doc/1210304/1210304.pdf page 81
    # reduction factor for buildings with equally to or more than 3 floors is 0.76
    # reduction factor for buildings with less than 3 floors is 08
    df_copy["netFloorgroundArea"] = df_copy.apply(lambda row: row["floorArea"] * 0.76 if row["storeysAboveGround"] >= 3 else row["floorArea"] * 0.8, axis=1)


    # Read in the heated groundArea factor
    root_folder = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    auxillary_data = os.path.join(root_folder , "TECDEM", "src", "auxilary", "heated_area.csv")

    heated_groundArea_factors = pd.read_csv(auxillary_data, sep=";")
    df_copy_temp = df_copy.merge(heated_groundArea_factors, how='left', left_on='building', right_on='type')
    df_copy["area"] = df_copy_temp["netFloorgroundArea"] * df_copy_temp["heated_area_factor"].astype(float)
    return df_copy


def normalize_function_code(code_value):
    """
    Extract the trailing numeric portion of the function code, if it exists.
    Examples:
      - '31001_2310'  -> 2310
      - '2310'        -> 2310
      - '31001_1000'  -> 1000
    If no digits found, returns None.
    """
    if pd.isnull(code_value):
        return None
    
    elif "_" in code_value:
        code_value = code_value.split("_")[1]
        return int(float(code_value))
    else: 
        code_str = str(code_value).strip()
        match = re.search(r"(\d+(?:\.\d+)?)$", code_str)
        if match:
            try:
                return int(float(match.group(1)))
            except ValueError:
                return None

        return None

def get_building_subtype(candidates, floorArea, default_building_type: str = "SFH"):
    """
    Given a list of possible building types (candidates) and the ground area,
    decide which one is appropriate. For purely residential codes (e.g. 1000),
    we choose from TH/SFH/MFH/AB based on area thresholds. Otherwise,
    if only one candidate is in the list, we return it directly.
    """
    # Check for the typical residential codes:
    if any(t in ["TH", "SFH", "MFH", "AB"] for t in candidates):
        # Example logic: smaller area -> Townhouse, medium area -> SFH, etc.
        # You can adapt these thresholds to match your real definitions:
        if floorArea <= 140:
            return "TH"
        elif 140 < floorArea <= 280:
            return "SFH"
        elif 280 < floorArea <= 800:
            return "MFH"
        elif floorArea > 800:
            return "AB"
        else:
            return default_building_type

    # If the code is not purely residential or does not require sub-selection:
    if len(candidates) == 1:
        return candidates[0]

    # If multiple remain, pick the first or define more complex rules:
    return candidates[0]


def parse_building_types(df: pd.DataFrame, default_building_type: str = "SFH") -> pd.DataFrame:
    """
    Parses the building 'function' in the DataFrame.
    1) Normalizes the GML/ALKIS code to an integer suffix (e.g. 31001_2310 -> 2310).
    2) Looks up a list of candidate building types from BUILDING_FUNCTIONS.
    3) Uses groundArea to select the correct subtype if necessary.
    4) Falls back to default_building_type if the code is unknown or invalid.
    Returns a copy of df with a new column: 'building'.
    """

    df_copy = df.copy()

    # Convert 'function' to integer suffix
    df_copy["normalized_function"] = df_copy["function"].apply(normalize_function_code)

    # Identify any invalid codes
    invalid_mask = df_copy["normalized_function"].isna()
    if invalid_mask.any():
        invalid_codes = df_copy.loc[invalid_mask, "function"].unique()
        log.warning(f"Warning: Dropping {len(invalid_codes)} buildings with invalid function codes: {invalid_codes}")
        df_copy = df_copy.loc[~invalid_mask]

    # Retrieve candidate types from the dictionary
    df_copy["type_candidates"] = df_copy["normalized_function"].apply(
        lambda x: BUILDING_FUNCTIONS.get(x, [default_building_type])
    )

    # Decide final subtype
    df_copy["building"] = df_copy.apply(
        lambda row: get_building_subtype(row["type_candidates"], row["floorArea"]),
        axis=1
    )
    return df_copy

    
def clean_scenario(df: pd.DataFrame):
    """ 
    Cleans the scenario data, by removing buildings with a ground area of 0.
    """

def set_yoc(path:str, yoc:int, retrofit:int):
    """
    Sets the year of construction and the retrofit status of a building.
    #To-Do: Replace
    """
    df = pd.read_csv(path, na_values="", sep=";")
    df["year"] = yoc
    df["retrofit"] = retrofit 
    df.to_csv(path, index=False, sep=";")
    return None


