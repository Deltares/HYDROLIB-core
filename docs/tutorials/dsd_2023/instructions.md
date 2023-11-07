# HYDROLIB-core guide for the Delft Software Days 2023

## Contents

- [HYDROLIB-core guide for the Delft Software Days 2023](#hydrolib-core-guide-for-the-delft-software-days-2023)
  - [Contents](#contents)
  - [Introduction](#introduction)
  - [User guide](#user-guide)
    - [Requirements](#requirements)
    - [Installation](#installation)
    - [Run the demo notebook](#run-the-demo-notebook)

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
- **Visual Studio Code**: https://code.visualstudio.com/download
Visual Studio Code  is a free, open-source and lightweight code editor for software development.
- **Visual Studio Code extensions for Python and Jupyter**: In Visual Studio Code, navigate to the Extensions section on the left sidebar, search for "Python," and install the extension. Additionally, search for "Jupyter" and install the Jupyter extension.

### Installation
Once you've installed the required software, you can create a Python 3.11 environment with HYDROLIB-core 0.5.2, the latest release. 
Note that the environment that we are creating now contains not only HYDROLIB-core, but also the other packages that are needed today during the breakout sessions.

Follow these steps:

1. Open your command line interface
2. Enter the following commands:

```
conda create --name dsd_env python=3.11 git -c conda-forge -y
conda activate dsd_env
pip install hydromt_delft3dfm[examples] dfm_tools
pip install pyogrio
pip install openpyxl
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

1. Open Visual Studio Code
2. Go to *File* > *Open Folder...*
3. Select the *HYDROLIB-core* folder
4. From the file explorer on the left, open the *demo.ipynb* inside the *demo* folder 
5. On the top right, click on *Select Kernel* and then *Python Environments...*
6. Select *dsd_env* from the drop-down list
7. Click on *Run all* to test if the notebook can be fully run