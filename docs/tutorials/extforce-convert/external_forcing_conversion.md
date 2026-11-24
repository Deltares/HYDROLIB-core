# `extforce-convert` Command Line Interface (CLI) Documentation

This document provides detailed usage instructions, argument descriptions, and examples for the `extforce-convert` CLI tool. The CLI is designed to convert D-Flow FM legacy external forcing files to the current format, which includes separate files for external forcings, initial fields, and structures.

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage Overview](#usage-overview)
- [Arguments](#arguments)
    - [`--version`](#-version)
    - [`--verbose` / `-v`](#-verbose-v)
    - [`--debug-mode`](#-debug-mode)
    - [Mutually Exclusive Options](#mutually-exclusive-options)
        - [`--mdufile` / `-m`](#-mdufile-m)
        - [`--dir` / `-d`](#-dir-d)
    - [Backups](#backups)
        - [`--no-backup`](#-no-backup)
    - [`--recurse`](#-recurse)
    - [`--remove-legacy-files` / `-r`](#-remove-legacy-files-r)
    - [`--path-style {unix,windows}`](#-path-style-unixwindows)
- [Examples](#examples)
- [Additional Notes](#additional-notes)

---

## Introduction

`extforce-convert` is a command-line tool that helps migrate legacy external forcing configurations in D-Flow FM to the newest, more modular format. The converted quantities are written to a new external forcings file (`[Boundary]`, `[Lateral]`, `[SourceSink]` and `[Spatial]` blocks; meteo, initial-condition and parameter quantities all become `[Spatial]` blocks), a structures file and a mass balance area file, and the MDU file is updated to reference them. This tool can handle:
- Conversions of a single `mdu` file, also converting all model files that are linked to it.
- Recursively converting all `.mdu` files within a specified directory.

---

## Installation

To use the `extforce-convert` CLI directly from your terminal, make sure that the `hydrolib-core` Python package is installed in your environment.

Simply install or update `hydrolib-core` in your environment:
```bash
pip install hydrolib-core
```
Once installed, the `extforce-convert` command should be available in your PATH (after activating your environment):
```bash
extforce-convert [options]
```
This will not work if your Python script folder is not accessible. Alternatively, you may run it using (note the underscore):
```bash
python -m hydrolib.tools.extforce_convert.cli [options]
```

---

## Usage Overview

The basic usage pattern is:
```bash
extforce-convert [options]
```
Where exactly one of `--mdufile` or `--dir` is required.

---

## Arguments

Below is a complete list of arguments supported by the CLI:

### `--version`
**Syntax**: `--version`  
Displays the version of the `hydrolib-core` package currently installed, then exits.

### `--verbose` / `-v`
**Syntax**: `--verbose` or `-v`  
Enables additional diagnostic information during the conversion process. Use this option if you need more insight into what the tool is doing.

### `--debug-mode`
**Syntax**: `--debug-mode`  
Convert the supported quantities only and leave unsupported quantities in the old external forcing file. Default is `False`. Without this flag, a conversion will fail if any unsupported quantities are present. Most quantities are already supported so most users won't need this option. This option will be removed when all quantities are supported.


---

### Mutually Exclusive Options

You must choose **one** of these arguments to specify your source of legacy external forcing data (`--mdufile` or `--dir`).

#### `--mdufile` / `-m`
**Syntax**: `--mdufile MDUFILE` or `-m MDUFILE`  
Specifies an `mdu` file from which input and output filenames for the conversion are automatically inferred.
- **Example**: `-m path/to/project.mdu`

#### `--dir` / `-d`
**Syntax**: `--dir DIRECTORY` or `-d DIRECTORY`  
Specifies a directory path; the tool will search recursively for `.mdu` files and convert them. MDU files whose name
contains `_ext` are skipped. If one model fails, the error is printed and the tool continues with the next one.
- **Example**: `-d /path/to/projects`


The output filenames are always derived automatically from the MDU file, for both `--mdufile` and `--dir`
(the latter applies it to every `.mdu` file it finds).

---

### Backups

#### `--no-backup`
**Syntax**: `--no-backup`  
By default, the tool creates a backup of each file that will be overwritten. Use `--no-backup` to disable backups and overwrite files in-place.

---

### `--recurse`
**Syntax**: `--recurse`  
Recursively resolves and loads files referenced by the existing new-format external forcing file, including `.bc` files. Default is `False`.

This option is independent of `--dir`: `--dir` searches subdirectories for `.mdu` files, while `--recurse` controls loading referenced files.

---

### `--remove-legacy-files` / `-r`
**Syntax**: `--remove-legacy-files` or `-r`  
Deletes old/legacy files (e.g., `.tim`) after successfully converting them to the new format. Default is `False`.

---

### `--path-style {unix,windows}`
**Syntax**: `--path-style unix` or `--path-style windows`  
Handle absolute paths in input files according to the specified style. Use this when converting models with Unix paths on Windows, or with Windows paths on Unix.

---


## Examples

Below are several usage examples to illustrate typical operations:

1. **Basic usage: convert a single MDU file, preserving backups**:
   ```bash
   extforce-convert -m path/to/project.mdu
   ```
   This command infers the input/output from the `project.mdu` file, converts any old external forcing file into new-format files and creates backup files.

2. **Convert a single MDU file/model with verbose mode, do not create backups and removes legacy files**:
   ```bash
   extforce-convert -m path/to/project.mdu -v --no-backup --remove-legacy-files
   ```
   This command infers the input/output from the `project.mdu` file, prints extra diagnostic info, does not create backup files and removes legacy files (e.g. `.tim`) after conversion.

3. **Convert with path handling and debug mode**:
   ```bash
   extforce-convert -m path/to/project.mdu --path-style unix --debug-mode
   ```
   Forces Unix-style path handling and converts supported quantities while leaving unsupported ones in the old file.

4. **Recursively convert all `.mdu` files in a directory**:
   ```bash
   extforce-convert -d /path/to/projects
   ```
   Searches the directory and subdirectories for `.mdu` files and converts them.


5. **Convert an MDU file and normalize legacy quantities in referenced `.bc` files**:
   ```bash
   extforce-convert -m path/to/project.mdu --recurse
   ```
   Loads the files referenced by the existing new-format external forcing file and saves normalized quantity names in both the external forcing file and its referenced `.bc` files.

---

## Status

### Known model differences

Sometimes the converted model will give different results, the following cases are known and will not change in the future:
- Any WAQ inifields that do not have boundary conditions prescribed behave differently between old and new extfile. In the old extfile the boundaries are initialized with the initial field values if the mirror cells are covered with samples. In the new extfile these are consistently forced with 0-values. To maintain the old behaviour, add explicit boundary conditions for these quantities. More information available in https://github.com/Deltares/HYDROLIB-core/issues/1241#issuecomment-6194211845. >> this also goes for salinity i.c.w. diagnostic computation: https://github.com/Deltares/HYDROLIB-core/issues/1311
- when a delta suffix is present in the new extfile it will be removed. This is intended behaviour, but the delta suffix is not removed in the linked bc files, causing the quantities not to be found by the kernel. A warning is emitted about running the converter again with `recurse=True` (`--recurse`) but the user can also manually remove the delta suffixes from the bc file(s).

### Known performance limitations

Sometimes the conversion can be relatively slow:
- bc files that are mentioned multiple times (for instance `discharge_salinity_temperature_sorsin`) are written multiple times, this can take quite some time.
- netcdf files are not actually read, but nevertheless large netcdf files can make the conversion very slow because of md5 checksums being computed.

### Known exclusions
- The `StructureFile` file (e.g. `structures.ini`) is deliberately left untouched by `extforce-convert`. Users can manually update their structure file to the latest version (v3.x) by reading and writing it with `hydrolib.core.dflowfm.structure.models.StructureModel`. However, this step is excluded in the automatic conversion since this might cause different model results. To retain the old structure behaviour as close as possible, consult the [D-Flow FM User manual](https://content.oss.deltares.nl/delft3d/D-Flow_FM_User_Manual.pdf) section C.14.10 and manually update your structure file and mdu file.

### Known issues in the Delft3D FM 2027.01 kernel

The `extforce-convert` tool helps you with converting your model to the new ext file. Most of the models will be supported by Delft3D FM 2027.01. Some kernel issues cause different model results or errors after converting to the new extfile. These will be resolved in 2027.02:
- incorrect global initialisation of a polygon: [UNST-10214](https://issuetracker.deltares.nl/browse/UNST-10214) (fixed in DIMRset 2.32.00)
- multiple Spatial blocks with a non-override operand and targetMaskFile only use the last mask: [UNST-10436](https://issuetracker.deltares.nl/browse/UNST-10436)
- spatially uniform data in combination with targetMaskFile does not work: [UNST-10507](https://issuetracker.deltares.nl/browse/UNST-10507)
- not possbile to multipy bcascii global timeseries with xyz sample set in new ext file (this was possible in old ext): [UNST-10530](https://issuetracker.deltares.nl/browse/UNST-10530)
- pump in structures v3 goes in opposite direction compared to structures v0: [UNST-10462](https://issuetracker.deltares.nl/browse/UNST-10462) / [UNST-10496](https://issuetracker.deltares.nl/browse/UNST-10496)


## Additional Notes

- Your model is updated in-place. For testing purposes, please execute the converter on a copy of your model.
- If no valid input argument (`--mdufile` or `--dir`) is provided, the program will exit with an error indicating that no input was specified.
- Each conversion process involves parsing the old file(s), generating new format files, and (optionally) deleting or backing up files as directed by the command-line options.
- When the MDU's `ExtForceFileNew` lists **several files separated by a space** (a file name containing spaces must be enclosed in double quotes), the converted quantities are appended to the **first** listed file only; the remaining files are left unchanged and a warning naming them is printed. All migrated quantities are written into that single new external forcings file.
- If you encounter any errors during conversion, re-run the command with `-v` (verbose) or check the backup files (if enabled) for debugging.

---
