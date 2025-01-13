# Class, that takes care of data handling 
# First Feature, take a GML dataset, create a detailed and low level simulation sheet
# Detailed dataset from citygml.dataset.py
# Low level simulation sheet from sim.sheet_generation.py
import os
import pandas as pd
import json

from citygml.dataset import Dataset
from citygml.core.input.citygmlInput import load_buildings_from_xml_file
from citygml.tools.datasetToDataFrame import getDataFrame
from citygml.tools.partywall import get_party_walls
from citygml.tools.geometry_analysis import get_building_geometry_analysis
from sim.scenario_generation import create_scenario
from sim.scenario import Scenario


class DataHandler:
    """
    Loads one or multiple GML files into a Dataset,
    and can directly create a scenario from that Dataset.
    """

    def __init__(self, path_to_gml_file, scenario_name: str, scenario_folder: str = "data/scenario_sheets"):
        """
        Parameters
        ----------
        path_to_gml_file : str or list[str]
            Path(s) to the GML file(s).
        scenario_name : str
            A name describing this scenario.
        scenario_folder : str, optional
            Where to save scenario output.
        """
        self.path_to_gml_file = path_to_gml_file
        self.scenario_name = scenario_name
        self.scenario_folder = scenario_folder
        self.gml_dataset = Dataset(name=scenario_name)

    def load_dataset(self):
        """
        Loads GML file(s) into self.gml_dataset.
        """
        if isinstance(self.path_to_gml_file, list):
            for file_path in self.path_to_gml_file:
                load_buildings_from_xml_file(self.gml_dataset, file_path)
        else:
            load_buildings_from_xml_file(self.gml_dataset, self.path_to_gml_file)

        # Optionally attach party walls if relevant
        self.gml_dataset.party_walls = get_party_walls(self.gml_dataset)

    def save_geometry_analysis(self):
        """
        Runs geometry analysis and saves the results to a JSON file.
        """
        geometry_analysis = get_building_geometry_analysis(self.gml_dataset)
        out_file = f"{self.scenario_name}_geometry_analysis.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(geometry_analysis, f)
        print(f"Geometry analysis saved to {out_file}")
    
    def save_dataset(self):
        df = getDataFrame(self.gml_dataset, includeFreeWalls=True, includeBP=True)
        df.to_csv(f"{self.scenario_name}_detailed_dataset.csv", index=False)


    def create_scenario(
        self,
        default_building_type="SFH",
        aggregate_parts=True
    ) -> str:
        """
        Creates a scenario either directly from the loaded Dataset
        or from a passed-in DataFrame.

        Parameters
        ----------
        default_building_type : str, optional
            Fallback building type.
        aggregate_parts : bool, optional
            Whether to aggregate building parts into parent building.
        from_dataframe : pd.DataFrame, optional
            If provided, the scenario will be created from this DataFrame
            instead of from self.gml_dataset.

        Returns
        -------
        str
            Path to the created scenario file.
        """
        #if from_dataframe is not None:
        #    # We have a DataFrame; create a scenario from that
        scenario = Scenario(
            sheet_file=os.path.join(f"{self.scenario_name}_detailed_dataset.csv"),
            scenario_name=self.scenario_name,
            scenario_folder=self.scenario_folder,
            default_building_type=default_building_type,
            aggregate_parts=aggregate_parts, 
        )
        # TODO Implementation of a scenario from dataset version:
            # We use the citygml Dataset
        #    scenario = Scenario(
        #        scenario_name=self.scenario_name,
        #        scenario_folder=self.scenario_folder,
        #        default_building_type=default_building_type,
        #        aggregate_parts=aggregate_parts,
        #        dataset=self.gml_dataset,  # <-- Dataset mode
        #        df=None
        #    )
        scenario_csv_path = scenario.create_scenario()
        print(f"Scenario created: {scenario_csv_path}")
        return scenario_csv_path

    def get_dataset(self) -> Dataset:
        """
        Returns the loaded Dataset object.
        """
        return self.gml_dataset
    
    def validate_gml_file(self):
        pass


    def validate_simulation_sheet(self):
        pass 


if __name__ == "__main__":
    gml_files = [os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_384_5820_1_BE.gml")]
    #"data/examples/gml_data/Block020023.gml")]
                              #
    #             os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_384_5821_1_BE.gml"),
    #             os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_385_5820_1_BE.gml"),
    #             os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_385_5821_1_BE.gml")]
    datahandler = DataHandler(gml_files , "test")
    #datahandler.load_dataset()
    #datahandler.save_dataset()
    #datahandler.save_geometry_analysis()
    datahandler.create_scenario()
    datahandler.validate_gml_file()
    datahandler.validate_simulation_sheet()

