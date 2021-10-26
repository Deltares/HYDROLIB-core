# Installation using Poetry
We use `poetry` to manage our package and its dependencies, which you can download [here](https://python-poetry.org/).
After installation, make sure it's available on your `PATH` and run it in the HYDROLIB-core directory in your shell of choice.

To install the package (by default in editable mode) run `poetry install`. We advise using `virtualenv`s, Poetry will create one for you.
If you need to use an already existing Python installation, you can activate it and run `poetry env use system` before `poetry install`.
