"""CLI.

CLI for converting D-Flow FM legacy external forcings files to current external forcings file/initial
fields file/structures file.
"""

import argparse
from argparse import ArgumentTypeError, Namespace
from pathlib import Path

from hydrolib.core import __version__
from hydrolib.core.base.utils import PathStyle
from hydrolib.tools.extforce_convert.main_converter import (
    ExternalForcingConverter,
    recursive_converter,
)


def valid_file(path_str: str):
    """Validate an .mdu file path and return it as a Path object.

    Args:
        path_str (str):
            The path to the MDU file as provided on the command line.

    Returns:
        Path: The validated path to the file.

    Raises:
        argparse.ArgumentTypeError: If the file does not exist or does not have a .mdu extension.
    """
    path = Path(path_str)
    if not str(path).lower().endswith(".mdu"):
        raise ArgumentTypeError(f"File must have a .mdu extension: {path}")

    if not path.exists():
        raise ArgumentTypeError(f"File not found: {path}")
    return path


def _validator(path_str: str, extension: str):
    """Validate that a file exists and matches the expected extension.

    Args:
        path_str (str):
            The path to the file to validate.
        extension (str):
            The required file extension (including the dot), e.g. ".ext".

    Returns:
        Path: The validated file path.

    Raises:
        argparse.ArgumentTypeError: If the file does not exist or the extension does not match.
    """
    path = Path(path_str)
    if not path.exists():
        raise ArgumentTypeError(f"File not found: {path}")
    if not str(path).lower().endswith(extension):
        raise ArgumentTypeError(f"File must have a {extension} extension: {path}")
    return path


def valid_file_with_extension(extension: str):
    """Create a validator callable for argparse that enforces a file extension.

    Args:
        extension (str):
            The required file extension (including the dot), e.g. ".mdu".

    Returns:
        Callable[[str], Path]:
            A function that validates a path string and returns a Path when invoked.

    Raises:
        argparse.ArgumentTypeError: Raised by the returned validator if the provided path does not exist or
            does not end with the required extension.
    """
    return lambda path_str: _validator(path_str, extension)


def valid_dir(path_str: str):
    """Validate that the given path exists and is a directory.

    Args:
        path_str (str): The path to validate.

    Returns:
        Path: The validated directory path.

    Raises:
        argparse.ArgumentTypeError: If the path does not exist or is not a directory.
    """
    path = Path(path_str)
    if not path.exists():
        raise ArgumentTypeError(f"Directory not found: {path}")
    if not path.is_dir():
        raise ArgumentTypeError(f"Path is not a directory: {path}")
    return path


def _get_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the extforce_convert CLI.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="extforce_convert",
        description="Convert D-Flow FM legacy external forcings files to current external forcings file/initial fields file/structures file.",
    )

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print diagnostic information"
    )
    parser.add_argument(
        "--debug-mode",
        action="store_true",
        default=False,
        help="Convert the supported quantities only and leave unsupported quantities in the old external forcing "
        "file, default is False.(the conversion will fail if there is any unsupported quantities) ",
    )

    # mdu file, extforcefile and dir are mutually exclusive (can only use one)
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--mdufile",
        "-m",
        action="store",
        type=valid_file_with_extension(".mdu"),
        metavar="MDUFILE",
        help="Automatically take input and output filenames from MDUFILE.",
    )
    group.add_argument(
        "--extoldfile",
        "-e",
        action="store",
        type=valid_file_with_extension(".ext"),
        metavar="EXTOLDFILE",
        help="Input EXTOLDFILE to be converted.",
    )
    group.add_argument(
        "--dir",
        "-d",
        action="store",
        type=valid_dir,
        metavar="DIR",
        help="Directory to recursively find and convert .mdu files in.",
    )

    parser.add_argument(
        "--outfiles",
        "-o",
        action="store",
        nargs=3,
        metavar=("EXTFILE", "INIFIELDFILE", "STRUCTUREFILE"),
        help="Save forcings, initial fields and structures to specified filenames (only valid with --mdufile or --extoldfile).",
    )

    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Do not create a backup of each file that will be overwritten.",
    )
    parser.set_defaults(backup=True)

    parser.add_argument(
        "--remove-legacy-files",
        "-r",
        dest="remove_legacy",
        action="store_true",
        default=False,
        help="Remove legacy/old files (e.g. .tim) after conversion. Defaults to False.",
    )
    parser.add_argument(
        "--path-style",
        choices=[style.value for style in PathStyle],
        dest="path_style",
        default=None,
        type=lambda s: PathStyle(s),
        help="Handle absolute paths in input files according to the specified style (unix/windows)."
        "Use this when converting models with unix paths on Windows or windows paths on Unix.",
    )
    return parser


def main(args=None):
    """
    Entry point for the extforce_convert command-line tool.

    CLI argument combinations:

    Required (mutually exclusive, pick one):
      --mdufile, -m MDUFILE         Use MDUFILE to determine input/output files automatically.
      --extoldfile, -e EXTOLDFILE   Convert a specific legacy external forcing file.
      --dir, -d DIR                 Recursively find and convert all .mdu files in DIR.

    Optional:
      --outfiles, -o EXTFILE INIFIELDFILE STRUCTUREFILE
                               Specify output filenames for forcings, initial fields, and structures (only with --mdufile or --extoldfile).
                               Note: requires exactly three paths and is only valid for single-file conversions
                               (i.e., when using --mdufile or --extoldfile). Using --outfiles with --dir is invalid
                               and will result in an error.
      --no-backup                  Do not create a backup of overwritten files.
      --remove-legacy-files, -r    Remove legacy/old files (e.g. .tim) after conversion.
      --debug-mode                 Convert only supported quantities; leave unsupported quantities in the legacy external forcing file (default: False).
      --verbose, -v                Print diagnostic information.
      --version                    Print version and exit.
      --path-style {unix,windows}
                                 Handle absolute paths in input/output files according to the specified style (unix/windows).
                                 Use this when converting models that use unix paths but you are running the converter
                                 on a Windows machine, or the opposite.

    Args:
      args (Optional[List[str]]): Optional list of argument strings to parse instead of sys.argv. Useful for testing.

    Notes:
      - `--outfiles` cannot be combined with `--dir`.
      - `--outfiles` applies only to a single conversion target (from --mdufile or --extoldfile) and must provide three
        filenames, in this order: EXTFILE INIFIELDFILE STRUCTUREFILE.
      - When `--debug-mode` is provided, only supported quantities are converted; unsupported quantities remain in the
        legacy external forcing file. Without this flag, encountering unsupported quantities results in a failure.

    Examples (valid):
        - Use an MDU file and let the tool determine I/O automatically
            ```shell
            >>> extforce_convert --mdufile model.mdu # doctest: +SKIP
            ```
        - Convert a specific legacy .ext and explicitly set output filenames
            ```shell
            >>> extforce_convert --extoldfile old.ext --outfiles new.ext new.ini new.str # doctest: +SKIP
            ```
        - Recursively convert all models in a directory (no --outfiles here)
            ```shell
            >>> extforce_convert --dir ./models --no-backup --remove-legacy-files # doctest: +SKIP
            ```
        - Convert with explicit path style handling
            ```shell
            >>> extforce_convert --mdufile model.mdu --path-style unix # doctest: +SKIP
            ```
        - invalid flags combinations that will raise an error:
            --outfiles only works with single-file modes, not with --dir
            ```shell
            >>> extforce_convert --dir ./models --outfiles a.ext b.ini c.str # doctest: +SKIP
            ```
    """
    parser = _get_parser()
    args = parser.parse_args(args)

    # Disallow --outfiles when converting a directory.
    if args.dir is not None and args.outfiles is not None:
        parser.error(
            "--outfiles cannot be used with --dir. It only applies to single-file conversions."
        )

    if args.mdufile:
        convert_with_mdu_file(args)
    elif args.extoldfile is not None:
        convert_with_extold_file(args)
    elif args.dir is not None:
        recursive_converter(
            args.dir,
            backup=args.backup,
            remove_legacy=args.remove_legacy,
            debug=args.debug_mode,
        )
    else:
        print("Error: no input specified. Use one of --mdufile, --extoldfile or --dir.")


def convert_with_mdu_file(args: Namespace):
    """Convert the old external forcing file using the mdu file.

    Read the old external forcing file path from the mdu file,
    and convert it to the new format files.

    Args:
        args : Namespace
            The arguments parsed from the command line.
    """
    converter = ExternalForcingConverter.from_mdu(
        args.mdufile,
        ext_file_user=(args.outfiles[0] if args.outfiles else None),
        inifield_file_user=(args.outfiles[1] if args.outfiles else None),
        structure_file_user=(args.outfiles[2] if args.outfiles else None),
        path_style=args.path_style,
        debug=args.debug_mode,
    )
    convert(converter, args)


def convert_with_extold_file(args: Namespace):
    """Convert the old external forcing file to the new format files.

    Args:
        args : Namespace
            The arguments parsed from the command line.
    """
    converter = ExternalForcingConverter(
        args.extoldfile,
        ext_file=(args.outfiles[0] if args.outfiles else None),
        inifield_file=(args.outfiles[1] if args.outfiles else None),
        structure_file=(args.outfiles[2] if args.outfiles else None),
        path_style=args.path_style,
        debug=args.debug_mode,
    )
    convert(converter, args)


def convert(converter: ExternalForcingConverter, args: Namespace):
    """Run the update method of ExternalForcingConverter and save the results.

    Args:
        converter : ExternalForcingConverter
            The converter object to convert the old external forcing file.
        args : Namespace
            The arguments parsed from the command line.
    """
    converter.verbose = args.verbose
    converter.update()
    print("Converting the old external forcing file to the new format files is done.")
    print("Saving the new files ...")
    converter.save(backup=args.backup, recursive=True)
    print("The new files are saved.")
    if args.remove_legacy:
        print("Cleaning legacy tim files ...")
        converter.clean()


if __name__ == "__main__":
    main()
