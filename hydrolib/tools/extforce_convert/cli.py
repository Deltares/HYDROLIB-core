import argparse
from argparse import ArgumentTypeError
from pathlib import Path

from hydrolib.core import __version__
from hydrolib.tools.extforce_convert.main_converter import (
    ExternalForcingConverter,
    recursive_converter,
)


def valid_file(path_str):
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
    """
    Main entry point for extforce_convert tool.
    Args:
        args : list
            A of arguments as if they were input in the command line. Leave it
            None to use sys.argv.
    """
    parser = _get_parser()
    args = parser.parse_args(args)
    backup = args.backup

    # three cases to consider
    if args.mdufile:
        # mdu file is given
        converter = ExternalForcingConverter.from_mdu(
            args.mdufile,
            ext_file=(args.outfiles[0] if args.outfiles else None),
            inifield_file=(args.outfiles[1] if args.outfiles else "inifields.ini"),
            structure_file=(args.outfiles[2] if args.outfiles else "structures.ini"),
            suppress_errors=True,
        )
        converter.verbose = args.verbose
        converter.update()
        print(
            "Converting the old external forcing file to the new format files is done."
        )
        converter.save(backup=backup)
        print("The new files are saved.")

        if args.remove_legacy:
            print("Cleaning legacy tim files ...")
            converter.clean()

    elif args.extoldfile is not None:
        # extold file is given
        converter = ExternalForcingConverter(
            args.extoldfile,
            ext_file=(args.outfiles[0] if args.outfiles else None),
            inifield_file=(args.outfiles[1] if args.outfiles else "inifields.ini"),
            structure_file=(args.outfiles[2] if args.outfiles else "structures.ini"),
        )
        converter.verbose = args.verbose
        converter.update()
        print(
            "Converting the old external forcing file to the new format files is done."
        )
        converter.save(backup=backup)
        print("The new files are saved.")
        if args.remove_legacy:
            print("Cleaning legacy tim files ...")
            converter.clean()
    elif args.dir is not None:
        recursive_converter(args.dir, backup=backup, remove_legacy=args.remove_legacy)
    else:
        print("Error: no input specified. Use one of --mdufile, --extoldfile or --dir.")


if __name__ == "__main__":
    main()
