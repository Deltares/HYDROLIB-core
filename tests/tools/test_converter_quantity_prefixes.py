from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.dflowfm.ext.models import Boundary, Spatial
from hydrolib.core.dflowfm.extold.models import ALL_PREFIXES, ExtOldForcing
from hydrolib.core.dflowfm.mba.models import MassBalanceArea
from hydrolib.tools.extforce_convert.converters import (
    BoundaryConditionConverter,
    ConverterFactory,
    MassBalanceAreaConverter,
    SpatialConverter,
)
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


BOUNDARY_PREFIXES = ["sedfracbnd", "tracerbnd"]
SPATIAL_PREFIXES = [
    "initialsedfrac",
    "initialtracer",
    "initialverticalsedfracprofile",
    "initialverticalsigmasedfracprofile",
    "initialwaqbot",
    "initialsediment",
    "waqfunction",
    "waqsegmentfunction",
    "waqsegmentnumber",
    "waqparameter",
]
MASS_BALANCE_AREA_PREFIXES = ["waqmassbalancearea", "massbalancearea"]


class TestQuantityPrefixConversion:
    def test_conversion_cases_cover_all_quantity_prefixes(self):
        assert set(BOUNDARY_PREFIXES + SPATIAL_PREFIXES + MASS_BALANCE_AREA_PREFIXES) == set(
            ALL_PREFIXES
        )

    @pytest.fixture
    def mdu_parser(self):
        parser = MagicMock(spec=MDUParser)
        parser.temperature_salinity_data = {"refdate": "minutes since 2015-01-01 00:00:00"}
        return parser

    @pytest.mark.parametrize("prefix", BOUNDARY_PREFIXES)
    def test_convert_boundary_prefix(
        self, prefix, input_files_dir: Path, mdu_parser
    ):
        quantity = f"{prefix}SomeName"
        root = input_files_dir / "boundary-conditions"
        forcing = ExtOldForcing(
            quantity=quantity,
            filename=root / "tfl_01.pli",
            filetype=9,
            method=3,
            operand="override",
        )
        converter = ConverterFactory.create_converter(
            forcing.quantity, root_dir=root, mdu_parser=mdu_parser
        )
        assert isinstance(converter, BoundaryConditionConverter)
        result = converter.convert(forcing)
        assert isinstance(result, Boundary)

    @pytest.mark.parametrize("prefix", SPATIAL_PREFIXES)
    def test_convert_spatial_prefix(self, prefix, mdu_parser):
        quantity = f"{prefix}SomeName"
        forcing = ExtOldForcing(
            quantity=quantity, filename="data.xyz", filetype=7, method=5, operand="override"
        )
        converter = ConverterFactory.create_converter(forcing.quantity, mdu_parser=mdu_parser)
        assert isinstance(converter, SpatialConverter)
        result = converter.convert(forcing, forcing.filename.filepath)
        assert isinstance(result, Spatial)
        assert result.quantity == quantity
        assert result.datafile.filepath == Path("data.xyz")

    @pytest.mark.parametrize("prefix", MASS_BALANCE_AREA_PREFIXES)
    def test_convert_mass_balance_area_prefix(self, prefix, mdu_parser):
        forcing = ExtOldForcing(
            quantity=f"{prefix}SomeName",
            filename="area.pol",
            filetype=7,
            method=5,
            operand="override",
        )
        converter = ConverterFactory.create_converter(forcing.quantity, mdu_parser=mdu_parser)
        assert isinstance(converter, MassBalanceAreaConverter)
        result = converter.convert(forcing)
        assert isinstance(result, MassBalanceArea)
        assert result.name == "SomeName"
        assert result.locationfile.filepath == Path("area.pol")
