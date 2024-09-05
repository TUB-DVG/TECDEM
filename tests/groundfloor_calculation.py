import unittest
import os
import sys

# Ensure the correct path to the virtual environment is added
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'venv', 'Lib', 'site-packages')
sys.path.append(venv_path)



sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")



try:
    import citygml.file_handling as file_handling
except ImportError as e:
    print(f"Error importing citygml.file_handling: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

class TestGroundFloorArea(unittest.TestCase):
    def test_ground_floor_area(self):
        file_path = 'data/examples/gml_data/FZKHouseLoD3-ADE-results.gml'
         # CityGML file has floo area for both ground and first floor
        # <energy:floorArea>
        #     <energy:FloorArea>
        #       <energy:type>grossFloorArea</energy:type>
        #       <energy:value uom="m2">240</energy:value>
        #     </energy:FloorArea>
        #   </energy:floorArea>
        expected_area = 240 / 2 

        result = file_handling.get_floor_area(file_path)

        self.assertEqual(result[0][1], expected_area)

if __name__ == '__main__':
    unittest.main()
