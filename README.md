# TECDEM - Tool for Efficient CityGML District Energy Modelling

This is the Tool for Efficient CityGML District Energy Modelling (TECDEM). It is a Python-based tool that utilizes CityGML, the [EnergyADE](https://www.citygmlwiki.org/images/4/41/KIT-UML-Diagramme-Profil.pdf), and the [Districtgenerator](https://github.com/RWTH-EBC/districtgenerator) (also known as Quartiersgenerator) to easily parameterize districts based on CityGML files, extract and enrich data for simulation, and visualize the results.

TECDEM is a tool that can be used for quickly exraction geometry and further information for simulation of districts. We consider districts and tools for their modeling and simulation, as districts provide an important scale in the energy transition. They offer more flexibility than a single building and hence can be considered the smallest cell of energy transition.

## Project Status

TECDEM is currently under heavy development. An overview of the current functionalities can be found in the [experiments](experiments) folder. Currently, surfaces can be extracted from both CityGML and CityJSON. 

## Installation

To install TECDEM, follow these steps:

1. Clone this repository
2. Run: `pip install -r requirements.txt`
3. Navigate to the `src` folder and clone this branch of the [Districtgenerator](https://github.com/c0nb4/districtgenerator)

For a complete list of dependencies, please refer to the `requirements.txt` file in the repository.

## Usage

Please refer to the experiments in the repository for examples of how to use TECDEM. Generally, usage is suggested as follows:

1. Load the CityGML file into the tool
2. Extract the information you need
3. Save detailed information and geometry 
4. Create s low level simulation scenario
5. Enrich the archetype data from the simulation with the detailed geometry and information extracted from the input data

## Project Structure

TECDEM utilizes [CityDPC](https://github.com/RWTH-E3D/CityDPC) componenets for geometry extraction and further processing. The strucuture of the project is displayed in the following diagram:

![Project Structure](img/TECDEM_structure.png)

## Roadmap

The tool is currently under active development. Future updates and releases are planned, as well as publication in a journal. Stay tuned for more features and improvements.


- Planned to allow for different spatial merges. 
- Verifaction and validation of GML files.
- Write results to CityGML + EnergyADE files


## Authors and Acknowledgment

TECDEM is developed and maintained by Felix Rehmann. For inquiries, please contact: rehmann@tu-berlin.de

## License

TECDEM is licensed under the MIT License.

## Contributing

At present, there are no other contributors to the project. However, we welcome contributions and feedback from the community.

## Acknowledgments

TECDEM utilizes [CityDPC](https://github.com/RWTH-E3D/CityDPC) componenets for geometry extraction and further processing. 

TECDEM utilizes [Districtgenerator](https://github.com/RWTH-EBC/districtgenerator) for the simulation of the districts.

TECDEM utilizes [TABULA](https://www.iwu.de/index.php?id=205) for archetype enrichment of residential buildings. 

TECDEM utilizes [DataNWG](https://www.datanwg.de/home/aktuelles/) for the archetype enrichment of non-residential buildings.

