import os
import logging as log
from typing import Optional
from .
from ...citygml.dataset import Dataset
from src.citygml.core.object.building import Building as CityGMLBuilding


# TODO: Need to adapt the simulation class, so it works with both dataframes and datasets
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


def normalize_function_code(func_code: Optional[str]) -> Optional[int]:
    """
    Example normalization of a CityGML function code:
      - '31001_2310' -> 2310
      - '2310'       -> 2310
      - None         -> None
    Adjust to your own logic.
    """
    if not func_code:
        return None

    # If there's an underscore, split on that
    if "_" in func_code:
        try:
            return int(float(func_code.split("_")[1]))
        except ValueError:
            return None

    # Otherwise, parse the whole string as an int
    try:
        return int(float(func_code))
    except ValueError:
        return None

def get_building_subtype(candidates, ground_area, default_building_type: str = "SFH"):
    """
    Example logic to pick a final building function from candidates 
    based on ground_area (like your older code).
    """
    # If we see typical residential codes, do some area-based classification
    if any(t in ["TH", "SFH", "MFH", "AB"] for t in candidates):
        if ground_area <= 140:
            return "TH"
        elif 140 < ground_area <= 280:
            return "SFH"
        elif 280 < ground_area <= 800:
            return "MFH"
        else:
            return "AB"

    # If there's only one candidate
    if len(candidates) == 1:
        return candidates[0]

    # Default fallback
    return candidates[0] if candidates else default_building_type


class Scenario:
    """
    Creates a simulation scenario directly from a citygml.dataset.Dataset object,
    without intermediate CSV reading.
    """

    def __init__(
        self,
        dataset: Dataset,
        scenario_name: str,
        default_building_type: str = "SFH",
        scenario_folder: str = "",
        aggregate_parts: bool = True,
    ):
        """
        Parameters
        ----------
        dataset : Dataset
            The loaded citygml.dataset.Dataset object containing buildings.
        scenario_name : str
            Name for the scenario.
        default_building_type : str, optional
            Fallback building type if function code is missing or unknown.
        scenario_folder : str, optional
            Folder path for saving scenario output (if needed).
        aggregate_parts : bool, optional
            If True, merges building parts into the parent building’s area. 
            If False, only propagates function codes downward, etc.
        """
        self.dataset = dataset
        self.scenario_name = scenario_name
        self.default_building_type = default_building_type
        self.scenario_folder = scenario_folder
        self.aggregate_parts = aggregate_parts
        self.results = []  # Example container for scenario results

    def process_buildings(self):
        """
        Main processing step, iterates over buildings in the dataset
        and optionally aggregates building parts, assigns function codes, etc.
        """
        for b_id, bldg in self.dataset.buildings.items():
            # bldg is a citygml.core.object.building.Building
            # We'll wrap it in our own aggregator or process it directly.
            processed_bldg = self._process_single_building(bldg)
            self.results.append(processed_bldg)

    def _process_single_building(self, bldg: CityGMLBuilding) -> dict:
        """
        Example method that:
        1) Normalizes or reads function code from the building.
        2) Computes or reads ground area.
        3) Aggregates building parts if required.
        4) Returns a dictionary with all relevant scenario fields.
        """
        # --- (1) Normalizing function code ---
        # citygml's Building might store function in bldg.function or something similar:
        if hasattr(bldg, "function"):
            raw_func_code = bldg.function  # e.g. "31001_2310"
        else:
            raw_func_code = None

        func_code = normalize_function_code(raw_func_code)
        candidates = BUILDING_FUNCTIONS.get(func_code, [self.default_building_type])

        # --- (2) Example ground area computation ---
        # You might have a custom geometry method for computing ground area:
        # or it might be precomputed / stored in bldg.
        ground_area = self._compute_ground_area(bldg)

        # --- (3) Building Parts aggregation (optional) ---
        # citygml Building might store parts in bldg.buildingParts 
        # or you might find them by cross-ref in the dataset.
        total_area = ground_area
        part_areas = []
        if self.aggregate_parts and hasattr(bldg, "buildingParts"):
            for part_id in bldg.buildingParts:
                part_obj = self.dataset.buildings.get(part_id, None)
                if part_obj:
                    part_area = self._compute_ground_area(part_obj)
                    part_areas.append(part_area)
                    total_area += part_area

        # Decide final building function subtype
        final_function = get_building_subtype(candidates, total_area, self.default_building_type)

        # Return a minimal dictionary describing the building scenario
        return {
            "gml_id": bldg.gml_id,
            "ground_area": total_area,
            "function": final_function,
            "part_areas": part_areas,
        }

    def _compute_ground_area(self, bldg: CityGMLBuilding) -> float:
        """
        Example placeholder for computing ground area from geometry or stored attribute.
        """
        # If your Building object already has an attribute for area:
        if hasattr(bldg, "groundArea"):
            return bldg.groundArea if bldg.groundArea else 0.0

        # Otherwise, do some geometry-based calculation:
        # e.g. polygon area from the building footprint, etc.
        # Pseudocode:
        #   polygons = bldg.lod2Solid or bldg.lod1Solid ...
        #   compute area...
        return 0.0

    def save_scenario(self) -> str:
        """
        Example method if you still want to save scenario output to a CSV or JSON.
        """
        if not self.results:
            log.warning("No scenario results to save. Did you call process_buildings()?")

        # Convert list of dicts to CSV or JSON
        output_path = os.path.join(
            self.scenario_folder, f"{self.scenario_name}.csv"
        )

        # Minimal CSV writing with standard library (if you prefer no Pandas):
        import csv
        fieldnames = ["gml_id", "ground_area", "function", "part_areas"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for row in self.results:
                writer.writerow(row)

        return output_path

    def run_scenario(self):
        """
        High-level orchestration: process buildings and then optionally save scenario.
        Returns the path to the scenario file or some result object.
        """
        self.process_buildings()
        return self.save_scenario()


if __name__ == "__main__":
    # Example usage:
    from dataHandler import DataHandler  # from the code above

    # 1) Load GML data into a Dataset
    gml_path = "path/to/some/file.gml"
    datahandler = DataHandler(gml_path, "my_cool_scenario")
    datahandler.load_dataset()

    # 2) Create and run scenario
    scenario = Scenario(
        dataset=datahandler.get_dataset(),
        scenario_name="my_cool_scenario",
        scenario_folder="some/output/folder",
        aggregate_parts=True,
    )
    scenario_csv_path = scenario.run_scenario()
    print(f"Scenario results saved at: {scenario_csv_path}")
