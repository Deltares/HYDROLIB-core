# HYDROLIB-core guide for the Delft Software Days 2023

## Contents

- [HYDROLIB-core guide for the Delft Software Days 2023](#hydrolib-core-guide-for-the-delft-software-days-2023)
  - [Contents](#contents)
  - [Introduction](#introduction)
  - [User guide](#user-guide)
    - [Requirements](#requirements)
    - [Installation](#installation)
    - [Run the demo notebook](#run-the-demo-notebook)
  - [Cheat sheet](#cheat-sheet)
    - [Kernel files vs HYDROLIB-core FileModels](#kernel-files-vs-hydrolib-core-filemodels)
    - [Commonly used functions of a FileModel](#commonly-used-functions-of-a-filemodel)


## Introduction
This document contains instructions about the installation and usage of HYDROLIB-core during the Delft Software Days 2023.

HYDROLIB-core is a Python package that offers functionality to process D-HYDRO input files. It offers Python-wrapped classes that represent these files and their content. 
HYDROLIB-core serves as the basis for various pre- and postprocessing tools for a modelling workflow of hydrodynamic simulations in D-HYDRO.

## User guide
### Requirements
Before getting started with HYDROLIB-core, make sure you have the following software and tools installed:

- **Anaconda**: https://www.anaconda.com/download
Anaconda is an open-source distribution for Python and contains the package manager "conda". 
(!) Make sure to add Anaconda to your PATH environment variable during installation.

### Installation
Once you've installed the required software, you can create a Python 3.11 environment with HYDROLIB-core 0.5.2, the latest release. 
Note that the environment that we are creating now contains not only HYDROLIB-core, but also the other packages that are needed today during the breakout sessions.

Follow these steps:

1. Open your command line interface
2. Enter the following commands:

```
conda create --name dsd_env python=3.11 git -c conda-forge -y
conda activate dsd_env
pip install hydromt_delft3dfm[examples] dfm_tools pyogrio openpyxl
conda deactivate
```

After executing these commands, an Anaconda environment with the latest HYDROLIB-core is created. After deactivation, you can reactivate this environment at any time by using the following command:
```
conda activate dsd_env
```

If you'd like to remove the environment entirely, call the following command:

```
conda remove -n dsd_env --all
```

This will remove all the packages in the environment and the environment folder itself.
  

### Run the demo notebook

We'd like to be able to run the provided demo notebook. We can set it up with the following steps:

1. Open a command line in the *HYDROLIB-core* folder
2. Activate the conda environment:
```
conda activate dsd_env
```
3. And start Jupyter Notebook:
```
jupyter notebook
```
4. Open the *demo.ipynb* inside the *demo* folder

## Cheat sheet

In HYDROLIB-core, there is a class called FileModel, which is used to represent an individual kernel file. This class has multiple derived implementations, with each one corresponding to a specific kernel file. Every FileModel, except for the root model, is referenced within another FileModel, following the same hierarchy as the kernel files themselves.

The table below contains the models relevant for today's exercises. 

### Kernel files vs HYDROLIB-core FileModels
| **Kernel file**                                    	| **FileModel (Python class in HYDROLIB-core)** 	| **File reference**                                         	|
|---------------------------------------------	|------------------	|------------------------------------------------------------	|
| Model definition file (*.mdu)               	| FMModel          	| -                                                          	|
| Network file (*_net.nc)                     	| NetworkModel     	| Model definition file > geometry > netFile                 	|
| Cross-section location file (crosloc.ini)   	| CrossLocModel    	| Model definition file > geometry > crossLocFile            	|
| Cross-section definition file (crosdef.ini) 	| CrossDefModel    	| Model definition file > geometry > crossDefFile            	|
| Roughness file (roughness-*.ini)            	| FrictionModel    	| Model definition file > geometry > frictFile               	|
| New external forcing file (*_bnd.ext)       	| ExtModel         	| Model definition file > external forcing > extForceFileNew 	|
| Boundary conditions file (*.bc)             	| ForcingModel     	| New external forcing file > boundary > forcingFile         	|
| 1D initial conditions field file (*.ini)    	| OneDFieldModel   	| Initial field file > initial > dataFile                    	|
| Initial field file (*.ini)                  	| IniFieldModel    	| Model definition file > geometry > iniFieldFile            	|
| Structures file (structures.ini)            	| StructureModel   	| Model definition file > geometry > structureFile           	|

### Commonly used functions of a FileModel
Each FileModel offers a set of commonly used functions. 

**__init__(): Initialize a new file model instance**
Parameters (all optional):
* `filepath (Path)`: The file path from which the file model should be loaded. Default to None.
* `resolve_casing (bool)`: Whether or not to resolve the file name references so that they match the case with what is on disk. Defaults to False.
* `recurse (bool)`: Whether or not to recursively load the model. Defaults to True.
* `path_style (str)`: Which path style is used in the loaded files. Options: 'unix', 'windows'. Defaults to the path style that matches the current operating system. 

**save(): Export the file model data to a file**
Parameters (all optional):
* `filepath (Path)`: The file path at which this model is saved. If None is specified it defaults to the filepath currently stored in the filemodel. Defaults to None.
* `recurse (bool)`: Whether or not to recursively save all children of this file model, or only save this model. Defaults to False.
* `path_style (str)`: With which file path style to save the model. File references will be written with the specified path style. Options: 'unix', 'windows'. Defaults to the path style used by the current operating system.

**show_tree(): Print the file model tree**