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