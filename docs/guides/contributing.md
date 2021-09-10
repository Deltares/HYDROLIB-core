# Contributing


## Tooling
### Poetry
We use `poetry` to manage our package and its dependencies, which you can download [here](https://python-poetry.org/).
After installation, make sure it's available on your `PATH` and run it in the HYDROLIB-core directory in your shell of choice.

To install the package (by default in editable mode) run `poetry install`. We advise using `virtualenv`s, Poetry will create one for you.
If you need to use an already existing Python installation, you can activate it and run `poetry env use system` before `poetry install`.

### Pytest
We use `pytest` to test our package. Run it with `poetry run pytest` to test your code changes locally.

### Black
We use `black` as an autoformatter. It is also run during CI and will fail if it's not formatted beforehand.

### Isort
We use `isort` as an autoformatter.

### Commitizen
We use `commitizen` to automatically bump the version number.
If you use [conventional commit messages](https://www.conventionalcommits.org/en/v1.0.0/#summary), the [`changelog.md`](../changelog.md) is generated automatically.

## Development

### Branches
For each issue or feature, a separate branch should be created from the main. To keep the branches organized a feature branch should be created with the `feature/` prefix. 
When starting development on a branch, a pull request should be created for reviews and continous integration. During continuous integration, the checks will be run with python 3.8 and 3.9 on Windows, Ubuntu and MacOS. The checks consist of running the tests, checking the code formatting and running SonarCloud. 
We advise to use a draft pull request, to prevent the branch to be merged back before developement is finished. When the branch is ready for review, you can update the status of the pull request to "ready for review".

### Reviews
When an issue is ready for review, it should be moved to the "Ready for review" column on the GitHub board for visibility. 

### Merging
Merging a branch can only happen when a pull request is accepted through review. When a pull request is accepted the changes should be merged back with the "squash and merge" option.

### Coding guidelines
* If there is code that needs to be tested, there should be tests written for it.
* If there are any additions or changes to the public API, the documentation should be updated. 
* Files should be added to the appropriate folder to keep modules and objects within the correct scope.  
