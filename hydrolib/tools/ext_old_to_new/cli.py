import argparse

from hydrolib.core import __version__
from hydrolib.tools.ext_old_to_new.main_converter import (
    ExternalForcingConverter,
    ext_old_to_new_dir_recursive,
)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ext_old_to_new",
        description="Convert D-Flow FM legacy external forcings files to current external forcings file/initial fields file/structures file.",
    )

    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print diagnostic information"
    )
    parser.add_argument(
        "--mdufile",
        "-m",
        action="store",
        help="Automatically take input and output filenames from MDUFILE",
    )
    parser.add_argument(
        "--extoldfile",
        "-e",
        action="store",
        help="Input EXTOLDFILE to be converted.",
    )
    parser.add_argument(
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

    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        default=True,
        help="Create a backup of each file that will be overwritten.",
    )
    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Do not create a backup of each file that will be overwritten.",
    )
    return parser


def main(args=None):
    """
    Main entry point for ext_old_to_new tool.
    Args:
        args : list
            A of arguments as if they were input in the command line. Leave it
            None to use sys.argv.
    """
    parser = _get_parser()
    args = parser.parse_args(args)
    backup = args.backup

    if args.mdufile is not None and args.extoldfile is not None:
        raise ValueError("Error: use either input MDUFILE or EXTOLDFILE, not both.")

    outfiles = {
        "ext_file": None,
        "inifield_file": "inifields.ini",
        "structure_file": "structures.ini",
    }
    if args.outfiles is not None:
        outfiles["ext_file"] = args.outfiles[0]
        outfiles["inifield_file"] = args.outfiles[1]
        outfiles["structure_file"] = args.outfiles[2]

    if args.mdufile is not None:
        converter = ExternalForcingConverter.from_mdu(
            args.mdufile, **outfiles, suppress_errors=True
        )
        converter.verbose = args.verbose
        converter.update()
        converter.save(backup=backup)
    elif args.extoldfile is not None:
        converter = ExternalForcingConverter(
            args.extoldfile,
            outfiles["ext_file"],
            outfiles["inifield_file"],
            outfiles["structure_file"],
        )
        converter.update()
        converter.save(backup=backup)
    elif args.dir is not None:
        ext_old_to_new_dir_recursive(args.dir, backup=backup)
    else:
        print("Error: no input specified. Use one of --mdufile, --extoldfile or --dir.")


if __name__ == "__main__":
    main()
