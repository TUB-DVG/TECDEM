from __future__ import annotations
from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from src.citygml.dataset import Dataset
    from src.citygml.core.obejct.abstractBuilding import AbstractBuilding

import numpy as np
from citygml.tools.partywall import get_party_walls
from citygml.logger import logger

def get_building_geometry_analysis(dataset: Dataset) -> dict:
    """Analyzes building geometries to get areas per arbitrary direction and connected areas
    
    Parameters
    ----------
    dataset : Dataset
        CityDPC dataset containing the buildings to analyze
        
    Returns
    -------
    dict
        Dictionary containing, for each building and orientation:
        - surface_id  
        - total_wall_area
        - connected_wall_area
        - free_wall_area
    """
    results = {}
    for building in dataset.get_building_list():
        building_id = building.gml_id
        if building_id not in results:
            results[building_id] = {}
            results[building_id]["gml_id"] = building.gml_id
        wall_surfaces = building.get_surfaces(["WallSurface"])
        if not wall_surfaces:
            logger.info(f"No wall surfaces found for building {building_id}")
            continue
        for wall_surface in wall_surfaces:
            direction = wall_surface.get_gml_orientation()
            results[building_id][direction] = {
                "surface_id": wall_surface.polygon_id,
                "total_wall_area": wall_surface.surface_area,
                "connected_wall_area": 0,
                "free_wall_area": wall_surface.surface_area  # Initially all area is free
            }
        

    if dataset.party_walls is None:
        dataset.party_walls = get_party_walls(dataset)
    if dataset.party_walls is None:
        logger.info("No party walls found")
        return results
    else:
        for party_wall in dataset.party_walls:
            building_id = party_wall[0]
            building_id_2 = party_wall[2]
            
            try:
                building = dataset.get_building_by_id(building_id)
            except KeyError:
                # In cases of building parts, the building has the format 'DEBE3D04YY50000FXx/DEBE3DxwQ0k50GVY'
                building_id = building_id.split("/")[0]
                building = dataset.get_building_by_id(building_id)

            for wall_surface in building.get_surfaces(["WallSurface"]):
                if wall_surface.polygon_id == party_wall[1]:
                    direction = wall_surface.get_gml_orientation()
                    connected_area = party_wall[4]
                    results[building_id][direction]["connected_wall_area"] += connected_area
                    results[building_id][direction]["free_wall_area"] = (
                        results[building_id][direction]["total_wall_area"] - 
                        results[building_id][direction]["connected_wall_area"]
                    )
            
            try:
                building_2 = dataset.get_building_by_id(building_id_2)
            except KeyError:
                building_id_2 = building_id_2.split("/")[0]
                building_2 = dataset.get_building_by_id(building_id_2)
            for wall_surface in building_2.get_surfaces(["WallSurface"]):
                if wall_surface.polygon_id == party_wall[3]:
                    direction = wall_surface.get_gml_orientation()
                    connected_area = party_wall[4]
                    results[building_id_2][direction]["connected_wall_area"] += connected_area
                    results[building_id_2][direction]["free_wall_area"] = (
                        results[building_id_2][direction]["total_wall_area"] - 
                        results[building_id_2][direction]["connected_wall_area"]
                    )
    
    return results


