# Triggering a GitHub Release

This repository ships via the GitHub Actions workflow in `.github/workflows/release.yml`. It is a manual (workflow_dispatch) workflow that bumps the version, generates the changelog, builds the package, publishes to PyPI, and creates a GitHub release.

## Prerequisites

- You have permission to run workflows on the repository.
- Repository secrets are configured:
  - `PYPI_API_TOKEN` for publishing to PyPI.
  - `GITHUB_TOKEN` is provided automatically by GitHub Actions.
- The release branch (default `main`) is up to date and protected branch rules allow the workflow to push commits and tags.

## How to trigger the workflow

1. Go to GitHub → **Actions**.
2. Select **Automated release workflow**.
3. Click **Run workflow**.
4. Choose the `release_branch` (defaults to `main`).
5. Provide a version using one of the two methods below.

## Version input options

Choose exactly one of the following approaches:

### Option A: Full version string

Set `version` to a full release version such as `1.2.3` or `1.2.3-beta.1`.  
This is the most reliable option and overrides all other version inputs.

### Option B: Major/Minor/Patch

Provide `major`, `minor`, and `patch` values to construct a version string.  
For example: `major=1`, `minor=2`, `patch=3` → `1.2.3`.

Note: The `increment` input exists in the workflow UI but is not used by the workflow script.

## What the workflow does

- Checks out the `release_branch` and determines the target version.
- Generates the changelog for the new version.
- Bumps the version and pushes the commit and tag to the repository.
- Builds the package and publishes it to PyPI.
- Creates a GitHub release for the tag.

## Pre-release tagging

If the version contains the letter `b` (for example `1.2.3b1`), the GitHub release is marked as a pre-release.
