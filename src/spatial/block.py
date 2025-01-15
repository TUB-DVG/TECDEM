from __future__ import annotations
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from citygml.dataset import Dataset
    from citygml.core.object.abstractBuilding import AbstractBuilding
    from citygml.core.object.geometry import Geometry

import numpy as np
from shapely import wkt
import pandas as pd
from citygml.tools.cityATB import check_if_building_in_coordinates
from citygml.geometric_strings import get_2dPosList_from_str



class Block:
    """
    A class representing a city block containing buildings.

    This class manages information about a city block including its geometry,
    area, inhabitants, and the buildings contained within it.

    Parameters
    ----------
    id : str or int
        Unique identifier for the block
    geometry : shapely.geometry
        Geometric shape/boundary of the block
    area : float
        Area of the block in square meters
    inhabitants : int
        Number of inhabitants in the block

    Attributes
    ----------
    id : str or int
        Unique identifier for the block
    geometry : shapely.geometry
        Geometric shape/boundary of the block 
    area : float
        Area of the block in square meters
    inhabitants : int
        Number of inhabitants in the block
    date : str or None
        Date associated with the block data
    block_type : str or None
        Type/classification of the block
    list_of_buildings : list or None
        List of building identifiers in the block
    list_of_building_ages : list or None
        List of building construction years
    average_building_age : float or None
        Average construction year of buildings
    buildings : list
        List of building objects contained in the block
    """
    def __init__(self, id, geometry,
                 area, inhabitants):
        self.id = id
        self.geometry = geometry
        self.area = area
        self.inhabitants = inhabitants
        self.date = None
        self.block_type = None
        self.list_of_buildings = None
        self.list_of_building_ages = None
        self.average_building_age = None
        self.buildings = []


    
    def calculate_average_building_age(self, path_to_year_range_data:str):
        """
        Calculate the average building age for this block from year range data.

        Parameters
        ----------
        path_to_year_range_data : str
            Path to CSV file containing building age ranges by block number.
            Expected columns: 'blknr', 'ueberw_dek'

        Returns
        -------
        None
            Sets self.average_building_age based on the calculated average year.

        Notes
        -----
        Attempts to match block ID as both string and int to handle different formats.
        Uses average_year_from_range() to calculate final age value.
        """
        # TODO: Add error handling for missing data
        # TODO: Add functionality to get list of potential building ages
        year_range_data = pd.read_csv(path_to_year_range_data, na_values=None)
        matching_rows = year_range_data[year_range_data['blknr'] == self.id]

        if matching_rows.empty:
            try:
                matching_rows = year_range_data[year_range_data['blknr'] == int(self.id)]
            except ValueError:
                pass

        if matching_rows.empty:
            self.average_building_age = ""
            return

        year_range_data_block = matching_rows['ueberw_dek'].iloc[0]
        self.average_building_age = self.average_year_from_range(year_range_data_block)

    
    def add_age_to_buildings(self):
        """Adds the block's average building age to all buildings in the block.

        Sets the yearOfConstruction attribute of each building in self.buildings
        to match the block's average_building_age value.

        Parameters
        ----------
        None

        Returns
        -------
        None
            Modifies the yearOfConstruction attribute of buildings in place.
        """
        
        for building in self.buildings:
            building.yearOfConstruction = self.average_building_age


    def get_buildings(self, dataset:Dataset):
        """Identifies and stores buildings that fall within this block's geometry.

        Filters buildings from the dataset by checking if they fall within the 
        block's 2D coordinates. Matching buildings are added to self.buildings.

        Parameters
        ----------
        dataset : Dataset
            CityGML dataset containing building objects to filter

        Returns
        -------
        None
            Modifies self.buildings list in place by appending matching buildings.
            Logs number of buildings found.
        """
        block_coordinates_2D = list(self.geometry.exterior.coords)
        for building in dataset.get_building_list():
            if check_if_building_in_coordinates(building, block_coordinates_2D):
                self.buildings.append(building)
        logging.info(f"Found {len(self.buildings)} buildings in block {self.id}")
            


    def average_year_from_range(self, year_range):
        """Calculate the average year from a year range string or value.

        This function extracts start and end years from a range string, calculates 
        the average, and handles special cases like "gemischte Baualtersklasse".
        The result is stored in self.average_building_age.

        Parameters
        ----------
        year_range : str or float
            The year range to process. Can be:
            - A range like "1900-1920"
            - Special strings like "gemischte Baualtersklasse", "bis 1900", "NaN"
            - A float or empty string
            - A single year as int/float

        Returns
        -------
        int or None or str
            The calculated average year as integer, None for invalid/mixed ranges,
            or empty string for invalid float inputs
        """
        if isinstance(year_range, str):
            if '-' in year_range:
                start_year, end_year = year_range.split('-')
                self.average_building_age = (int(start_year) + int(end_year)) // 2
                return self.average_building_age
            elif year_range == "gemischte Baualtersklasse":
                self.average_building_age = ""
                return "" 
            elif year_range == "bis 1900": 
                self.average_building_age = 1900
                return 1900
            elif year_range == "NaN":
                self.average_building_age = None
                return "" 
        elif isinstance(year_range, float):
            if year_range == "":
                self.average_building_age = ""
                return ""
            else:
                return ""
        elif year_range is None:
            return ""
        else:
            return ""
        
    def merge_block_data(self,
                         path_to_year_range_data: str, dataset: Dataset):
        """
        High level function to merge block data with buildings.
        
        This function:
        1. Loads block data from shapefile
        2. Extracts buildings for this block from dataset
        3. Calculates average building age from year range data
        4. Assigns the age to all buildings in the block
        
        Parameters
        ----------
        path_to_year_range_data : str
            Path to CSV file containing building year ranges
        dataset : Dataset
            CityGML dataset containing building information
        """
        # Get buildings for this block
        self.get_buildings(dataset)
        
        if self.buildings:
            # Calculate average age from year range data
            self.calculate_average_building_age(path_to_year_range_data)
            
            # Assign age to all buildings
            self.add_age_to_buildings()
        else:
            logging.info(f"No buildings found for block {self.id}. Skipping age calculation.")
