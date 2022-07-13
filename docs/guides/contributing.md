# Contributing


## Tooling
### Poetry
We use `poetry` to manage our package and its dependencies. More information on the separate [Poetry](poetry.md) page.

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

## Releasing
### Making a release on GitHub and PyPi

When we are releasing hydrolib-core, we want to create a release on GitHub and PyPi.
This should only be done by one of the hydrolib-core maintainers.
To prepare for releasing, please make sure you have a clean checkout of the latest `main` branch and follow these steps:

 * Go to the root level your hydrolib-core checkout location
 * Open your command line in this location
 * Perform the following commands:
	 * If commitizen is not installed yet:
	 ```
	 pip install commitizen
	 ```
	 * Use MAJOR, MINOR or PATCH to increment the version
	 ```
	 cz bump <MAJOR|MINOR|PATCH>
	 ```
	 * Or let commitizen detect the increment automatically
	 ```
	 cz bump
	 ```
	 * Push the tags and changes to git
	 ```
	 git push --tags
	 git push
	 ```
	 * Build the wheels and publish the package to PyPi
	 ```
	 poetry build
	 poetry publish
	 ```
* Go to the hydrolib-core GitHub page.
* Go to `Releases` and click on `Draft a new release`.
* Fill in the `Release title` field with `Release v<VERSION>`, with `<VERSION>` in the full format `<MAJOR>.<MINOR>.<PATCH>`, for example `Release v0.3.0`.
* Choose the appropriate tag in the `Choose a tag` dropdown box (typically `<VERSION>`).
* Click on `Generate release notes`.
* Click on `Publish release`.
* Celebrate :partying_face:
