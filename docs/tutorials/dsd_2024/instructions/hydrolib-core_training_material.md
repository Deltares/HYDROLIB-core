# Installation

To install:
1. Download Miniforge3 from [the miniforge github](https://github.com/conda-forge/miniforge?tab=readme-ov-file#miniforge3)
   and install it with the recommended settings.
2. Open "Miniforge Prompt". On Windows: Press "Start" and type "Miniforge Prompt"
3. Run the following command in the Miniforge Prompt: 
> ``conda create -n hydrolib-core-dsd -y python=3.12``
4. When this has finished succesfully, run 
> ``conda activate hydrolib-core-dsd``
5. Once in the active enviroment we install all dependencies with pip: 
> ``pip install hydrolib-core geopandas openpyxl notebook ipykernel``

# Exercises HYDROLIB-core
We have set up a Jupyter Notebook with exercises to get you started on how to use HYDROLIB-core for creating models.

1. In the active environment install a jupyter kernel: 
> ``python -m ipykernel install --name=hydrolib-core-dsd``
2. And start the notebook: 
> ``jupyter notebook <path to magdalena_workbook_exercises.ipynb>``

In this tutorial we will create a 1D2D fluvial flood model of the Magdalena river in Columbia.

## Worked out answers
An example of the worked out exercises can be found within the other provided notebook: *magdalena_workbook_workedout.ipynb*.

## Cheat sheet

In HYDROLIB-core, there is a class called FileModel, which is used to represent an individual kernel file. This class has multiple derived implementations, with each one corresponding to a specific kernel file. Every FileModel, except for the root model, is referenced within another FileModel, following the same hierarchy as the kernel files themselves.

The table below contains the models relevant for today's exercises.

### Kernel files vs HYDROLIB-core FileModels
| **Kernel file**                                    	| **FileModel** 	| **File reference**                     	        |
|---------------------------------------------	|------------------	|--------------------------------------------------- |
| Model definition file (*.mdu)               	| FMModel          	| -                                                  |
| Network file (*_net.nc)                     	| NetworkModel     	| MDU > [geometry] > netFile                           |
| Cross-section location file (crosloc.ini)   	| CrossLocModel    	| MDU > [geometry] > crossLocFile                      |
| Cross-section definition file (crosdef.ini) 	| CrossDefModel    	| MDU > [geometry] > crossDefFile                      |
| Roughness file (roughness-*.ini)            	| FrictionModel    	| MDU > [geometry] > frictFile                         |
| New external forcing file (*_bnd.ext)       	| ExtModel         	| MDU > [external forcing] > extForceFileNew           |
| Boundary conditions file (*.bc)             	| ForcingModel     	| New external forcing file > [boundary] > forcingFile |
| 1D initial conditions field file (*.ini)    	| OneDFieldModel   	| Initial field file > [initial] > dataFile            |
| Initial field file (*.ini)                  	| IniFieldModel    	| MDU > [geometry] > iniFieldFile                      |
| Structures file (structures.ini)            	| StructureModel   	| MDU > [geometry] > structureFile                     |

### Commonly used functions of a **FileModel**
Each FileModel offers a set of commonly used functions. 

---
**__init__()**: Create a new file model instance

Parameters (all optional):
* `filepath (Path)`: The file path from which the file model should be loaded. Default to None.
* `resolve_casing (bool)`: Whether to resolve the file name references so that they match the case with what is on disk. This can be handy for case-sensitive operating systems, like Linux. Defaults to False.
* `recurse (bool)`: Whether or not to recursively load the model. If True, the file plus all the referenced files will be loaded. Otherwise, only this file will be loaded. Defaults to True.
* `path_style (str)`: Which path style is used in the model files. This is useful when reading a model with Linux paths on a Windows machine, and vice versa. Options: 'unix', 'windows'. Defaults to the path style that matches the current operating system.

Example:

> `fmmodel = FMModel(filepath='dflowfm.mdu', recurse=True)`

The above line creates an FM model object with all the data from the `dflowfm.mdu` MDU file. Because `recurse=True` it also loads all data from the other model files, such as the cross sections.

---
**save()**: Write the model data to a file

Parameters (all optional):
* `filepath (Path)`: The file path at which this model is saved. If None is specified it defaults to the filepath currently stored in the filemodel. Defaults to None.
* `recurse (bool)`: Whether to recursively save all children of this file model, or only save this model. Defaults to False.
* `path_style (str)`: With which file path style to save the model. File references will be written with the specified path style. Options: 'unix', 'windows'. Defaults to the path style used by the current operating system.

Example:

> `fmmodel.save(filepath='dflowfm_saved.mdu', recurse=True)`

The above line saves the FM model data to the `dflowfm_saved.mdu` MDU file. Because `recurse=True` it also writes the model data to the other model files, such as the cross sections files.

---
**show_tree()**: Print the file model tree

> `fmmodel.show_tree()`