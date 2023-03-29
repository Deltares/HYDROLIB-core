import argparse
import re
import sys
from typing import Dict, List

from hydrolib.core import __version__
from hydrolib.core.basemodel import PathOrStr
from hydrolib.core.dflowfm import FMModel
from hydrolib.core.dflowfm.crosssection.models import (
    CrossDefModel,
    CrossLocModel,
    CrossSection,
)
from hydrolib.core.dflowfm.xyz.models import XYZModel

_program: str = "prof_to_cross"
_verbose: bool = False


def read_profloc_data(proflocfile: PathOrStr) -> XYZModel:
    global _verbose

    loc_as_xyz = XYZModel(proflocfile)

    if _verbose:
        print(f"Read {len(loc_as_xyz.points)} profile locations from {proflocfile}.")

    return loc_as_xyz


def read_profdef_data(profdeffile: PathOrStr) -> List[Dict]:
    defs = []
    linenr = 0
    with open(profdeffile) as file:
        for line in file:
            linenr = linenr + 1
            if line.startswith("*"):
                continue
            tokens = re.split("[=\s]+", line.strip())
            defs.append(dict(zip(tokens[::2], map(float, tokens[1::2]))))

    if _verbose:
        print(f"Read {len(defs)} profile definitions from {profdeffile}.")

    return defs


def prof_to_cross_from_mdu(mdufile: PathOrStr):
    global _verbose

    fmmodel = FMModel(mdufile, recurse=False)
    proflocfile = fmmodel.geometry.proflocfile._resolved_filepath
    profdeffile = fmmodel.geometry.profdeffile._resolved_filepath
    profdefxyzfile = fmmodel.geometry.profdefxyzfile._resolved_filepath
    if _verbose:
        print("Using profile files found in MDU:")
        print(f"* {proflocfile}")
        print(f"* {profdeffile}")
        if profdefxyzfile:
            print(f"* {profdefxyzfile}")

    prof_to_cross(proflocfile, profdeffile, profdefxyzfile)


def prof_to_cross(
    proflocfile: PathOrStr,
    profdeffile: PathOrStr,
    profdefxyzfile: PathOrStr = None,
):
    print(proflocfile)
    print(profdeffile)
    print(profdefxyzfile)

    profloc_data = read_profloc_data(proflocfile)
    # print(profloc_data.points)
    profdef_data = read_profdef_data(profdeffile)
    # print(profdef_data)

    crsloc_data = []
    crsdef_data = []

    crsloc_data = [
        CrossSection(
            id=f"PROFLOC{nr+1}",
            x=profloc.x,
            y=profloc.y,
            definitionId=f"PROFNR{int(profloc.z)}",
        )
        for nr, profloc in enumerate(profloc_data.points)
    ]

    # print(crsloc_data)

    crsloc_model = CrossLocModel(crosssection=crsloc_data)
    crsloc_model.filepath = "crsloc.ini"
    crsloc_model.save()

    crsdef_model = CrossDefModel(definition=crsdef_data)
    crsdef_model.filepath = "crsdef.ini"
    crsdef_model.save()


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_program,
        description="Convert D-Flow FM legacy profile files to cross section files.",
    )

    parser.add_argument("--version", "-v", action="version", version=__version__)
    parser.add_argument(
        "--verbose", action="store_true", help="also print diagnostic information"
    )
    parser.add_argument(
        "--mdufile",
        "-m",
        action="store",
        help="automatically take profile filenames from MDUFILE",
    )
    parser.add_argument(
        "--proffiles",
        "-p",
        action="extend",
        nargs="*",
        metavar="PROFFILE",
        help="2 or 3 profile files: PROFLOCFILE PROFDEFFILE [PROFDEFXYZFILE]",
    )
    return parser


def main(args=None):
    """
    Main entry point for prof_to_cross tool.
    Args:
        args : list
            A of arguments as if they were input in the command line. Leave it
            None to use sys.argv.
    """
    global _verbose

    parser = _get_parser()
    args = parser.parse_args(args)
    _verbose = args.verbose

    if args.mdufile is not None and args.proffiles:
        print("Error: use either input MDUFILE or PROFFILEs, not both.")
        sys.exit(1)

    if args.proffiles is not None and not 2 <= len(args.proffiles) <= 3:
        print("Error: Expecting at least 2, at most 3 profile files,")
        print("       use: -p PROFLOCFILE PROFDEFFILE [PROFDEFXYZFILE]")

        sys.exit(1)

    if args.mdufile is not None:
        prof_to_cross_from_mdu(args.mdufile)
    elif args.proffiles is not None:
        prof_to_cross(*args.proffiles)
    else:
        print("Error: Missing input file(s), use either -m or -p.")

        sys.exit(1)

    print(_program + ": done")


if __name__ == "__main__":
    main()
