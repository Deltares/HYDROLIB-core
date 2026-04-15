"""Tests for the BubbleScreen INI block model.

Covers construction and validation (``__init__`` + field/model validators),
the ``is_intermediate_link`` method, round-trip serialization via
``ExtModel.save``/``load``, and integration with the enclosing ``ExtModel``
container. Organised per API surface so each test class targets a single
method or behavior of the model.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import BubbleScreen, ExtModel


@pytest.fixture(scope="function")
def inline_block_kwargs() -> dict:
    """Provide kwargs for a valid inline-coordinate BubbleScreen.

    Returns:
        dict: Field kwargs with four polygon vertices, ``zLevel=-5.0``, and a
        scalar ``discharge``. Safe to spread with ``**`` into ``BubbleScreen(...)``.
    """
    return {
        "id": "bubbles1",
        "numcoordinates": 4,
        "xcoordinates": [450.0, 450.0, 550.0, 550.0],
        "ycoordinates": [550.0, 650.0, 650.0, 550.0],
        "zlevel": -5.0,
        "discharge": 1.0,
    }


@pytest.fixture(scope="function")
def locationfile_block_kwargs() -> dict:
    """Provide kwargs for a valid locationFile-style BubbleScreen.

    Returns:
        dict: Field kwargs with a ``.pli`` ``locationFile``, ``zLevel=-5.0``,
        and a scalar ``discharge``. Safe to spread with ``**`` into
        ``BubbleScreen(...)``.
    """
    return {
        "id": "bubbles1",
        "locationfile": DiskOnlyFileModel(filepath=Path("simple_bubbles.pli")),
        "zlevel": -5.0,
        "discharge": 1.0,
    }


class TestBubbleScreenInit:
    """Tests for ``BubbleScreen.__init__`` construction and field validators.

    In Pydantic v2 the ``__init__`` entrypoint runs every field/model validator
    (``split_coordinates``, ``resolve_forcing_reference``,
    ``validate_location_specification``, ``validate_locationfile``), so
    construction scenarios are the right surface to exercise them.
    """

    def test_init_with_inline_coordinates(self, inline_block_kwargs):
        """Construct with inline ``numCoordinates`` + ``xCoordinates`` + ``yCoordinates``.

        Args:
            inline_block_kwargs: Fixture with valid inline-coordinate kwargs.

        Test scenario:
            A polygon with four vertices, a single ``zLevel``, and a scalar
            discharge is a valid BubbleScreen. All supplied fields round-trip
            onto the model with the same values.
        """
        block = BubbleScreen(**inline_block_kwargs)

        assert block.id == "bubbles1", f"id not preserved: {block.id}"
        assert block.numcoordinates == 4, (
            f"numcoordinates not preserved: {block.numcoordinates}"
        )
        assert block.xcoordinates == [450.0, 450.0, 550.0, 550.0], (
            f"xcoordinates not preserved: {block.xcoordinates}"
        )
        assert block.ycoordinates == [550.0, 650.0, 650.0, 550.0], (
            f"ycoordinates not preserved: {block.ycoordinates}"
        )
        assert block.zlevel == -5.0, f"zlevel not preserved: {block.zlevel}"

    def test_init_with_locationfile(self, locationfile_block_kwargs):
        """Construct with ``locationFile`` instead of inline coordinates.

        Args:
            locationfile_block_kwargs: Fixture with a ``.pli`` locationFile.

        Test scenario:
            Location can alternatively be specified via a ``.pli`` file;
            inline coord fields remain ``None`` in that case.
        """
        block = BubbleScreen(**locationfile_block_kwargs)

        assert block.id == "bubbles1", f"id not preserved: {block.id}"
        assert block.zlevel == -5.0, f"zlevel not preserved: {block.zlevel}"
        assert block.numcoordinates is None, (
            f"numcoordinates should be None with locationFile, "
            f"got: {block.numcoordinates}"
        )
        assert block.locationfile.filepath == Path("simple_bubbles.pli"), (
            f"locationfile path not preserved: {block.locationfile.filepath}"
        )

    def test_init_name_defaults_to_empty_string(self, inline_block_kwargs):
        """Optional ``name`` field defaults to empty string when omitted.

        Args:
            inline_block_kwargs: Fixture providing a valid base block.

        Test scenario:
            ``BubbleScreen`` mirrors ``SourceSink.name`` with a default of
            ``""`` so the field is never ``None`` in serialised output.
        """
        block = BubbleScreen(**inline_block_kwargs)

        assert block.name == "", f"name should default to '', got: {block.name!r}"

    def test_init_split_coordinates_parses_whitespace_string(self):
        """The ``split_coordinates`` field validator handles space-separated strings.

        Test scenario:
            When ``ExtModel`` parses an INI file, the parser yields
            ``xCoordinates`` as a single string like ``"450 450 550 550"``.
            The validator must split this into a ``list[float]``.
        """
        block = BubbleScreen(
            id="bubbles1",
            numcoordinates=4,
            xcoordinates="450 450 550 550",
            ycoordinates="550 650 650 550",
            zlevel=-5.0,
            discharge=1.0,
        )

        assert block.xcoordinates == [450.0, 450.0, 550.0, 550.0], (
            f"xcoordinates string not split correctly: {block.xcoordinates}"
        )
        assert block.ycoordinates == [550.0, 650.0, 650.0, 550.0], (
            f"ycoordinates string not split correctly: {block.ycoordinates}"
        )

    def test_init_resolve_forcing_reference_accepts_scalar(
        self, inline_block_kwargs
    ):
        """The ``resolve_forcing_reference`` validator accepts a scalar discharge.

        Args:
            inline_block_kwargs: Fixture providing a valid base block.

        Test scenario:
            A ``float`` discharge is kept as-is (no .bc resolution needed).
        """
        block = BubbleScreen(**inline_block_kwargs)

        assert block.discharge == 1.0, (
            f"scalar discharge not preserved: {block.discharge}"
        )

    def test_init_resolve_forcing_reference_accepts_numeric_string(
        self, inline_block_kwargs
    ):
        """The ``resolve_forcing_reference`` validator parses a numeric string.

        Args:
            inline_block_kwargs: Fixture providing a valid base block.

        Test scenario:
            When parsed from INI, ``discharge = 1.5`` arrives as a string.
            The validator must coerce it to a float.
        """
        kwargs = {**inline_block_kwargs, "discharge": "1.5"}
        block = BubbleScreen(**kwargs)

        assert block.discharge == 1.5, (
            f"string discharge not coerced to float: {block.discharge}"
        )

    def test_init_without_location_raises(self):
        """``validate_location_specification`` raises when neither location style is given.

        Test scenario:
            A BubbleScreen with no ``locationFile`` *and* no inline
            coordinates is ambiguous. The validator must reject it with an
            error message mentioning both accepted forms.
        """
        with pytest.raises(
            (ValidationError, ValueError),
            match=r"locationFile.*or.*numCoordinates",
        ) as exc_info:
            BubbleScreen(id="bubbles1", zlevel=-5.0, discharge=1.0)

        assert "bubbles1" in str(exc_info.value), (
            f"error should mention block id 'bubbles1', got: {exc_info.value}"
        )

    @pytest.mark.parametrize(
        "xcoordinates, ycoordinates, numcoordinates, scenario",
        [
            ([450.0, 450.0], [550.0, 650.0, 650.0, 550.0], 4, "x shorter than y"),
            ([450.0, 450.0, 550.0, 550.0], [550.0, 650.0], 4, "y shorter than x"),
            (
                [450.0, 450.0, 550.0],
                [550.0, 650.0, 650.0],
                4,
                "matched x/y but wrong numcoordinates",
            ),
        ],
    )
    def test_init_mismatched_coordinate_counts_raise(
        self, xcoordinates, ycoordinates, numcoordinates, scenario
    ):
        """``validate_location_specification`` enforces coordinate-count consistency.

        Args:
            xcoordinates: The x-array to supply.
            ycoordinates: The y-array to supply.
            numcoordinates: The declared coordinate count.
            scenario: Human-readable description of the mismatch kind.

        Test scenario:
            Any of x-length, y-length, or ``numCoordinates`` disagreeing must
            be rejected. Three parametrised sub-scenarios cover
            under-/over-specified x, under-specified y, and a wrong
            ``numCoordinates`` count.
        """
        with pytest.raises((ValidationError, ValueError)):
            BubbleScreen(
                id="bubbles1",
                numcoordinates=numcoordinates,
                xcoordinates=xcoordinates,
                ycoordinates=ycoordinates,
                zlevel=-5.0,
                discharge=1.0,
            )

    def test_init_missing_zlevel_raises(self):
        """``zLevel`` is a required field with no default.

        Test scenario:
            Omitting ``zLevel`` must raise ``ValidationError`` — unlike
            ``SourceSink.zSource`` which is optional, BubbleScreen's vertical
            placement is always explicit.
        """
        with pytest.raises(ValidationError) as exc_info:
            BubbleScreen(
                id="bubbles1",
                numcoordinates=1,
                xcoordinates=[0.0],
                ycoordinates=[0.0],
                discharge=1.0,
            )

        assert "zLevel" in str(exc_info.value) or "zlevel" in str(exc_info.value), (
            f"error should mention zLevel, got: {exc_info.value}"
        )

    def test_init_missing_discharge_raises(self):
        """``discharge`` is a required field with no default.

        Test scenario:
            Omitting ``discharge`` must raise ``ValidationError`` — a
            BubbleScreen without a discharge value has no physical meaning.
        """
        with pytest.raises(ValidationError) as exc_info:
            BubbleScreen(
                id="bubbles1",
                numcoordinates=1,
                xcoordinates=[0.0],
                ycoordinates=[0.0],
                zlevel=-5.0,
            )

        assert "discharge" in str(exc_info.value), (
            f"error should mention discharge, got: {exc_info.value}"
        )

    def test_init_accepts_camelcase_aliases_from_dict(self):
        """Pydantic aliases accept the INI CamelCase names when constructing from a dict.

        Test scenario:
            INI keys like ``numCoordinates``/``xCoordinates``/``zLevel`` arrive
            verbatim from the parser; the model must accept those alongside
            the lowercase Python attribute names.
        """
        block = BubbleScreen.model_validate(
            {
                "id": "bubbles1",
                "numCoordinates": 1,
                "xCoordinates": [0.0],
                "yCoordinates": [0.0],
                "zLevel": -5.0,
                "discharge": 1.0,
            }
        )

        assert block.numcoordinates == 1, (
            f"numCoordinates alias not accepted: {block.numcoordinates}"
        )
        assert block.zlevel == -5.0, f"zLevel alias not accepted: {block.zlevel}"


class TestBubbleScreenIsIntermediateLink:
    """Tests for ``BubbleScreen.is_intermediate_link``."""

    def test_is_intermediate_link_returns_true(self, inline_block_kwargs):
        """``is_intermediate_link`` always reports the block participates in file resolution.

        Args:
            inline_block_kwargs: Fixture providing a valid base block.

        Test scenario:
            ``BubbleScreen`` references external resources via ``locationFile``
            / ``.bc`` files, so the framework must descend into it during save.
        """
        block = BubbleScreen(**inline_block_kwargs)

        assert block.is_intermediate_link() is True, (
            f"is_intermediate_link should return True, got: "
            f"{block.is_intermediate_link()}"
        )


class TestBubbleScreenSerialization:
    """Tests for ``ExtModel.save`` + re-load round-trip of BubbleScreen blocks."""

    def test_save_roundtrip_preserves_inline_block(
        self, tmp_path: Path, inline_block_kwargs
    ):
        """An inline-coordinate block round-trips with all fields intact.

        Args:
            tmp_path: pytest-provided temporary directory.
            inline_block_kwargs: Fixture with valid inline-coordinate kwargs.

        Test scenario:
            Writing an ``ExtModel`` containing a single inline BubbleScreen
            and reading it back yields an equivalent block — id, zLevel, and
            all four x/y vertices match.
        """
        block = BubbleScreen(**inline_block_kwargs)
        model = ExtModel(bubblescreen=[block])
        out_path = tmp_path / "out.ext"
        model.filepath = out_path
        model.save()

        reread = ExtModel(out_path)

        assert len(reread.bubblescreen) == 1, (
            f"expected exactly one BubbleScreen after reload, "
            f"got: {len(reread.bubblescreen)}"
        )
        reloaded = reread.bubblescreen[0]
        assert reloaded.id == "bubbles1", f"id not preserved: {reloaded.id}"
        assert reloaded.zlevel == -5.0, f"zlevel not preserved: {reloaded.zlevel}"
        assert list(reloaded.xcoordinates) == [450.0, 450.0, 550.0, 550.0], (
            f"xcoordinates not preserved: {reloaded.xcoordinates}"
        )
        assert list(reloaded.ycoordinates) == [550.0, 650.0, 650.0, 550.0], (
            f"ycoordinates not preserved: {reloaded.ycoordinates}"
        )

    def test_save_roundtrip_preserves_locationfile_block(
        self, tmp_path: Path, locationfile_block_kwargs
    ):
        """A locationFile block round-trips without being rewritten to inline form.

        Args:
            tmp_path: pytest-provided temporary directory.
            locationfile_block_kwargs: Fixture with a ``.pli`` locationFile.

        Test scenario:
            HYDROLIB-core must preserve whichever location style was supplied,
            so a ``locationFile``-style block stays ``locationFile``-style
            after save and reload.
        """
        block = BubbleScreen(**locationfile_block_kwargs)
        model = ExtModel(bubblescreen=[block])
        out_path = tmp_path / "out.ext"
        model.filepath = out_path
        model.save()

        reread = ExtModel(out_path)

        assert len(reread.bubblescreen) == 1, (
            f"expected exactly one BubbleScreen after reload, "
            f"got: {len(reread.bubblescreen)}"
        )
        assert reread.bubblescreen[0].zlevel == -5.0, (
            f"zlevel not preserved: {reread.bubblescreen[0].zlevel}"
        )


class TestBubbleScreenInExtModel:
    """Tests for the ``ExtModel.bubblescreen`` container field and INI parsing."""

    def test_extmodel_bubblescreen_defaults_to_empty_list(self):
        """A fresh ``ExtModel`` reports no bubble screens rather than ``None``.

        Test scenario:
            ``ExtModel.bubblescreen`` is a ``List[BubbleScreen]`` with
            ``default_factory=list``; consumers should be able to iterate
            over it unconditionally.
        """
        model = ExtModel()

        assert model.bubblescreen == [], (
            f"fresh ExtModel.bubblescreen should default to [], "
            f"got: {model.bubblescreen}"
        )

    def test_extmodel_parses_bubblescreen_block_from_ini(self, tmp_path: Path):
        """A ``[BubbleScreen]`` section in an on-disk ext file is parsed into the model.

        Args:
            tmp_path: pytest-provided temporary directory.

        Test scenario:
            Writing a minimal INI file with a single ``[BubbleScreen]`` block
            and loading via ``ExtModel(path)`` populates ``bubblescreen`` with
            one entry whose fields match the INI values.
        """
        ext_content = (
            "[General]\n"
            "fileVersion = 2.01\n"
            "fileType = extForce\n"
            "\n"
            "[BubbleScreen]\n"
            "id = bubbles1\n"
            "numCoordinates = 4\n"
            "xCoordinates = 450 450 550 550\n"
            "yCoordinates = 550 650 650 550\n"
            "zLevel = -5.0\n"
            "discharge = 1.0\n"
        )
        ext_file = tmp_path / "bubbles.ext"
        ext_file.write_text(ext_content)

        model = ExtModel(ext_file)

        assert len(model.bubblescreen) == 1, (
            f"expected exactly one BubbleScreen, "
            f"got: {len(model.bubblescreen)}"
        )
        assert model.bubblescreen[0].id == "bubbles1", (
            f"id not parsed: {model.bubblescreen[0].id}"
        )
        assert model.bubblescreen[0].zlevel == -5.0, (
            f"zlevel not parsed: {model.bubblescreen[0].zlevel}"
        )
        assert model.bubblescreen[0].numcoordinates == 4, (
            f"numcoordinates not parsed: {model.bubblescreen[0].numcoordinates}"
        )


class TestBubbleScreenPublicAPI:
    """Tests that ``BubbleScreen`` is reachable via the package's public API."""

    def test_bubblescreen_is_exported_from_ext_package(self):
        """``BubbleScreen`` is re-exported from ``hydrolib.core.dflowfm.ext``.

        Test scenario:
            Public consumers should be able to
            ``from hydrolib.core.dflowfm.ext import BubbleScreen`` without
            reaching into the internal ``.models`` submodule.
        """
        from hydrolib.core.dflowfm.ext import BubbleScreen as BS

        assert BS is BubbleScreen, (
            f"exported BubbleScreen is not the same class as ext.models.BubbleScreen"
        )
