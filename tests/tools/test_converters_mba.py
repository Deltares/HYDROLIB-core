from pathlib import Path
from types import SimpleNamespace

from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.core.dflowfm.mba.models import MassBalanceArea
from hydrolib.tools.extforce_convert.converters import (
    ConverterFactory,
    MassBalanceAreaConverter,
    SpatialConverter,
)
from hydrolib.tools.extforce_convert.utils import CONVERTER_DATA


def _make_forcing(quantity: str, filename: str) -> SimpleNamespace:
    """Build a lightweight stub matching the ExtOldForcing attributes the converter reads.

    Phase 4 registers the `waqmassbalancearea` prefix so a real ExtOldForcing accepts the
    quantity; until then this stub keeps the converter test independent of that routing work.
    """
    return SimpleNamespace(
        quantity=quantity,
        filename=SimpleNamespace(filepath=Path(filename)),
    )


class TestMassBalanceAreaConverter:
    def test_convert_waq_prefix(self):
        """Test that a waqmassbalancearea<name> quantity converts correctly.

        Test scenario:
            The area name is the suffix after the prefix, the polygon comes from
            FILENAME, and VALUE is ignored.
        """
        forcing = _make_forcing("waqmassbalanceareaEstruaryWest", "EstruaryWest.pol")

        result = MassBalanceAreaConverter().convert(forcing)

        assert isinstance(result, MassBalanceArea), f"Got {type(result)}"
        assert result.name == "EstruaryWest", f"Got {result.name}"
        assert result.locationfile.filepath == Path(
            "EstruaryWest.pol"
        ), f"Got {result.locationfile.filepath}"

    def test_convert_plain_prefix(self):
        """Test that a plain massbalancearea<name> quantity converts correctly.

        Test scenario:
            The converter also accepts the non-waq spelling used by UNST-10107.
        """
        forcing = _make_forcing("massbalanceareaRiver", "River.pol")

        result = MassBalanceAreaConverter().convert(forcing)

        assert result.name == "River", f"Got {result.name}"
        assert result.locationfile.filepath == Path("River.pol")

    def test_convert_preserves_name_case(self):
        """Test that the suffix casing is preserved while the prefix match is case-insensitive.

        Test scenario:
            An upper-cased prefix still strips, and the mixed-case name survives.
        """
        forcing = _make_forcing(
            "WAQMASSBALANCEAREAHarbourAntwerp", "HarbourAntwerp.pol"
        )

        result = MassBalanceAreaConverter().convert(forcing)

        assert result.name == "HarbourAntwerp", f"Got {result.name}"

    def test_strip_prefix_longest_first(self):
        """Test that the waq prefix is matched before the plain prefix.

        Test scenario:
            A waqmassbalancearea quantity must strip the full 'waqmassbalancearea'
            prefix, not the shorter 'massbalancearea' substring.
        """
        assert (
            MassBalanceAreaConverter._strip_prefix("waqmassbalanceareaA") == "A"
        ), "waq prefix should strip fully"
        assert (
            MassBalanceAreaConverter._strip_prefix("massbalanceareaB") == "B"
        ), "plain prefix should strip fully"


class TestMassBalanceAreaRouting:
    """Phase 4: quantity recognition (extold) and factory routing."""

    def test_extold_recognizes_waq_prefix(self):
        """Test that the old-ext quantity validator accepts waqmassbalancearea<name>.

        Test scenario:
            validate_quantity_prefix returns the full quantity (prefix + name) once
            the mass balance area prefix is registered in ALL_PREFIXES.
        """
        result = ExtOldForcing.validate_quantity_prefix(
            "waqmassbalanceareaestruarywest", "waqmassbalanceareaEstruaryWest"
        )
        assert result == "waqmassbalanceareaEstruaryWest", f"Got {result}"

    def test_extold_recognizes_plain_prefix(self):
        """Test that the plain massbalancearea<name> spelling is also accepted."""
        result = ExtOldForcing.validate_quantity_prefix(
            "massbalanceareariver", "massbalanceareaRiver"
        )
        assert result == "massbalanceareaRiver", f"Got {result}"

    def test_factory_routes_waq_prefix_to_mba_converter(self):
        """Test that the factory routes waqmassbalancearea<name> to the MBA converter."""
        converter = ConverterFactory.create_converter("waqmassbalanceareaEstruaryWest")
        assert isinstance(converter, MassBalanceAreaConverter), f"Got {type(converter)}"

    def test_factory_routes_plain_prefix_to_mba_converter(self):
        """Test that the factory routes plain massbalancearea<name> to the MBA converter."""
        converter = ConverterFactory.create_converter("massbalanceareaRiver")
        assert isinstance(converter, MassBalanceAreaConverter), f"Got {type(converter)}"

    def test_factory_does_not_route_spatial_quantity_to_mba(self):
        """Test that a non-mba spatial quantity is unaffected by the new branch."""
        converter = ConverterFactory.create_converter("frictioncoefficient")
        assert isinstance(converter, SpatialConverter), f"Got {type(converter)}"

    def test_quantity_no_longer_unsupported(self):
        """Test that the mass balance area quantity is no longer flagged unsupported."""
        unsupported = CONVERTER_DATA.external_forcing.find_unsupported(
            ["waqmassbalanceareaestruarywest"]
        )
        assert unsupported == set(), f"Expected supported, got {unsupported}"
