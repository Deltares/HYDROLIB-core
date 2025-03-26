# `extforce-convert` Command Line Interface (CLI) Documentation

This document provides detailed usage instructions, argument descriptions, and examples for the `extforce-convert` CLI tool. The CLI is designed to convert D-Flow FM legacy external forcing files to the current format, which includes separate files for external forcings, initial fields, and structures.

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage Overview](#usage-overview)
- [Arguments](#arguments)
    - [`--version`](#version)
    - [`--verbose` / `-v`](#verbose--v)
    - [Mutually Exclusive Options](#mutually-exclusive-options)
        - [`--mdufile` / `-m`](#mdufile--m)
        - [`--extoldfile` / `-e`](#extoldfile--e)
        - [`--dir` / `-d`](#dir--d)
    - [`--outfiles` / `-o`](#outfiles--o)
    - [Backup Options](#backup-options)
        - [`--backup` / `-b`](#backup--b)
        - [`--no-backup`](#no-backup)
    - [`--remove-legacy-files`](#remove-legacy-files)
- [Examples](#examples)
- [Additional Notes](#additional-notes)

---

## Introduction

`extforce-convert` is a command-line tool that helps migrate legacy external forcing configurations in D-Flow FM to the newest, more modular format. This tool can handle:
- Conversions of a single `mdu` file.
- Conversions of a standalone legacy external forcing file.
- Recursively converting all `.mdu` files within a specified directory.

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

---

### Backup Options

#### `--backup` / `-b`
**Syntax**: `--backup` or `-b` (default)  
Tells the tool to create backups of every file that might be overwritten during the conversion. By default, this behavior is **enabled**.

#### `--no-backup`
**Syntax**: `--no-backup`  
Disables the backup creation behavior. The tool will overwrite files without saving previous copies.

---

### `--remove-legacy-files`
**Syntax**: `--remove-legacy-files`  
Deletes old/legacy files (e.g., `.tim`) after successfully converting them to the new format. Default is `False`.

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

---

## Additional Notes

- If no valid input argument (`--mdufile`, `--extoldfile`, or `--dir`) is provided, the program will exit with an error indicating that no input was specified.
- Each conversion process involves parsing the old file(s), generating new format files, and (optionally) deleting or backing up files as directed by the command-line options.
- If you encounter any errors during conversion, re-run the command with `-v` (verbose) or check the backup files (if enabled) for debugging.

---
