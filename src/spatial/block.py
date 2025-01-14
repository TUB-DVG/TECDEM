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
        
        year_range_data = pd.read_csv(path_to_year_range_data, na_values=None)
        year_range_data_block = year_range_data[year_range_data['blknr'] == self.id]['ueberw_dek']
        if not year_range_data_block.empty:
            self.average_building_age = self.average_year_from_range(year_range_data_block)
        else:
            year_range_data_block = year_range_data[year_range_data['blknr'] == int(self.id)]['ueberw_dek']
            self.average_building_age = self.average_year_from_range(year_range_data_block)

    


    def get_buildings(self, dataset:Dataset):
        """
        Get the buildings of the block from the dataset
        -> Filter the datset by coordinates 
        -> Get the ids that fit
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
                self.average_building_age = None
                return None 
            elif year_range == "bis 1900": 
                self.average_building_age = 1900
                return 1900
            elif year_range == "NaN":
                self.average_building_age = None
                return None 
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
