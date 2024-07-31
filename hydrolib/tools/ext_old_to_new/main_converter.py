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
from hydrolib.core.dflowfm.ext.models import (
    Boundary,
    ExtModel,
    Lateral,
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import *
from hydrolib.core.dflowfm.inifield.models import (
    AveragingType,
    DataFileType,
    IniFieldModel,
    InitialField,
    InterpolationMethod,
    ParameterField,
)
from hydrolib.core.dflowfm.mdu.legacy import LegacyFMModel
from hydrolib.core.dflowfm.mdu.models import General
from hydrolib.core.dflowfm.structure.models import Structure, StructureModel

from .converter_factory import ConverterFactory
from .utils import construct_filemodel_new_or_existing

_program: str = "ext_old_to_new"
_verbose: bool = False


def _read_ext_old_data(extoldfile: PathOrStr) -> ExtOldModel:
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


def ext_old_to_new(
    extoldfile: PathOrStr,
    extfile: PathOrStr = None,
    inifieldfile: PathOrStr = None,
    structurefile: PathOrStr = None,
):
    """
    Convert old external forcing file to new format files.
    When the output files are existing, output will be appended to them.

    Args:
        extoldfile (PathOrStr): Path to the old external forcing file.
        extfile (PathOrStr, optional): Path to the new external forcing file.
        inifieldfile (PathOrStr, optional): Path to the initial field file.
        structurefile (PathOrStr, optional): Path to the structure file.
    """

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

    try:
        extold_model = _read_ext_old_data(extoldfile)
    except Exception as error:
        print("The old external forcing file could not be read:", error)
        return

    ext_model = construct_filemodel_new_or_existing(ExtModel, extfile)
    inifield_model = construct_filemodel_new_or_existing(IniFieldModel, inifieldfile)
    structure_model = construct_filemodel_new_or_existing(StructureModel, structurefile)

    for forcing in extold_model.forcing:
        try:
            converter_class = ConverterFactory.create_converter(forcing.quantity)
            new_quantity_block = converter_class.convert(forcing)
        except ValueError:
            # While this tool is in progress, accept that we do not convert all quantities yet.
            new_quantity_block = None

        if isinstance(new_quantity_block, Boundary):
            ext_model.boundary.append(new_quantity_block)
        elif isinstance(new_quantity_block, Lateral):
            ext_model.lateral.append(new_quantity_block)
        elif isinstance(new_quantity_block, Meteo):
            ext_model.meteo.append(new_quantity_block)
        elif isinstance(new_quantity_block, InitialField):
            inifield_model.initial.append(new_quantity_block)
        elif isinstance(new_quantity_block, ParameterField):
            inifield_model.parameter.append(new_quantity_block)
        elif isinstance(new_quantity_block, Structure):
            structure_model.structure.append(new_quantity_block)
        else:
            raise NotImplementedError(
                f"Unsupported model class {type(new_quantity_block)} for {forcing.quantity} in {extoldfile}."
            )

        print(new_quantity_block)
    ext_model.save()


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
            print(
                f"mdufile: {mdufile} does not contain an old style external forcing file"
            )
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

    for path in Path(dir).rglob("*.mdu"):
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
