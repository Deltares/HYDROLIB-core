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
	 * Ensure that you are using the poetry environment (this contains commitizen), optionally run this command in a fresh environment:
	 ```
	 poetry install
	 ```
	 * Update the Changelog before bumping the release version (use the version tag instead of the raw version number (so without "v" in our case)):
	 ```
	 cz changelog --unreleased-version="0.3.1" --incremental
	 ```
	 * Use MAJOR, MINOR or PATCH to increment the version
	 ```
	 cz bump --increment {MAJOR,MINOR,PATCH}
	 ```
	 * Push the tags and changes to git
	 ```
	 git push --tags
	 git push
	 ```
	 * Build the wheels and publish the package to PyPi (get an API token in your PyPI account)
	 ```
	 poetry build
	 poetry publish --username __token__ --password [PYPI_API_TOKEN]
	 ```
	 You will need a PyPI account and permissions for this publish step. Ask a maintainer for help if you need this.
* Go to the hydrolib-core GitHub page.
* Go to `Releases` and click on `Draft a new release`.
* Fill in the `Release title` field with `Release v<VERSION>`, with `<VERSION>` in the full format `<MAJOR>.<MINOR>.<PATCH>`, for example `Release v0.3.0`.
* Choose the appropriate version tag in the `Choose a tag` dropdown box (typically `<VERSION>` without "v" prefix).
* Click on `Generate release notes`.
* Click on `Publish release`.
* Celebrate :partying_face:


### Automatic release

This section describes the purpose, structure, and usage of the `release.yml` GitHub Actions workflow.


#### Workflow Overview
**Name:** `Automated release workflow`

This workflow is manually triggered to create a release of the Python package. It allows:
- Releasing from a user-specified branch (default: `main`)
- Manual or auto-generated version control (e.g. `1.0.0` or `1.0.0-beta.1`)
- Conditional test mode to simulate the release process without tagging or publishing

---

###### Trigger
```yaml
on:
  workflow_dispatch:
```
This workflow is triggered manually from the GitHub Actions UI.

---

###### Inputs
| Name           | Description                                               | Required | Default |
|----------------|-----------------------------------------------------------|----------|---------|
| `release_branch` | Branch to create release from                           | ❌       | `main`  |
| `version`        | Full version (e.g. `1.0.0`, `1.0.0-beta.1`)             | ❌       |         |
| `major`          | Major version if not using `version`                   | ❌       |         |
| `minor`          | Minor version if not using `version`                   | ❌       |         |
| `patch`          | Patch version if not using `version`                   | ❌       |         |
| `increment`      | Type of version bump (`MAJOR`, `MINOR`, `PATCH`)       | ❌       |         |
| `test_mode`      | Run in test mode (skip tagging/publishing)             | ❌       | `false` |

---

###### Jobs and Steps
####### `release` Job
**Runs on:** `ubuntu-latest`

####### Key steps:
- **Validate branch**: Ensures `release_branch` exists in the remote repository
- **Checkout**: Uses `actions/checkout@v4` to get code from the chosen branch
- **Python/Poetry Setup**: Uses `actions/setup-python`, Poetry, and caching
- **Dependency Installation**: Installs via `poetry install`
- **Version Determination**: Resolves version from inputs
- **Changelog Generation**: Creates changelog using `cz changelog`
- **Version Bumping**: Uses `cz bump` with dry-run if `test_mode` is true
- **Package Build and Publish**: Builds and optionally publishes to PyPI
- **GitHub Release**: Tags and creates a GitHub Release if `test_mode` is false

---

#### Notes
- This workflow uses `commitizen (cz)` for versioning and changelog management.
- Secrets required: `PYPI_API_TOKEN` for publishing to PyPI.
- Assumes `pyproject.toml` is configured correctly for Poetry and Commitizen.

---

#### Example Usage
When manually triggering the workflow:
- Fill in `version=1.0.0-beta.1` **or** `major=1`, `minor=0`, `patch=0`, `increment=PATCH`
- Set `release_branch=release/1.0.0` or leave it blank to use `main`