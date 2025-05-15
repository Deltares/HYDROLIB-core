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
    """Check if the file exists and return its path."""
    path = Path(path_str)
    if not path.exists():
        raise ArgumentTypeError(f"File not found: {path}")
    return path


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
        type=valid_file,
        help="Automatically take input and output filenames from MDUFILE",
    )
    group.add_argument(
        "--extoldfile",
        "-e",
        action="store",
        type=valid_file,
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
    """Entry point for extforce_convert tool.

    Args:
        args : list
            A of arguments as if they were input in the command line. Leave it
            None to use sys.argv.
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
        ext_file=(args.outfiles[0] if args.outfiles else None),
        inifield_file=(args.outfiles[1] if args.outfiles else None),
        structure_file=(args.outfiles[2] if args.outfiles else None),
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
    converter.save(backup=args.backup)
    print("The new files are saved.")
    if args.remove_legacy:
        print("Cleaning legacy tim files ...")
        converter.clean()


if __name__ == "__main__":
    main()
