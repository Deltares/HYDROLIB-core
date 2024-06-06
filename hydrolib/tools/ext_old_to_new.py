import argparse
import math
import os
import re
import sys
from typing import Dict, List, Literal, Optional, Tuple

from pydantic import Extra

from hydrolib.core import __version__
from hydrolib.core.basemodel import PathOrStr
from hydrolib.core.dflowfm import FMModel
from hydrolib.core.dflowfm.ext.models import ExtModel, Meteo, MeteoForcingFileType
from hydrolib.core.dflowfm.extold.models import *
from hydrolib.core.dflowfm.inifield.models import AveragingType, InterpolationMethod
from hydrolib.core.dflowfm.mdu.legacy import LegacyFMModel
from hydrolib.core.dflowfm.mdu.models import General

# from hydrolib.core.dflowfm.polyfile.models import PolyFile, PolyObject
# from hydrolib.core.dflowfm.xyz.models import XYZModel

_program: str = "ext_old_to_new"
_verbose: bool = False


def read_extold_data(extoldfile: PathOrStr) -> ExtOldModel:
    """Read a legacy D-Flow FM external forcings file (.ext) into an
       ExtOldModel object.

    Args:
        extoldfile (PathOrStr): path to the external forcings file (.ext)

    Returns:
        ExtOldModel: object with all forcing blocks."""
    global _verbose

    extold_model = ExtOldModel(extoldfile)

    if _verbose:
        print(f"Read {len(extold_model.forcing)} forcing blocks from {extoldfile}.")

    return extold_model


def _oldfiletype_to_forcing_file_type(
    oldfiletype: int,
) -> Union[MeteoForcingFileType, str]:
    """Convert old external forcing `FILETYPE` integer value to valid
        `forcingFileType` string value.

    Args:
        oldfiletype (int): The FILETYPE value in an old external forcings file.

    Returns:
        Union[MeteoForcingFileType,str]: Corresponding value for `forcingFileType`,
            or "unknown" for invalid input.
    """

    if oldfiletype == 1:
        forcing_file_type = MeteoForcingFileType.uniform
    elif oldfiletype == 2:
        forcing_file_type = MeteoForcingFileType.unimagdir
    elif oldfiletype == 4:
        forcing_file_type = MeteoForcingFileType.meteogridequi
    elif oldfiletype == 5:
        forcing_file_type = MeteoForcingFileType.spiderweb
    elif oldfiletype == 6:
        forcing_file_type = MeteoForcingFileType.meteogridcurvi
    elif oldfiletype == 9:
        forcing_file_type = MeteoForcingFileType.meteogridcurvi
    else:
        forcing_file_type = "unknown"

    return forcing_file_type


def _oldmethod_to_interpolation_method(
    oldmethod: int,
) -> Union[InterpolationMethod, str]:
    """Convert old external forcing `METHOD` integer value to valid
        `interpolationMethod` string value.

    Args:
        oldmethod (int): The METHOD value in an old external forcings file.

    Returns:
        Union[InterpolationMethod,str]: Corresponding value for `interpolationMethod`,
            or "unknown" for invalid input.
    """

    if oldmethod in [1, 2, 3, 5]:
        interpolation_method = InterpolationMethod.triangulation
    elif oldmethod == 4:
        interpolation_method = InterpolationMethod.constant
    elif oldmethod in range(6, 10):
        interpolation_method = InterpolationMethod.averaging
    else:
        interpolation_method = "unknown"


def _oldmethod_to_averaging_type(
    oldmethod: int,
) -> Union[AveragingType, str]:
    """Convert old external forcing `METHOD` integer value to valid
        `averagingType` string value.

    Args:
        oldmethod (int): The METHOD value in an old external forcings file.

    Returns:
        Union[AveragingType,str]: Corresponding value for `averagingType`,
            or "unknown" for invalid input.
    """

    if oldmethod == 6:
        averaging_type = AveragingType.mean
    else:
        interpolation_method = "unknown"


def ext_old_to_new(
    extoldfile: PathOrStr,
    extfile: PathOrStr = None,
    inifieldfile: PathOrStr = None,
    structurefile: PathOrStr = None,
):

    if _verbose:
        workdir = os.getcwd() + "\\"
        print(f"Work dir: {workdir}")
        print("Using attribute files:")
        print("Input:")
        print(f"* {extoldfile}")
        print("Output:")
        print(f"* {extfile}")
        print(f"* {inifieldfile}")
        print(f"* {structurefile}")

    # TODO: isolate this in helper function
    extold_model = ExtOldModel(extoldfile)

    ext_model = ExtModel()
    ext_model.filepath = extfile

    i_meteo = 0  # TODO: remove hardcoding
    meteo_data = {}
    meteo_data["quantity"] = extold_model.forcing[i_meteo].quantity
    meteo_data["forcingfile"] = extold_model.forcing[i_meteo].filename
    meteo_data["forcingfiletype"] = _oldfiletype_to_forcing_file_type(
        extold_model.forcing[i_meteo].filetype
    )
    # TODO: varname
    # TODO: sourcemask
    meteo_data["interpolationmethod"] = _oldmethod_to_interpolation_method(
        extold_model.forcing[i_meteo].method
    )
    if meteo_data["interpolationmethod"] == InterpolationMethod.averaging:
        meteo_data["averagingtype"] = _oldmethod_to_averaging_type(
            extold_model.forcing[i_meteo].method
        )
        meteo_data["averagingrelsize"] = extold_model.forcing[
            i_meteo
        ].relativesearchcellsize
        meteo_data["averagingnummin"] = extold_model.forcing[i_meteo].nummin
        meteo_data["averagingpercentile"] = extold_model.forcing[
            i_meteo
        ].percentileminmax

    # TODO: meteo_data["extrapolationallowed"] = extold_model.forcing[i_meteo].extrapolation_method
    # TODO: maxsearchradius -> extrapolationSearchRadius

    meteo_data["operand"] = extold_model.forcing[i_meteo].operand
    meteo_block = Meteo(**meteo_data)
    ext_model.meteo.append(meteo_block)
    ext_model.save()
    print(meteo_block)


def ext_old_to_new_from_mdu(
    mdufile: PathOrStr,
    extfile: PathOrStr = "forcings.ext",
    inifieldfile: PathOrStr = "inifields.ini",
    structurefile: PathOrStr = "structures.ini",
):
    """Wrapper converter function for converting legacy external forcings
    files into cross section .ini files, for files listed in an MDU file.

    Args:
        mdufile (PathOrStr): path to the D-Flow FM main input file (.mdu).
            Must be parsable into a standard FMModel.
            When this contains a valid filename for ExtFile, conversion
            will be performed.
        extfile (PathOrStr, optional): path to the output external forcings file.
            Defaults to the given ExtForceFileNew in the MDU file, if present,
            or forcings.ext otherwise.
        inifieldfile (PathOrStr, optional): path to the output initial field file.
            Defaults to the given IniFieldFile in the MDU file, if present,
            or inifields.ini otherwise.
        structurefile (PathOrStr, optional): path to the output structures.ini file.
            Defaults to the given StructureFile in the MDU file, if present,
            or structures.ini otherwise.
    """
    global _verbose

    # For flexibility, also accept legacy MDU file versions (which does not
    # external forcings functionailty anyway):
    fmmodel = LegacyFMModel(mdufile, recurse=False)
    workdir = fmmodel._resolved_filepath.parent
    os.chdir(workdir)

    # Input file:
    extoldfile = fmmodel.external_forcing.extforcefile._resolved_filepath
    # Output files:
    extfile = (
        fmmodel.external_forcing.extforcefilenew._resolved_filepath
        if fmmodel.external_forcing.extforcefilenew
        else workdir / extfile
    )
    inifieldfile = (
        fmmodel.geometry.inifieldfile._resolved_filepath
        if fmmodel.geometry.inifieldfile
        else workdir / inifieldfile
    )
    structurefile = (
        fmmodel.geometry.structurefile[0]._resolved_filepath
        if fmmodel.geometry.structurefile
        else workdir / structurefile
    )

    ext_old_to_new(extoldfile, extfile, inifieldfile, structurefile)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_program,
        description="Convert D-Flow FM legacy external forcings files to current external forcings file/initial fields file/structures file.",
    )

    parser.add_argument("--version", "-v", action="version", version=__version__)
    parser.add_argument(
        "--verbose", action="store_true", help="also print diagnostic information"
    )
    parser.add_argument(
        "--mdufile",
        "-m",
        action="store",
        help="automatically take input and output filenames from MDUFILE",
    )
    parser.add_argument(
        "--extoldfile",
        "-e",
        action="store",
        help="Input EXTOLDFILE to be converted.",
    )
    parser.add_argument(
        "--outfiles",
        "-o",
        action="store",
        nargs=3,
        metavar=("EXTFILE", "INIFIELDFILE", "STRUCTUREFILE"),
        help="save forcings, initial fields and structures to specified filenames",
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
    global _verbose

    parser = _get_parser()
    args = parser.parse_args(args)
    _verbose = args.verbose

    if args.mdufile is not None and args.extoldfile is not None:
        print("Error: use either input MDUFILE or EXTOLDFILE, not both.")
        sys.exit(1)
    ...

    outfiles = {"extfile": None, "inifieldfile": None, "structurefile": None}
    if args.outfiles is not None:
        outfiles["extfile"] = args.outfiles[0]
        outfiles["inifieldfile"] = args.outfiles[1]
        outfiles["structurefile"] = args.outfiles[2]

    if args.mdufile is not None:
        ext_old_to_new_from_mdu(args.mdufile, **outfiles)
    elif args.extoldfile is not None:
        ext_old_to_new(args.extoldfile, **outfiles)
    else:
        print("Error: Missing input file(s), use either -m or -e.")

    #     sys.exit(1)

    print(_program + ": done")


if __name__ == "__main__":
    main()
