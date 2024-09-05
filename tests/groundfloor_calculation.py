import unittest
import os
import sys

# Ensure the correct path to the virtual environment is added
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'venv', 'Lib', 'site-packages')
sys.path.append(venv_path)

try:
    import shapely
except ImportError as e:
    print(f"Error importing shapely: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
try:
    import citygml.file_handling
except ImportError as e:
    print(f"Error importing citygml.file_handling: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

class TestGroundFloorArea(unittest.TestCase):
    def test_ground_floor_area(self):
        file_path = 'data/examples/gml_data/FZKHouseLoD3-ADE-results.gml'
        expected_area = 1000
        # Ensure get_ground_floor_area is imported or defined
        from citygml.file_handling import get_ground_floor_area
        result = get_ground_floor_area(file_path)
        self.assertEqual(result, expected_area)

if __name__ == '__main__':
    unittest.main()
