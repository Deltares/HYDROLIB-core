import argparse
import math
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

from pydantic import Extra, FilePath

from hydrolib.core import __version__
from hydrolib.core.basemodel import PathOrStr
from hydrolib.core.dflowfm import FMModel
from hydrolib.core.dflowfm.ext.models import ExtModel, Meteo, MeteoForcingFileType, MeteoInterpolationMethod
from hydrolib.core.dflowfm.extold.models import *
from hydrolib.core.dflowfm.inifield.models import AveragingType, InterpolationMethod
from hydrolib.core.dflowfm.mdu.legacy import LegacyFMModel
from hydrolib.core.dflowfm.mdu.models import General

# from hydrolib.core.dflowfm.polyfile.models import PolyFile, PolyObject
# from hydrolib.core.dflowfm.xyz.models import XYZModel

_program: str = "ext_old_to_new"
_verbose: bool = False

def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True    

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
    elif oldfiletype == 11:
        forcing_file_type = MeteoForcingFileType.netcdf
    else:
        forcing_file_type = "unknown"

    return forcing_file_type


def _oldmethod_to_interpolation_method(
    oldmethod: int,
) -> Union[InterpolationMethod, MeteoInterpolationMethod, str]:
    """Convert old external forcing `METHOD` integer value to valid
        `interpolationMethod` string value.

    Args:
        oldmethod (int): The METHOD value in an old external forcings file.

    Returns:
        Union[InterpolationMethod,str]: Corresponding value for `interpolationMethod`,
            or "unknown" for invalid input.
    """

    if oldmethod in [1, 2, 3, 11]:
        interpolation_method = MeteoInterpolationMethod.linearSpaceTime
    elif oldmethod == 5: 
        interpolation_method = InterpolationMethod.triangulation
    elif oldmethod == 4:
        interpolation_method = InterpolationMethod.constant
    elif oldmethod in range(6, 10):
        interpolation_method = InterpolationMethod.averaging
    else:
        interpolation_method = "unknown"
    return interpolation_method

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
    try:
        extold_model = ExtOldModel(extoldfile)
    except Exception as error:
        print("The old external forcing file contained invalid input:", error)
        return
    
    ext_model = ExtModel()
    ext_model.filepath = extfile

    for forcing in extold_model.forcing:
        if __contains__(ExtOldMeteoQuantity,forcing.quantity):
            meteo_data = {}
            meteo_data["quantity"] = forcing.quantity 
            meteo_data["forcingfile"] = forcing.filename
            meteo_data["forcingfiletype"] = _oldfiletype_to_forcing_file_type(forcing.filetype)
            meteo_data["forcingVariableName"] = forcing.varname
            meteo_data["sourceMaskFile"] = forcing.sourcemask
            meteo_data["interpolationmethod"] = _oldmethod_to_interpolation_method(forcing.method)
            if meteo_data["interpolationmethod"] == InterpolationMethod.averaging:
                meteo_data["averagingtype"] = _oldmethod_to_averaging_type(forcing.method)
                meteo_data["averagingrelsize"] = forcing.relativesearchcellsize
                meteo_data["averagingnummin"] = forcing.nummin
                meteo_data["averagingpercentile"] = forcing.percentileminmax

            meteo_data["extrapolationAllowed"] = bool(forcing.extrapolation_method)
            meteo_data["extrapolationSearchRadius"] = forcing.maxsearchradius
            meteo_data["operand"] = forcing.operand

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
    if fmmodel.external_forcing.extforcefile is None:
        if _verbose:
            print(f"mdufile: {mdufile} does not contain an old style external forcing file")
            return
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
    try: 
        ExtModel(extfile)
        newmdufile: PathOrStr = fmmodel.filepath.stem + "_new" + ".mdu"
        newmdufile = workdir / newmdufile
        fmmodel.filepath = FilePath(newmdufile)
        fmmodel.external_forcing.extforcefile = None
        fmmodel.external_forcing.extforcefilenew = extfile
        fmmodel.save()
        if _verbose:
                print(f"succesfully saved converted file {newmdufile} ")
    except Exception as error:
        print("The converter did not produce a valid ext file:", error)
        return

def ext_old_to_new_dir_recursive(
    dir: PathOrStr,
):
    
    for path in Path(dir).rglob('*.mdu'):
        if "_ext" not in path.name:
            ext_old_to_new_from_mdu(path)    
    
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
        "--dir",
        "-d",
        action="store",
        help="Folder to recursively convert .mdufiles in",
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
    elif args.dir is not None:
        ext_old_to_new_dir_recursive(args.dir)
    else:
        ext_old_to_new_dir_recursive(os.getcwd())

    #     sys.exit(1)

    print(_program + ": done")


if __name__ == "__main__":
    main()
