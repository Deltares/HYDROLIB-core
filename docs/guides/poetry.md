# Installation using Poetry

You can use a Poetry-based installation if you are using
hydrolib-core from a local clone of the Github repository,
for example if you intend to contribute to the code.

## Clone the GitHub repo
Use your own preferred way of cloning the GitHub repository of hydrolib-core.

## Use Poetry to install hydrolib-core
We use `poetry` to manage our package and its dependencies.

1. Download + installation instructions for Poetry are [here](https://python-poetry.org/). In the examples below it is placed in `C:\checkouts\HYDROLIB-core_git`.
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
Installing the current project: hydrolib-core (0.1.3)
(base) PS C:\checkouts\HYDROLIB-core_git> 
```  
   If you need to use an already existing Python installation, you can activate it and run `poetry env use system` before `poetry install`.

3. Test your installation, by running the hydrolib-core pytest suite via poetry:
```
(base) PS C:\checkouts\HYDROLIB-core_git> poetry run pytest
================================================= test session starts =================================================
platform win32 -- Python 3.8.8, pytest-6.2.5, py-1.10.0, pluggy-1.0.0
rootdir: C:\checkouts\HYDROLIB-core_git, configfile: pyproject.toml
plugins: cov-2.12.1
collected 426 items / 2 deselected / 424 selected

tests\test_model.py ...............                                                                              [  3%]
tests\test_utils.py .......                                                                                      [  5%]
[..]
(base) PS C:\checkouts\HYDROLIB-core_git>
```

4. Start using hydrolib-core. You can launch your favourite editor (for example VS Code)
by first starting a poetry shell with the virtual hydrolib-core environment:
```
(base) PS C:\checkouts\HYDROLIB-core_git> poetry shell
(base) PS C:\checkouts\HYDROLIB-core_git> code
```

