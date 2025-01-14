import logging as log

import os 
import re
from collections import Counter
from typing import Optional
import math

import pandas as pd
import numpy as np

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

 # Read in the heated groundArea factor
ROOT_FOLDER = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
AUXILLARY_DATA = os.path.join(ROOT_FOLDER , "TECDEM", "src", "auxilary", "heated_area.csv")
HEATED_GROUND_AREA_FACTOR = pd.read_csv(AUXILLARY_DATA, sep=";")
HEATED_GROUND_AREA_FACTOR_DICT = {
    type: heated_area_factor for type, heated_area_factor in zip(HEATED_GROUND_AREA_FACTOR["type"].tolist(), HEATED_GROUND_AREA_FACTOR["heated_area_factor"].tolist())
}
print(HEATED_GROUND_AREA_FACTOR_DICT)

class Building():
    """Represents a building and allows aggregation of building parts."""
    
    def __init__(self, id: str, ground_area: float = 0.0, building_func: str = None,
                 measured_height: float = None, storeys_above_ground: int = None) -> None:
        """
        Initialize a new building.
        
        Parameters
        ----------
        id : str
            The unique identifier (e.g., gml:id) of the Building.
        ground_area : float, optional
            Ground area of the building (default is 0.0).
        building_func : str, optional
            The building function/type (default is None).
        measured_height : float, optional
            The measured height of the building (default is None).
        storeys_above_ground : int, optional
            The number of storeys above ground (default is None).
        floor_area : float, optional
            The floor area of the building (default is None). 
            Is calculated from the ground area and the storeys above ground, as well as the measured height.
        """
        self.id = id
        self.building_parts = []  # List to hold aggregated building parts
        self.is_building_part = False
        self.ground_area = ground_area
        self.building_func = building_func
        self.building_type = None
        self.measured_height = measured_height
        self.storeys_above_ground = storeys_above_ground
        self.floor_area = None
        self.heated_ground_area = None
        self.heated_area_factor = None


    def add_building_part(self, part: "Building"):
        """Adds a building part to this building."""
        self.building_parts.append(part)

    def aggregate_area_from_parts(self):
        """Aggregates ground area from all building parts into the main building."""
        if self.has_building_parts():
            total_area = sum(part.ground_area for part in self.building_parts)
            self.ground_area += total_area

    def propagate_function_to_parts(self):
        """Copies the building function of the parent to all its parts."""
        if self.has_building_parts():
            for part in self.building_parts:
                part.building_func = self.building_func

    def has_building_parts(self) -> bool:
        """Check if the building has building parts."""
        return len(self.building_parts) > 0

    def get_building_parts(self) -> list:
        """Returns a list of building parts of the building."""
        return self.building_parts

    def get_building_part_ids(self) -> list:
        """Returns list of building part ids of the given building."""
        return [part.id for part in self.building_parts]



class Scenario:
    def __init__(self, sheet_file: str, scenario_name: str,
                 default_building_type: str ="SFH", 
                 scenario_folder: str = "",
                 aggregate_parts: bool = True):
        self.sheet_file = sheet_file
        self.scenario_name = scenario_name
        self.buildings = {}
        self.default_building_type = default_building_type
        self.scenario_folder = scenario_folder
        self.aggregate_parts = aggregate_parts
        self.df = None
        self.clean_data = None

    def load_sheet(self):
        """Loads the CSV file into a DataFrame."""
        if not os.path.exists(self.sheet_file):
            raise FileNotFoundError(f"File not found: {self.sheet_file}")
        self.df = pd.read_csv(self.sheet_file, na_values="", sep=",", decimal=".")


    def parse_building_types(self, building: Building):
        """Parses building types using the helper function."""
        building.building_type = normalize_function_code(building.building_func)


    def compute_heated_ground_area(self, building: Building):
        """Computes heated ground area using the helper function."""
        calculate_groundArea_from_parts(building)


    def generate_model_dataframe(self) -> pd.DataFrame:
        """Generates a DataFrame in the expected model format."""
        # Generate a dataframe with the expected columns
        model_list = []
        for building_id, building in self.buildings.items(): 
            building_dict = {
                "id": building_id,
                "building": building.building_type,
                "groundArea": building.ground_area,
                "area": building.heated_ground_area,
                "gml_id": building.id
            }
            model_list.append(building_dict)
        model_df = pd.DataFrame(model_list)
        model_df = self.add_year_of_construction(model_df, default_year = 1900)
        model_df = self.add_retrofit_status(model_df, default_retrofit = 0)
        return model_df


    def add_retrofit_status(self, model_df: pd.DataFrame, default_retrofit: int = 0):
        """Adds the retrofit status to the model DataFrame."""
        try:
            model_df["retrofit"] = model_df["retrofit"].fillna(default_retrofit).astype("Int64")
        except Exception:
            model_df["retrofit"] = default_retrofit
        return model_df
    
    def add_year_of_construction(self, model_df: pd.DataFrame, default_year: int = 1900):
        """Adds the year of construction to the model DataFrame."""
        try:
            model_df["year"] = model_df["year"].fillna(default_year).astype("Int64")
        except Exception:
            model_df["year"] = default_year
        return model_df

    def save_scenario(self, model_df: pd.DataFrame) -> str:
        """Saves the model DataFrame to a CSV file and returns its path."""
        scenario_path = os.path.join(self.scenario_folder, f'{self.scenario_name}.csv')
        try: 
            model_df.to_csv(scenario_path, index=False, sep=";")
        except OSError:
            cwd_path = os.path.dirname(os.getcwd())
            scenario_path = os.path.join(cwd_path, self.scenario_folder, f'{self.scenario_name}.csv')
            model_df.to_csv(scenario_path, index=False, sep=";")
        return scenario_path

    def process_buildings(self):
        """Processes each building row to handle building parts based on the aggregate_parts flag."""
        buildings = {}
        # Only process buildings that are not building parts
        # Add Building parts to the building
        for _, row in self.df[self.df["isBP"] == False].iterrows():
            bldg_id = row["gml_id"]
            ground_area = row["groundArea"]
            measured_height = row["measuredHeight"]
            storeys_above_ground = row["storeysAboveGround"]
            building_func = row["function"]
            building = Building(id=bldg_id, ground_area=ground_area, building_func=building_func,
                                 measured_height=measured_height, storeys_above_ground=storeys_above_ground)
            
            # Parse building_parts column, assuming it's a stringified list of part IDs
            parts_raw = row.get("building_parts", "[]")
            try:
                part_ids = eval(parts_raw) if parts_raw != "[]" else []
            except Exception:
                part_ids = []
            try:
                for part_id in part_ids:
                    part_row = self.df[self.df["gml_id"] == part_id]
                    part_area = float(part_row["groundArea"].iloc[0])
                    part_measured_height = float(part_row["measuredHeight"].iloc[0])    
                    part_storeys_above_ground = float(part_row["storeysAboveGround"].iloc[0])
                    part = Building(id=part_id, ground_area=part_area, building_func=building_func,
                                    measured_height=part_measured_height, storeys_above_ground=part_storeys_above_ground)
                    part.is_building_part = True
                    building.add_building_part(part)
            except Exception:
                log.info(f"No building parts found for {part_ids, bldg_id}")

            if self.aggregate_parts:
                building.aggregate_area_from_parts()
            else:
                building.propagate_function_to_parts()
            
            self.buildings[bldg_id] = building
        

        for bldg_id, bldg in buildings.items():
            self.df.loc[self.df["gml_id"] == bldg_id, "groundArea"] = bldg.ground_area
        
        return buildings

    def clean_up_scenario(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans up the scenario by removing unnecessary columns and rows."""
        clean_data = df.dropna(subset = ['area', 'year', 'building'])
        # Dop data where area os 0
        clean_data = clean_data[clean_data["area"] != 0]
        clean_data = clean_data[clean_data["building"] != '-']
        clean_data.reset_index(drop = True, inplace = True)
        clean_data.loc[:,"id"]    = clean_data.index
        # Clean the data
        self.clean_data = clean_data
        return clean_data


    def create_scenario(self) -> str:
        """High-level method to execute all steps and create the scenario CSV file."""
        self.load_sheet()
         # Process buildings according to the aggregate_parts flag
        self.process_buildings()
        for building in self.buildings.values():
            calculate_groundArea_from_parts(building)
            parse_building_types_from_parts(building)
            calculate_heated_groundArea_from_parts(building)

       
        # Generate model dataframe
        # Clean up, so it follows the expected format from DistrictGenerator
        model_df = self.generate_model_dataframe()
        clean_data = self.clean_up_scenario(model_df)
        scenario_path = self.save_scenario(clean_data)
        return scenario_path



def calculate_groundArea_from_parts(Building, floor_height: float = 2.8):
    """
    Calculates the floor area of a building, based on its ground area, measured height,
    and/or the number of storeys above ground. Handles building parts by recursively
    summing their floor areas.

    Parameters
    ----------
    Building : Building
        The Building object whose floor area is being calculated.
    floor_height : float, optional
        The assumed floor height (in meters) used as a fallback if storeys_above_ground
        is unavailable. By default, 2.8.

    Returns
    -------
    float
        The calculated floor area for this Building. 
        If it has parts, returns the sum of each part's floor area.
        If no valid numeric data is available, returns 0.0 and logs a warning.

    Notes
    -----
    - If Building.building_parts is non-empty, this function recursively sums up the
      parts' floor areas.
    - If both measured_height and storeys_above_ground are valid (non-NaN), we compute
      the floor area by multiplying ground_area by the ratio of measured_height to 
      storeys_above_ground (rounded to the nearest integer).
    - If only storeys_above_ground is valid, the floor area is ground_area multiplied
      by storeys_above_ground.
    - If only measured_height is valid, floor area is ground_area multiplied by 
      measured_height / floor_height (rounded to the nearest integer).
    - If neither is valid, we log a warning and default the floor_area to 0.0.
    """

    # If this building contains parts, recursively compute the parts' floor areas
    if Building.building_parts:
        Building.floor_area = sum(
            calculate_groundArea_from_parts(part, floor_height) 
            for part in Building.building_parts
        )
        return Building.floor_area
    
    # Check for valid numeric values & None fields 
    valid_height  = (Building.measured_height is not None 
                     and not math.isnan(Building.measured_height))
    valid_storeys = (Building.storeys_above_ground is not None 
                     and not math.isnan(Building.storeys_above_ground))
    
    if valid_height and valid_storeys:
        ratio = round((Building.measured_height / Building.storeys_above_ground), 0)
        Building.floor_area = Building.ground_area * ratio
    elif valid_storeys:
        Building.floor_area = Building.ground_area * Building.storeys_above_ground
    elif valid_height:
        ratio = round((Building.measured_height / floor_height), 0)
        Building.floor_area = Building.ground_area * ratio

    else:
        # Neither height nor storeys are available -> fall back to orignal area
        log.warning(
            f"No valid storey or height data found for building {Building.id}. "
            f"Setting floor_area= {Building.ground_area}"
        )
        Building.floor_area = Building.ground_area

    return Building.floor_area


def calculate_heated_groundArea_from_parts(Building):
    """
    Calculates the heated ground area of a building based on its building parts.

    The heated ground area is calculated by multiplying the floor area by a heating factor
    that varies by building type. For buildings with parts, it recursively calculates
    and sums the heated ground area of all parts.

    Parameters
    ----------
    Building : Building
        The building object to calculate heated ground area for

    Returns
    -------
    float
        The total heated ground area in square meters

    Notes
    -----
    - Uses the HEATED_GROUND_AREA_FACTOR_DICT to look up heating factors by building type
    - For buildings with parts, recursively calculates and sums the parts' heated areas
    - If no heated area factor is set, looks it up based on the building type
    """
    ### There is an error in this function
    if not Building.heated_area_factor:
        Building.heated_area_factor = lookup_heated_area_factor(Building)

    if Building.building_parts:
        Building.heated_ground_area = sum(calculate_heated_groundArea_from_parts(part) for part in Building.building_parts)
        return Building.heated_ground_area
    else:
        Building.heated_ground_area = Building.floor_area * Building.heated_area_factor
        log.info(f"Heated ground area for building {Building.id}: {Building.heated_ground_area} = {Building.floor_area} * {Building.heated_area_factor}")   
        return Building.heated_ground_area


def lookup_heated_area_factor(Building):
    """
    Lookup the heated area factor for a building type.
    """
    if not Building.building_type:
        log.warning(f"No building type found for building {Building.id}. Skipping heated area factor lookup.")
        return None
    Building.heated_area_factor = HEATED_GROUND_AREA_FACTOR_DICT.get(Building.building_type, 1)
    return Building.heated_area_factor

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


def parse_building_types_from_parts(Building, 
                                    default_building_type: str = "SFH",
                                    total_area: Optional[float] = None):
    """
    Parse and assign building types for a building and its parts.

    Parameters
    ----------
    Building : Building
        The Building object to process.
    default_building_type : str, optional
        Default building type if none can be determined, by default "SFH".
    total_area : Optional[float], optional
        The total floor area to use for type determination, by default None.
        If None, this function will use Building.floor_area. 
        When the building has parts, we pass the parent's total area 
        so that all parts consider the same total area.

    Returns
    -------
    str
        The determined building type in DistrictGenerator naming scheme.
    """
    total_area_for_building = total_area if total_area is not None else Building.floor_area

    if Building.building_parts:
        # Recursively parse building types for each part, 
        # passing the parent's total_area_for_building
        type_list = []
        for part in Building.building_parts:
            subtype = parse_building_types_from_parts(
                part, 
                default_building_type=default_building_type, 
                total_area=total_area_for_building
            )
            type_list.append(subtype)

        if len(set(type_list)) > 1:
            log.warning(
                f"Warning: Multiple building types found in building parts of '{Building.id}': "
                f"{type_list}. Returning majority type."
            )
            Building.building_type = Counter(type_list).most_common(1)[0][0]
        else:
            Building.building_type = type_list[0]

        return Building.building_type

    else:
        building_code = normalize_function_code(Building.building_func)
        building_type_candidates = BUILDING_FUNCTIONS.get(building_code, [default_building_type])
        if building_type_candidates:
            Building.building_type = str(
                get_building_subtype(
                    candidates=building_type_candidates,
                    floorArea=total_area_for_building, 
                    default_building_type=default_building_type
                )
            )
            return Building.building_type
        else:
            Building.building_type = str(building_type_candidates)
            return Building.building_type




if __name__ == '__main__':
    file_path = r'C:\Users\felix\Programmieren\DVG\TECDEM\test_detailed_dataset.csv'  
    scenario_name = "MyScenario"

    # Create a Scenario instance with aggregate_parts flag
    my_scenario = Scenario(sheet_file=file_path, scenario_name=scenario_name, aggregate_parts=True)
    scenario_csv_path = my_scenario.create_scenario()

    print(f"Scenario saved at: {scenario_csv_path}")
