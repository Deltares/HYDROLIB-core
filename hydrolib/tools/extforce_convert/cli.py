"""CLI.

CLI for converting D-Flow FM legacy external forcings files to current external forcings file/initial
fields file/structures file.
"""

import argparse
from argparse import ArgumentTypeError, Namespace
from pathlib import Path

from hydrolib.core import __version__
from hydrolib.tools.extforce_convert.main_converter import (
    ExternalForcingConverter,
    recursive_converter,
)


def valid_file(path_str):
    """Check if the file exists, has a .mdu extension, and return its path."""
    path = Path(path_str)
    if not str(path).lower().endswith(".mdu"):
        raise ArgumentTypeError(f"File must have a .mdu extension: {path}")

    if not path.exists():
        raise ArgumentTypeError(f"File not found: {path}")
    return path


def _validator(path_str, extension):
    """Validate that the file exists and has the given extension."""
    path = Path(path_str)
    if not path.exists():
        raise ArgumentTypeError(f"File not found: {path}")
    if not str(path).lower().endswith(extension):
        raise ArgumentTypeError(f"File must have a {extension} extension: {path}")
    return path


def valid_file_with_extension(extension):
    """Create a validator for files with a specific extension for argparse."""
    return lambda path_str: _validator(path_str, extension)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extforce_convert",
        description="Convert D-Flow FM legacy external forcings files to current external forcings file/initial fields file/structures file.",
    )

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print diagnostic information"
    )

    # mdu file, extforcefile and dir are mutually exclusive (can only use one)
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--mdufile",
        "-m",
        action="store",
        type=valid_file_with_extension(".mdu"),
        help="Automatically take input and output filenames from MDUFILE",
    )
    group.add_argument(
        "--extoldfile",
        "-e",
        action="store",
        type=valid_file_with_extension(".ext"),
        help="Input EXTOLDFILE to be converted.",
    )
    group.add_argument(
        "--dir",
        "-d",
        action="store",
        help="Directory to recursively find and convert .mdu files in",
    )

    parser.add_argument(
        "--outfiles",
        "-o",
        action="store",
        nargs=3,
        metavar=("EXTFILE", "INIFIELDFILE", "STRUCTUREFILE"),
        help="Save forcings, initial fields and structures to specified filenames",
    )

    backup_group = parser.add_mutually_exclusive_group()

    backup_group.add_argument(
        "--backup",
        "-b",
        action="store_true",
        default=True,
        help="Create a backup of each file that will be overwritten.",
    )
    backup_group.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Do not create a backup of each file that will be overwritten.",
    )

    parser.add_argument(
        "--remove-legacy-files",
        dest="remove_legacy",
        action="store_true",
        default=False,
        help="Remove legacy/old files (e.g. .tim) after conversion. Defaults to False.",
    )
    return parser


def main(args=None):
    """
    Entry point for extforce_convert tool.

    CLI argument combinations:

    Required (mutually exclusive, pick one):
      --mdufile MDUFILE         Use MDUFILE to determine input/output files automatically.
      --extoldfile EXTOLDFILE   Convert a specific legacy external forcing file.
      --dir DIR                 Recursively find and convert all .mdu files in DIR.

    Optional:
      --outfiles EXTFILE INIFIELDFILE STRUCTUREFILE
                              Specify output filenames for forcings, initial fields, and structures (only with --mdufile or --extoldfile).
      --backup / --no-backup   Create (default) or skip creating a backup of overwritten files (mutually exclusive).
      --remove-legacy-files    Remove legacy/old files (e.g. .tim) after conversion.
      --verbose, -v            Print diagnostic information.
      --version                Print version and exit.

    Example usages:
      extforce_convert --mdufile model.mdu
      extforce_convert --extoldfile old.ext --outfiles new.ext new.ini new.str
      extforce_convert --dir ./models --no-backup --remove-legacy-files
    """
    parser = _get_parser()
    args = parser.parse_args(args)

    # three cases to consider
    if args.mdufile:
        convert_with_mdu_file(args)
    elif args.extoldfile is not None:
        convert_with_extold_file(args)
    elif args.dir is not None:
        recursive_converter(
            args.dir, backup=args.backup, remove_legacy=args.remove_legacy
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
