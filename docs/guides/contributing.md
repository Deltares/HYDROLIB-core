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
If you use [conventional commit messages](https://www.conventionalcommits.org/en/v1.0.0/#summary), the [`changelog.md`](../changelog.md) is generated automatically. More details below under ["Merging"](#merging).

## Development

### Branches
For each issue or feature, a separate branch should be created from the main. To keep the branches organized each branch should be created with a prefix in the name:
* `feat/` for new features and feature improvements;
* `fix/` for bugfixes;
* `docs/` for documentation;
* `chore/` for tasks, tool changes, configuration work, everything not relevant for external users.

After this prefix, preferrably add the issue number, followed by a brief title using underscores. For example: `feat/160_obsfile` or, `fix/197_validation_pump_stages`.

### Pull requests
When starting development on a branch, a pull request should be created for reviews and continous integration. 
In the description text area on GitHub, use a [closing keyword](https://docs.github.com/articles/closing-issues-using-keywords) such that this PR will be automatically linked to the issue.
For example: `Fixes #160`.

During continuous integration, the checks will be run with several Python versions on Windows, Ubuntu and MacOS. The checks consist of running the tests, checking the code formatting and running SonarCloud. 
We advise to use a draft pull request, to prevent the branch to be merged back before developement is finished. When the branch is ready for review, you can update the status of the pull request to "ready for review".

### Reviews
When an issue is ready for review, it should be moved to the "Ready for review" column on the GitHub board for visibility. 

### Merging
Merging a branch can only happen when a pull request is accepted through review. When a pull request is accepted the changes should be merged back with the "squash and merge" option.
The merge commit message should adhere to the [conventional commit guidelines](https://www.conventionalcommits.org/en/v1.0.0/#summary).
* In the first textfield of the GitHub commit form, use for example: `feat: Support 3D timeseries in .bc file`, *without* any PR/issue references.
* In the text area of the GitHub commit form, optionally add some more description details on the commit.
* In the same text area, add footer line `Refs: #<issuenr>`, and if needed an extra line `BREAKING CHANGE: explanation`. Don't forget a blank line between footer lines and the preceding description lines (if present).

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
	 * Prepare the Changelog before bumping the release version:
	 ```
	 cz changelog --unreleased-version="0.3.1" --incremental
	 ```
	 In the above command, use the version tag instead of the raw version number (so without "v" in our case).
	 If you don't know the version tag yet, you can do a dry-run of the next step, for example via:
	 ```
	 cz bump --dry-run --increment PATCH
	 ```
	 * In the updated `docs/changelog.md`, manually add links to GitHub PR numbers (or issue numbers) at the end of each line, if appropriate.
         It is recommended to use the macros `{{gh_pr(123)}}`, resp. `{{gh_issue(345)}}` to get automatic hyperlinks (where 123 and 345 are GitHub's PR and issue numbers, respectively).
	 * Use MAJOR, MINOR or PATCH to increment the version
	 ```
	 cz bump --increment {MAJOR,MINOR,PATCH}
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
	 You will need a PyPI account and permissions for this publish step. Ask a maintainer for help if you need this.
* Go to the hydrolib-core GitHub page.
* Go to `Releases` and click on `Draft a new release`.
* Fill in the `Release title` field with `Release v<VERSION>`, with `<VERSION>` in the full format `<MAJOR>.<MINOR>.<PATCH>`, for example `Release v0.3.0`.
* Choose the appropriate version tag in the `Choose a tag` dropdown box (typically `<VERSION>` without "v" prefix).
* Click on `Generate release notes`.
* Click on `Publish release`.
* Celebrate :partying_face:
