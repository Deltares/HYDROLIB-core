# Installation using Poetry

You can use a Poetry-based installation if you are using
hydrolib-core from a local clone of the Github repository,
for example if you intend to contribute to the code.

## Clone the GitHub repo
Use your own preferred way of cloning the GitHub repository of hydrolib-core.
In the examples below it is placed in `C:\checkouts\HYDROLIB-core_git`.

## Use Poetry to install hydrolib-core
We use `poetry` to manage our package and its dependencies.

!!! note
    If you use `conda`, do not combine conda virtual environments with the poetry virtual environment.
    In other words, run the `poetry install` command from the `base` conda environment.

1. Download + installation instructions for Poetry are [here](https://python-poetry.org/).
2. After installation of Poetry itself, now use it to install your local clone of the hydrolib-core package, as follows.
   Make sure Poetry is available on your `PATH` and run `poetry install` in the hydrolib-core directory in your shell of choice.
   This will create a virtual environment in which hydrolib-core is installed and made available for use in your own scripts.
   For example in an Anaconda PowerShell:
```
(base) PS C:\checkouts\HYDROLIB-core_git> poetry install
Creating virtualenv hydrolib-core-kHkQBdtS-py3.8 in C:\Users\dam_ar\AppData\Local\pypoetry\Cache\virtualenvs
Installing dependencies from lock file

Package operations: 67 installs, 0 updates, 0 removals

  * Installing six (1.16.0)
[..]
Installing the current project: hydrolib-core (0.1.5)
(base) PS C:\checkouts\HYDROLIB-core_git>
```  
   If you need to use an already existing Python installation, you can activate it and run `poetry env use system` before `poetry install`.

3. Test your installation, by running the hydrolib-core pytest suite via poetry:
```
(base) PS C:\checkouts\HYDROLIB-core_git> poetry run pytest
===================================== test session starts ======================================
platform win32 -- Python 3.8.8, pytest-6.2.5, py-1.10.0, pluggy-1.0.0
rootdir: C:\checkouts\HYDROLIB-core_git, configfile: pyproject.toml
plugins: cov-2.12.1
collected 473 items / 2 deselected / 471 selected

tests\io\dflowfm\ini\test_ini.py ........................................................ [  3%]
tests\io\dflowfm\test_bc.py ....                                                          [  4%]
tests\io\dflowfm\test_ext.py ........................................................     [  5%]
tests\io\dflowfm\test_fnm.py ..................                                           [ 11%]
tests\io\dflowfm\test_net.py ............                                                 [ 11%]
tests\io\dflowfm\test_parser.py .                                                         [ 12%]
tests\io\dflowfm\test_polyfile.py ........................................................[ 23%]
....................................                                                      [ 27%]
tests\io\dflowfm\test_structure.py .......................................................[ 42%]
.........................................................                                 [ 54%]
tests\io\dimr\test_dimr.py ...                                                            [ 56%]
tests\io\rr\meteo\test_bui.py ...........................                                 [ 57%]
tests\io\test_docker.py .                                                                 [ 70%]
tests\test_model.py ...............                                                       [ 78%]
tests\test_utils.py .......                                                               [ 91%]
.........................................                                                 [100%]

============================== 471 passed, 2 deselected in 3.50s ===============================
(base) PS C:\checkouts\HYDROLIB-core_git>
```  
4. Start using hydrolib-core. You can launch your favourite editor (for example VS Code)
by first starting a poetry shell with the virtual hydrolib-core environment:
```
(base) PS C:\checkouts\HYDROLIB-core_git> poetry shell
(base) PS C:\checkouts\HYDROLIB-core_git> code
```

## Frequently asked questions
- How to fix "File ... does not exist" errors during `poetry install` as in the example below?
```
  * Installing six (1.16.0)

  ValueError

  File \C:\Users\dam_ar\AppData\Local\pypoetry\Cache\artifacts\48\e6\04\8118155ae3ec3a16dd2a213bbf7a7d8a62c596b2e90f73a22c896269f1\six-1.16.0-py2.py3-none-any.whl does not exist
```
  This may occur when a conda environment was activated.
  Delete the `AppData\Local\pypoetry\Cache` directory.
  Then run `conda deactivate` to return to the base environment.
  Finally, rerun `poetry install`.
