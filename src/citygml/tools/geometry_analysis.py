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
        for wall_surface in building.get_surfaces(["WallSurface"]):
            direction = wall_surface.get_gml_orientation()
            results[building_id][direction] = {
                "total_wall_area": 0,
                "connected_wall_area": 0,
                "free_wall_area": 0
            }
            results[building_id][direction]["total_wall_area"] += wall_surface.surface_area

    if dataset.party_walls is None:
        get_party_walls(dataset)
    if dataset.party_walls is None:
        logger.info("No party walls found")
    else:
        for party_wall in dataset.party_walls:
            building_id = party_wall[0]
            # building_id_2 = party_wall[2]  # Check if this is needed
            building = dataset.get_building_by_id(building_id)
            if building_id not in results:
                results[building_id] = {}
            
            for wall_surface in building.get_surfaces(["WallSurface"]):
                direction = wall_surface.get_gml_orientation()
                results[building_id][direction]["total_wall_area"] += wall_surface.surface_area
                if wall_surface.polygon_id == party_wall[1]:
                    results[building_id][direction]["connected_wall_area"] += party_wall[4]
                    results[building_id][direction]["free_wall_area"] += (
                        wall_surface.surface_area - party_wall[4]
                )
    
    return results


def _analyze_building_geometry(building: AbstractBuilding, party_walls: list) -> dict:
    """Analyzes geometry of a single building/building part
    
    Parameters
    ----------
    building : AbstractBuilding
        Building or BuildingPart to analyze
    party_walls : list
        List of detected party walls in the dataset
        
    Returns
    -------
    dict
        Dictionary containing:
        - Areas per direction (N,S,E,W)
        - Connected areas per direction (N,S,E,W)
        - Connected areas with other buildings
        - Total wall area
    """
    
    # Initialize results
    results = {
        "direction_areas": {
            "N": 0.0, # North facing walls
            "S": 0.0, # South facing walls
            "E": 0.0, # East facing walls
            "W": 0.0  # West facing walls
        },
        "connected_direction_areas": {
            "N": 0.0, # North facing connected walls
            "S": 0.0, # South facing connected walls
            "E": 0.0, # East facing connected walls
            "W": 0.0  # West facing connected walls
        },
        "connected_areas": {},  # Areas connected to other buildings
        "total_wall_area": 0.0
    }
    
    # Get all wall surfaces
    wall_surfaces = building.get_surfaces(["WallSurface"])
    
    for surface in wall_surfaces:
        # Get surface area
        area = surface.surface_area
        results["total_wall_area"] += area
        
        # Determine direction based on normal vector
        direction = surface.get_gml_orientation()
        # Add key if it doesn't exist yet
        if direction not in results["direction_areas"]:
            results["direction_areas"][direction] = 0
        results["direction_areas"][direction] += area
        
    # Calculate connected areas from party walls
    building_id = (building.gml_id if not building.is_building_part 
                  else f"{building.parent_gml_id}/{building.gml_id}")
    
    for party_wall in party_walls:
        breakpoint()
        if party_wall[0] == building_id:
            # direction über party_wall[0]
            # Alle Gebäude Wände rausfinden 
            # Dann für jeden Wand rausfinden, ob diese eine Nachbarwand hat 

            # This building is building_0 in party wall
            other_building = party_wall[2]
            area = party_wall[4]
            if isinstance(party_wall, list):
                for wall in party_wall:
                    direction = wall.get_gml_orientation()  # Assuming normal vector is at index 5
                    results["connected_areas"][other_building] = results["connected_areas"].get(other_building, 0) + area
                    if direction not in results["connected_direction_areas"]:
                        results["connected_direction_areas"][direction] = 0
                    results["connected_direction_areas"][direction] += area
            else:
                direction = party_wall.get_gml_orientation()  # Assuming normal vector is at index 5
                results["connected_areas"][other_building] = results["connected_areas"].get(other_building, 0) + area
            if direction not in results["connected_direction_areas"]:
                results["connected_direction_areas"][direction] = 0
            results["connected_direction_areas"][direction] += area
        elif party_wall[2] == building_id:
            # This building is building_1 in party wall
            other_building = party_wall[0]
            area = party_wall[4]
            # Invert normal vector direction since this building is building_1
            direction = party_wall.get_gml_orientation()  # Assuming normal vector is at index 5
            results["connected_areas"][other_building] = results["connected_areas"].get(other_building, 0) + area
            if direction not in results["connected_direction_areas"]:
                results["connected_direction_areas"][direction] = 0
            results["connected_direction_areas"][direction] += area
        else:
            continue
            
    return results

def _get_wall_direction(normal_vector: np.ndarray) -> str:
    """Determines the main direction of a wall based on its normal vector
    
    Parameters
    ----------
    normal_vector : np.ndarray
        Unit normal vector of the wall surface
        
    Returns
    -------
    str
        Main direction ('N', 'S', 'E' or 'W')
    """
    # Get x and y components
    x, y = normal_vector[0], normal_vector[1]
    
    # Determine main direction based on largest component
    try:
        if abs(x) > abs(y):
            return 'E' if x > 0 else 'W'
        else:
            return 'N' if y > 0 else 'S' 
    except:
        breakpoint()
        return "unknown"