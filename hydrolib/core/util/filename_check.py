import logging
import os
import re
from pathlib import Path

from hydrolib.core.io.dimr import parser as dimr_parser
from hydrolib.core.io.ini.io_models import CommentBlock
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.rr import parser as rr_parser


def is_file(value: str) -> list:
    """Checks whether the given value complies to a regex pattern for
    filenames.

    Args:
        value (str): string object to be checked for containing filenames

    Returns:
        (list): List of matches if a filename is present in the string else
        None.
    """
    pattern = r"([\w\d\-.]+\.[A-Za-z]{3})"
    match = re.findall(pattern, value)
    return match if match else None


def file_match(file: str, file_list: list) -> dict:
    """Looks for a match with file in the file list by changing file list to
    all lowercase and returning a dict object with name of file in file list
    and given file name.

    Args:
        file (str): Name of file
        file_list (list): list of files present in a directory.
    Returns:
        (dict): dict object with the matched file name in the directory as
        key and the given file name. If no match is found None is returned.
    """
    file_list_lower = {f.lower(): f for f in file_list}
    if (match_file := file.lower()) in file_list_lower.keys():
        return {file_list_lower[match_file]: file}
    else:
        return None


def parse_filenames_from_ini(ini_file_path: Path) -> list:
    """Parses filenames from .ini or .mdu file.

    Args:
        ini_file_path (Path): Path to .ini file
    Returns:
        files (list): List of files
    """
    parser = Parser(ParserConfig(allow_only_keywords=True, parse_comments=False))
    document = parser.parse(ini_file_path)
    directory = os.path.dirname(ini_file_path)
    files = []
    for section in document.sections:
        for properties in section.content:
            if isinstance(properties, CommentBlock):
                continue

            if properties.key == "IniFieldFile" and properties.value:
                filename_check(Path(os.path.join(directory, properties.value)))
            value = properties.value
            if value and (file := is_file(value)):
                files.extend(file)

    return files


def parse_filenames_from_fnm(fnm_file_path: Path) -> list:
    """Parses filenames from a Sobek .fnm file.

    Args:
        fnm_file_path (Path): Path to .fnm file
    Returns:
        files (list): List of files found in .fnm file
    """
    files = []
    with open(fnm_file_path, "r") as r:
        values = rr_parser._to_values(r.readlines())
        for value in values:
            if value and (file := is_file(value)):
                files.extend(file)

    return files


def filename_check(file_path: Path):
    """Checks whether the filenames mentioned in the given ini-like file are
    present in the directory of the given file. If not present the the
    function looks for a file with the same name but differently formatted
    and renames that file with the file name in the ini file.

    Args:
        ini_file_path (Path): Path to ini/mdu file
    """
    if file_path.suffix in [".ini", ".mdu"]:
        files = parse_filenames_from_ini(file_path)
    elif file_path.suffix == ".fnm":
        files = parse_filenames_from_fnm(file_path)
    else:
        return logging.warning(
            f"Given file path does not contain a file with .mdu/.ini/.fnm extension"
        )

    directory = os.path.dirname(file_path)
    file_list = os.listdir(directory)
    filename = file_path.name

    missing_files = [f for f in files if f not in file_list]
    missing_file_count = len(missing_files)
    if missing_files:
        logging.warning(
            f" {missing_file_count} missing file(s) in directory: {directory}"
        )
        logging.warning(f"Missing file(s): {*missing_files,}")
        if file_path.suffix == ".fnm":
            logging.warning(
                "Filenames specified in Sobek fnm files can be missing in the \
                directory without causing problems, check if this is the case for your model"
            )
        for missing_file in missing_files:
            if match_file := file_match(missing_file, file_list):
                for k, v in match_file.items():
                    os.rename(
                        os.path.join(directory, k),
                        os.path.join(directory, v),
                    )
                    logging.info(f"Renamed {k} to {v}")
            else:
                logging.warning(f"No match found for file: {missing_file}")
    if not missing_file_count:
        logging.info(f"No missing files found in {filename}")


def filename_check_dimr(file_path):
    """Parses a dimr_config.xml file and checks if .mdu or sobek .fnm files
    are present. If these files are found the path is passed to the filename_check
    function.

    Args:
        file_path (Path): Path to dimr_config.xml file
    """
    dimr_dict = dimr_parser.DIMRParser.parse(file_path)
    logging.info("Parsing xml file")
    for component in dimr_dict["component"]:
        if component["inputFile"].endswith((".fnm", ".mdu")):
            fp = Path(
                os.path.join(
                    file_path.parent, component["workingDir"], component["inputFile"]
                )
            )
            logging.info(f"Checking filenames for {fp}")
            filename_check(fp)
