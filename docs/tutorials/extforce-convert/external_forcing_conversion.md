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
        - [`--extoldfile` / `-e`](#-extoldfile-e)
        - [`--dir` / `-d`](#-dir-d)
    - [`--outfiles` / `-o`](#-outfiles-o)
    - [Backups](#backups)
        - [`--no-backup`](#-no-backup)
    - [`--remove-legacy-files` / `-r`](#-remove-legacy-files-r)
    - [`--path-style {unix,windows}`](#-path-style-unixwindows)
- [Examples](#examples)
- [Additional Notes](#additional-notes)

---

## Introduction

`extforce-convert` is a command-line tool that helps migrate legacy external forcing configurations in D-Flow FM to the newest, more modular format. This tool can handle:
- Conversions of a single `mdu` file.
- Conversions of a standalone legacy external forcing file.
- Recursively converting all `.mdu` files within a specified directory.

Note: Depending on your installation, the executable may be named `extforce-convert` or `extforce_convert`. You can always run it as a module: `python -m hydrolib.tools.extforce_convert.cli`.

---

## Installation

To use the CLI directly from your terminal, ensure that:
1. The `hydrolib` Python package is installed in your environment.

If `extforce-convert` is distributed as part of `hydrolib`, simply install or update `hydrolib`:
```bash
pip install hydrolib
```
Once installed, the `extforce-convert` command should be available in your PATH if your Python script folder is accessible. Alternatively, you may run it using:
```bash
python -m hydrolib.tools.extforce_convert.cli [options]
```

---

## Usage Overview

The basic usage pattern is:
```bash
extforce-convert [options]
```
Where exactly one of `--mdufile`, `--extoldfile`, or `--dir` is required.

---

## Arguments

Below is a complete list of arguments supported by the CLI:

### `--version`
**Syntax**: `--version`  
Displays the version of the `hydrolib` package currently installed, then exits.

### `--verbose` / `-v`
**Syntax**: `--verbose` or `-v`  
Enables additional diagnostic information during the conversion process. Use this option if you need more insight into what the tool is doing.

### `--debug-mode`
**Syntax**: `--debug-mode`  
Convert the supported quantities only and leave unsupported quantities in the old external forcing file. Default is `False`. Without this flag, a conversion will fail if any unsupported quantities are present.

---

### Mutually Exclusive Options

You must choose **one** of these three arguments to specify your source of legacy external forcing data.

#### `--mdufile` / `-m`
**Syntax**: `--mdufile MDUFILE` or `-m MDUFILE`  
Specifies an `mdu` file from which input and output filenames for the conversion are automatically inferred.
- **Example**: `-m path/to/project.mdu`

#### `--extoldfile` / `-e`
**Syntax**: `--extoldfile EXTOLDFILE` or `-e EXTOLDFILE`  
Specifies a single legacy external forcing file (e.g., `.ext` format) to be converted.
- **Example**: `-e path/to/old_external_forcing.ext`

#### `--dir` / `-d`
**Syntax**: `--dir DIRECTORY` or `-d DIRECTORY`  
Specifies a directory path; the tool will search recursively for `.mdu` files and convert them.
- **Example**: `-d /path/to/projects`

---

### `--outfiles` / `-o`
**Syntax**: `--outfiles EXTFILE INIFIELDFILE STRUCTUREFILE` or `-o EXTFILE INIFIELDFILE STRUCTUREFILE`  
Allows you to explicitly set the output filenames for:
1. External forcings file
2. Initial fields file
3. Structures file

If you omit these, default names will be used (e.g., `inifields.ini`, `structures.ini`, etc.).

Important: `--outfiles` applies only to single-file conversions (with `--mdufile` or `--extoldfile`). It cannot be used together with `--dir`.

---

### Backups

#### `--no-backup`
**Syntax**: `--no-backup`  
By default, the tool creates a backup of each file that will be overwritten. Use `--no-backup` to disable backups and overwrite files in-place.

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

1. **Convert a single MDU file, preserving backups, with verbose mode**:
   ```bash
   extforce-convert -m path/to/project.mdu -v
   ```
   This command infers the input/output from the `project.mdu` file, prints extra diagnostic info, and creates backup files.

2. **Convert a legacy external forcing file, specify exact output filenames, do not create backups**:
   ```bash
   extforce-convert -e oldforcing.ext -o newforcing.ext inifields.ini structures.ini --no-backup
   ```
   This specifies an old external forcing file, outputs three new files with specified names, and overwrites any existing files without backups.

3. **Recursively convert all `.mdu` files in a directory, remove legacy files**:
   ```bash
   extforce-convert -d /path/to/projects --remove-legacy-files
   ```
   Searches the directory and subdirectories for `.mdu` files, converts them, and removes the old `.tim` files after conversion.

4. **Convert with path handling and debug mode**:
   ```bash
   extforce-convert -m path/to/project.mdu --path-style unix --debug-mode
   ```
   Forces Unix-style path handling (useful on Windows for models authored on Unix) and converts supported quantities while leaving unsupported ones in the old file.

---

## Additional Notes

- If no valid input argument (`--mdufile`, `--extoldfile`, or `--dir`) is provided, the program will exit with an error indicating that no input was specified.
- `--outfiles` cannot be combined with `--dir`.
- Each conversion process involves parsing the old file(s), generating new format files, and (optionally) deleting or backing up files as directed by the command-line options.
- If you encounter any errors during conversion, re-run the command with `-v` (verbose) or check the backup files (if enabled) for debugging.

---
