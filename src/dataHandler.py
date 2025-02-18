# Class, that takes care of data handling 
# First Feature, take a GML dataset, create a detailed and low level simulation sheet
# Detailed dataset from citygml.dataset.py
# Low level simulation sheet from sim.sheet_generation.py
import os
import pandas as pd
import json
import geopandas as gpd


from citygml.dataset import Dataset
from citygml.core.input.citygmlInput import load_buildings_from_xml_file
from citygml.tools.datasetToDataFrame import getDataFrame
from citygml.tools.partywall import get_party_walls
from citygml.tools.geometry_analysis import get_building_geometry_analysis
from citygml.tools.cityATB import search_dataset

from sim.scenario_generation import create_scenario
from sim.scenario import Scenario
from spatial.block import Block


class DataHandler:
    """
    Loads one or multiple GML files into a Dataset,
    and can directly create a scenario from that Dataset.
    """

    def __init__(self, path_to_gml_file, scenario_name: str,
                 scenario_folder: str = "data/scenario_sheets", border_coordinates: list[float] = None):
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
        self.reduced_dataset = None
        self.border_coordinates = border_coordinates

    def load_dataset(self):
        """
        Loads GML file(s) into self.gml_dataset.

        This method loads one or multiple CityGML files into the dataset object.
        If border coordinates are specified, only buildings within those coordinates
        will be loaded. Party walls between adjacent buildings are also detected
        and attached to the dataset.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        The loaded data is stored in self.gml_dataset. Party walls are stored in
        self.gml_dataset.party_walls.
        """
        # TODO: Add loading of dataset with border coordinates
        if isinstance(self.path_to_gml_file, list):
            for file_path in self.path_to_gml_file:
                load_buildings_from_xml_file(self.gml_dataset, file_path)
        else:
            load_buildings_from_xml_file(self.gml_dataset, self.path_to_gml_file)

        self.gml_dataset.party_walls = get_party_walls(self.gml_dataset)

    def save_geometry_analysis(self):
        """
        Runs geometry analysis and saves the results to a JSON file.
        """
        if self.reduced_dataset is not None:
            geometry_analysis = get_building_geometry_analysis(self.reduced_dataset)
        else:
            geometry_analysis = get_building_geometry_analysis(self.gml_dataset)
        out_file = f"{self.scenario_name}_geometry_analysis.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(geometry_analysis, f, indent=4)
        print(f"Geometry analysis saved to {out_file}")
    
    def save_dataset(self):
        if self.reduced_dataset is not None:
            df = getDataFrame(self.reduced_dataset, includeFreeWalls=True, includeBP=True)
        else:
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
        # TODO: Implementation of a scenario from dataset version:
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
    
    def merge_block(self, path_to_block_data:str, path_to_year_range_data:str):
        block_data = gpd.read_file(path_to_block_data)
        # TODO: Figure out how to cacluate this quicker
        for index, row in block_data.iterrows():
            block = Block(id = row['blknr'], geometry=row['geometry'],
                          area=row['area'], inhabitants=row['ewk'])
            block.merge_block_data(path_to_year_range_data, self.gml_dataset)


    def get_dataset(self) -> Dataset:
        """
        Returns the loaded Dataset object.
        """
        return self.gml_dataset


    def select_subset_by_coordinates(self, coordinates: list[float]):
        """
        Selects a subset of the dataset by coordinates.
        """
        self.reduced_dataset = search_dataset(self.gml_dataset, coordinates)
        return self.reduced_dataset
    
    def validate_gml_file(self):
        pass


    def validate_simulation_sheet(self):
        pass 


if __name__ == "__main__":
    gml_files = [os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_384_5820_1_BE.gml"),
                 os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_384_5821_1_BE.gml"),
                 os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_385_5820_1_BE.gml"),
                 os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/gml_data/LoD2_33_385_5821_1_BE.gml")]
    border_coordinates = gpd.read_file(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/examples/Mierendorff_shape/Mierendorff_shape.dbf")).to_crs("EPSG:25833").iloc[0].geometry.exterior.coords
    datahandler = DataHandler(gml_files, scenario_name="Mierendorff")
    datahandler.load_dataset()
    #reduced_dataset = datahandler.select_subset_by_coordinates(border_coordinates)
    datahandler.merge_block(path_to_block_data=r"C:\Users\felix\Programmieren\DVG\TECDEM\data\block_data\00_block_shape.shp",
                            path_to_year_range_data=r"C:\Users\felix\Programmieren\DVG\TECDEM\data\berlin\02_Gebäudealter.csv")
    datahandler.save_dataset()
    datahandler.save_geometry_analysis()
    datahandler.create_scenario()
    datahandler.validate_gml_file()
    datahandler.validate_simulation_sheet()

