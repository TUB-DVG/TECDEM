# Class, that takes care of data handling 
# First Feature, take a GML dataset, create a detailed and low level simulation sheet
# Detailed dataset from citygml.dataset.py
# Low level simulation sheet from sim.sheet_generation.py

from citygml.dataset import Dataset
from citygml.core.input.citygmlInput import load_buildings_from_xml_file
from citygml.tools.datasetToDataFrame import getDataFrame
from sim.scenario_generation import create_scenario

import os

class DataHandler:
    def __init__(self, path_to_gml_file:str, scenario_name:str):
        self.gml_dataset = Dataset()
        self.path_to_gml_file = path_to_gml_file
        self.scenario_name = scenario_name

    def create_detailed_dataset(self):
        if isinstance(self.path_to_gml_file, list):
            for file in self.path_to_gml_file:
                load_buildings_from_xml_file(self.gml_dataset, file)
        else:
            load_buildings_from_xml_file(self.gml_dataset, self.path_to_gml_file)
        # Include free walls and building parts
        df = getDataFrame(self.gml_dataset, includeFreeWalls=True, includeBP=True)
        df.to_csv(f"{self.scenario_name}_detailed_dataset.csv", index=False)

    def create_low_level_simulation_sheet(self):
        sheet_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  f"{self.scenario_name}_detailed_dataset.csv")
        create_scenario(sheet_file=sheet_file,
                        scenario_name=self.scenario_name,
                        default_building_type="SFH",
                        scenario_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scenario_sheets"))


    def validate_gml_file(self):
        pass

    def validate_simulation_sheet(self):
        pass


if __name__ == "__main__":
    gml_files = [os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_384_5820_1_BE.gml"),
                 os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_384_5821_1_BE.gml"),
                 os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_385_5820_1_BE.gml"),
                 os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_385_5821_1_BE.gml")]
    datahandler = DataHandler(gml_files , "test")
    datahandler.create_detailed_dataset()
    datahandler.create_low_level_simulation_sheet()
    datahandler.validate_gml_file()
    datahandler.validate_simulation_sheet()

