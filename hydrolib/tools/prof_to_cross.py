import argparse
import math
import re
import sys
from typing import Dict, List, Optional, Tuple

from hydrolib.core import __version__
from hydrolib.core.basemodel import PathOrStr
from hydrolib.core.dflowfm import FMModel
from hydrolib.core.dflowfm.crosssection.models import (
    CircleCrsDef,
    CrossDefModel,
    CrossLocModel,
    CrossSection,
    CrossSectionDefinition,
    RectangleCrsDef,
    XYZCrsDef,
    YZCrsDef,
)
from hydrolib.core.dflowfm.polyfile.models import PolyFile, PolyObject
from hydrolib.core.dflowfm.xyz.models import XYZModel

_program: str = "prof_to_cross"
_verbose: bool = False


def read_profloc_data(proflocfile: PathOrStr) -> XYZModel:
    """Read a legacy profile location file (.xyz) into a XYZModel object.

    Args:
        proflocfile (PathOrStr): path to the profile location file (.xyz)

    Returns:
        XYZModel: object with point list, z values are the profile numbers
        that refer to the profile definitions."""
    global _verbose

    loc_as_xyz = XYZModel(proflocfile)

    if _verbose:
        print(f"Read {len(loc_as_xyz.points)} profile locations from {proflocfile}.")

    return loc_as_xyz


def read_profdef_data(profdeffile: PathOrStr) -> List[Dict]:
    """Read a legacy profile definition file (.xyz).

    Args:
        profdeffile (PathOrStr): path to the profile definition file (.txt)

    Returns:
        List[Dict]: list of profile definitions, one per line in the file.
            Each line in the file is a list item, each definition is a dict.
    """
    defs = []
    linenr = 0
    with open(profdeffile) as file:
        for line in file:
            linenr = linenr + 1
            if line.startswith("*") or len(line.strip()) == 0:
                continue
            tokens = re.split(r"[=\s]+", line.strip())

            defs.append(dict(zip(tokens[::2], map(float, tokens[1::2]))))

            if "PROFNR" not in defs[-1]:
                raise ValueError(
                    f"Invalid profile definition in {profdeffile}, line {linenr}: missing PROFNR="
                )
            if "TYPE" not in defs[-1]:
                raise ValueError(
                    f"Invalid profile definition in {profdeffile}, line {linenr}: missing TYPE="
                )

            defs[-1]["PROFNR"] = int(defs[-1]["PROFNR"])
            defs[-1]["TYPE"] = int(defs[-1]["TYPE"])

    if _verbose:
        print(f"Read {len(defs)} profile definitions from {profdeffile}.")

    return defs


def read_profdefxyz_data(profdefxyzfile: PathOrStr) -> PolyFile:
    """Read a legacy profile definition file for type xyz (.pliz) into
    a PolyFile object.

    Args:
        profdefxyzfile (PathOrStr): path to the profile definition file (.pliz)

    Returns:
        PolyFile: entire contents of the .pliz file. Polyline names should be
            of the form "PROFNR=<N>", where profile numbers N refer to the
            profile definitions.
    """
    global _verbose

    profdefxyz = PolyFile(profdefxyzfile)

    if _verbose:
        print(
            f"Read {len(profdefxyz.objects)} xyz profile polylines from {profdefxyzfile}."
        )

    return profdefxyz


def _proftype_to_crsdeftype(proftype: int) -> Tuple[int, str]:
    """Convert legacy profdef file type numbers to crsdef.ini type string.

    Args:
        proftype (int): integer type as listed in TYPE=<N> field.
    Returns:
        Tuple[int, str]: Tuple of: 1) normalized proftype (ignoring conveyance
            type and closed-sign, possible values: 1, 2, 4, 6, 100, 200),
            and 2) string type that can directly be used in type=<type> field.
    """

    _proftype = abs(proftype)
    if _proftype >= 2:
        _proftype = math.floor(_proftype / 2.0) * 2

    if _proftype == 1:  # Pipe
        crstype = "circle"
    elif _proftype == 2:  # Rectangle
        crstype = "rectangle"
    elif _proftype == 4:  # V-shaped
        crstype = "yz"
    elif _proftype == 6:  # Trapezoid
        crstype = "yz"
    elif _proftype == 100:  # yz
        crstype = "yz"
    elif _proftype == 200:  # xyz
        crstype = "xyz"
    else:
        raise ValueError(f"Invalid legacy profile type given: TYPE={proftype}")

    return (_proftype, crstype)


def _proftype_to_conveyancetype(proftype: int) -> str:
    """Convert legacy profdef file type numbers to conveyance type string.
    Only applies to profile types that translate to yz type.

    Args:
        proftype (int): integer type as listed in TYPE=<N> field.
    Returns:
        str: string type that can directly be used in coveyance=<type> field.
            Return value is "segmented" for 1D analytic types, and "lumped"
            for area/hydr.radius types.
    """

    _proftype = abs(proftype)
    if 2 <= _proftype <= 201:
        if (_proftype % 2) == 0:
            convtype = "lumped"
        else:
            convtype = "segmented"
    else:
        raise ValueError(f"Invalid legacy profile type given: TYPE={proftype}")

    return convtype


def _frctp_to_frictiontype(frctp: int) -> str:
    """Convert legacy profdef friction type numbers to crsdef.ini frictionType string.

    Args:
        frctp (int): integer type as listed in FRCTP=<I> field.
    Returns:
        str: Equivalent frictionType string value for use in a crsdef.ini.
    """

    if frctp == 0:
        friction_type = "Chezy"
    elif frctp == 1:
        friction_type = "Manning"
    elif frctp == 2:
        friction_type = "WallLawNikuradse"
    elif frctp == 3:
        friction_type = "WhiteColebrook"
    else:
        raise ValueError(f"Invalid legacy profile friction type given: FRCTP={frctp}")

    return friction_type


def _crs_append_friction_definition(
    profdef: dict, crsvalues: dict, plural: bool = False
):
    """Append key-value pairs to a dict for a crsdef.ini-compatible friction
    definition.

    Caller must specify whether the specific CrossSectionDefinition subtype,
    for which this dict is intended, is expecting plural (list) friction input.


    Args:
        profdef (dict): the key-value pairs read from profdef.txt. Optional
            friction keywords are: FRCCF and FRCTP.
        crsvalues (dict): dict of CrossSectionDefinition fields, to which the
            friction fields will be appended (in place, function has no return
            value).
        plural (bool, optional): whether intended CrossSectionDefinition
            subtype is expecting plural/list-friction parameters or not.
            Defaults to: False.
    """
    prof_frccf = profdef.get("FRCCF")
    prof_frctp = profdef.get("FRCTP")

    if prof_frccf is None and prof_frctp is None:
        return

    if (prof_frccf is None) ^ (prof_frctp is None):
        raise ValueError(
            f"Missing friction input, FRCCF={prof_frccf}, FRCTP={prof_frctp} (both must be given)."
        )

    val_frctype = _frctp_to_frictiontype(prof_frctp)

    # Append input profile friction parameters to output crs values dict
    if plural:
        crsvalues.update(
            {"frictionValues": [prof_frccf], "frictionTypes": [val_frctype]}
        )
    else:
        crsvalues.update({"frictionValue": prof_frccf, "frictionType": val_frctype})


def _convert_pipe_definition(profdef: dict) -> dict:
    crsvalues = {"type": "circle", "diameter": profdef["WIDTH"]}
    return crsvalues


def _convert_rectangle_definition(profdef: dict) -> dict:
    crsvalues = {
        "type": "rectangle",
        "width": profdef["WIDTH"],
        "height": profdef.get("HEIGHT", 999),
        "closed": "yes" if profdef["TYPE"] < 0 else "no",
    }
    return crsvalues


def _convert_v_shape_definition(profdef: dict) -> dict:
    dy_talud = profdef["WIDTH"] / 2.0

    crsvalues = {
        "type": "yz",
        "yCoordinates": [0, dy_talud, profdef["WIDTH"]],
        "zCoordinates": [profdef["HEIGHT"], 0, profdef["HEIGHT"]],
        "yzCount": 3,
        "conveyance": _proftype_to_conveyancetype(profdef["TYPE"]),
    }
    return crsvalues


def _convert_trapezoid_definition(profdef: dict) -> dict:
    if (
        base := profdef.get("BASE") is None
        and (talud := profdef.get("TALUD")) is not None
    ):
        base = max(0, profdef["WIDTH"] - 2 * profdef["HEIGHT"] * talud)

    dy_talud = (profdef["WIDTH"] - base) / 2.0

    crsvalues = {
        "type": "yz",
        "yCoordinates": [0, dy_talud, dy_talud + base, profdef["WIDTH"]],
        "zCoordinates": [profdef["HEIGHT"], 0, 0, profdef["HEIGHT"]],
        "yzCount": 4,
        "conveyance": _proftype_to_conveyancetype(profdef["TYPE"]),
    }
    return crsvalues


def _convert_xyz_definition(profdef: dict, profdefxyz: PolyObject) -> dict:
    crsvalues = {
        "type": "xyz",
        "xCoordinates": [p.x for p in profdefxyz.points],
        "yCoordinates": [p.y for p in profdefxyz.points],
        "zCoordinates": [p.z for p in profdefxyz.points],
        "xyzCount": len(profdefxyz.points),
        "conveyance": _proftype_to_conveyancetype(profdef["TYPE"]),
    }
    return crsvalues


def convert_profdef(
    profdef: dict, profdefxyzfile: Optional[PolyFile] = None
) -> CrossSectionDefinition:
    """Convert a single profile definition, read as dict from a legacy
    profdef.txt file into a CrossSectionDefinition (sub)class.

    The resulting crosssection definition can be stored in the official
    .ini file format.

    Args:
        profdef (dict): the key-value pairs read from profdef.txt. Must
            contain several keys, depending on type, but at least:
            PROFNR, TYPE, WIDTH, and optionally: ZMIN, BASE, TALUD,
            FRCTP and FRCCF (all in uppercase).
        profdefxyzfile (Optional[PolyFile]): A PolyFile (.pliz) containing
            the x,y,z polyline points for all xyz profile definitions
            (i.e., type=200/201). Polyline label must equal "PROFNR=<N>",
            corresponding to the same labels in the profdef.txt file.

    Returns:
        CrossSectionDefinition: a cross section definition object, already
            of the correct subclass, depending on the type, e.g., YZCrsDef.

    Raises:
        ValueError: when profdef has a wrong profile type, or when xyz data
            is missing.
    """

    (proftype, crstype) = _proftype_to_crsdeftype(profdef.get("TYPE"))

    crsdata = {}
    if proftype == 1:
        crsdata = _convert_pipe_definition(profdef)
    elif proftype == 2:
        crsdata = _convert_rectangle_definition(profdef)
    elif proftype == 4:
        crsdata = _convert_v_shape_definition(profdef)
    elif proftype == 6:
        crsdata = _convert_trapezoid_definition(profdef)
    elif proftype == 100:
        raise ValueError(
            f"Type YZ found in input for PROFNR={profdef['PROFNR']}. Use XYZ instead."
        )
    elif proftype == 200:
        if profdefxyzfile is None:
            raise ValueError(
                f"Profdefxyzfile is missing. Required for xyz profile type (PROFNR={profdef['PROFNR']})."
            )

        # Find the single polyline object in profdefxyz file for this PROFNR
        polyobj = next(
            (
                polyobj
                for polyobj in profdefxyzfile.objects
                if polyobj.metadata.name == f"PROFNR={profdef['PROFNR']}"
            )
        )

        crsdata = _convert_xyz_definition(profdef, polyobj)

    _crs_append_friction_definition(
        profdef, crsdata, plural=(crstype == "yz" or crstype == "xyz")
    )

    crsdata["id"] = f"PROFNR{profdef['PROFNR']}"
    crsdata["type"] = crstype
    if crstype == "circle":
        crsdeftype = CircleCrsDef
    elif crstype == "rectangle":
        crsdeftype = RectangleCrsDef
    elif crstype == "yz":
        crsdeftype = YZCrsDef
    elif crstype == "xyz":
        crsdeftype = XYZCrsDef
    else:
        crsdeftype = CrossSectionDefinition

    crsdef = crsdeftype(**crsdata)

    return crsdef


def prof_to_cross_from_mdu(
    mdufile: PathOrStr,
    crslocfile: PathOrStr = None,
    crsdeffile: PathOrStr = None,
):
    """Wrapper converter function for converting legacy profile files
    into cross section .ini files, for files listed in an MDU file.

    Args:
        mdufile (PathOrStr): path to the D-Flow FM main input file (.mdu).
            Must be parsable into a standard FMModel.
            When this contains valid filenames for proflocfile, profdeffile
            and optionally profdefxyzfile, conversion will be performed.
        crslocfile (PathOrStr, optional): path to the output location file.
            Defaults to crsloc.ini in current working dir.
        crsdeffile (PathOrStr, optional): path to the output definition file.
            Defaults to crsdef.ini in current working dir.
    """
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

    prof_to_cross(proflocfile, profdeffile, profdefxyzfile, crslocfile, crsdeffile)


def prof_to_cross(
    proflocfile: PathOrStr,
    profdeffile: PathOrStr,
    profdefxyzfile: PathOrStr = None,
    crslocfile: PathOrStr = None,
    crsdeffile: PathOrStr = None,
):
    """The actual converter function for converting legacy profile files
    into cross section .ini files.

    Args:
        proflocfile (PathOrStr): path to the profile location file (.xyz).
            Must be parsable into a standard XYZModel.
        profdeffile (PathOrStr): path to the profile definition file (.txt)
            A free-formatted text value with space-separated key-value pairs.
        profdefxyzfile (PathOrStr, optional): path to the xyz profile
            geometry definition (.pliz). Must be parsable into a standard
            PolyFile, including z-values.
        crslocfile (PathOrStr, optional): path to the output location file.
            Defaults to crsloc.ini in current working dir.
        crsdeffile (PathOrStr, optional): path to the output definition file.
            Defaults to crsdef.ini in current working dir.
    """
    profloc_data = read_profloc_data(proflocfile)
    profdef_data = read_profdef_data(profdeffile)
    if profdefxyzfile:
        profdefxyz_data = read_profdefxyz_data(profdefxyzfile)
    else:
        profdefxyz_data = None

    crsloc_data = []
    crsdef_data = []

    # Part 1 of 2: crs location data
    crsloc_data = [
        CrossSection(
            id=f"PROFLOC{nr+1}",
            x=profloc.x,
            y=profloc.y,
            definitionid=f"PROFNR{int(profloc.z)}",
            shift=next(
                profdef.get("ZMIN")
                for profdef in profdef_data
                if profdef.get("PROFNR") == profloc.z
            ),
        )
        for nr, profloc in enumerate(profloc_data.points)
    ]

    crsloc_model = CrossLocModel(crosssection=crsloc_data)
    crsloc_model.filepath = crslocfile
    crsloc_model.save()

    # Part 2 of 2: crs definition data
    crsdef_data = [
        convert_profdef(profdef, profdefxyz_data) for profdef in profdef_data
    ]
    crsdef_model = CrossDefModel(definition=crsdef_data)
    crsdef_model.filepath = crsdeffile
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
        action="store",
        nargs="*",
        metavar="PROFFILE",
        help="2 or 3 profile files: PROFLOCFILE PROFDEFFILE [PROFDEFXYZFILE]",
    )
    parser.add_argument(
        "--outfiles",
        "-o",
        action="store",
        nargs=2,
        metavar=("CRSLOCFILE", "CRSDEFFILE"),
        help="save cross section locations and definitions to specified filenames",
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

    outfiles = {"crslocfile": None, "crsdeffile": None}
    if args.outfiles is not None:
        outfiles["crslocfile"] = args.outfiles[0]
        outfiles["crsdeffile"] = args.outfiles[1]

    if args.mdufile is not None:
        prof_to_cross_from_mdu(args.mdufile, **outfiles)
    elif args.proffiles is not None:
        prof_to_cross(*args.proffiles, **outfiles)
    else:
        print("Error: Missing input file(s), use either -m or -p.")

        sys.exit(1)

    print(_program + ": done")


if __name__ == "__main__":
    main()
