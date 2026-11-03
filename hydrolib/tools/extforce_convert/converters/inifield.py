import warnings
import os
from typing import Any
from pathlib import Path
from pydantic import ValidationError
from hydrolib.core.dflowfm.ext.models import ExtModel, Spatial
from hydrolib.core.dflowfm.inifield.models import AbstractSpatialField, IniFieldModel, DataFileType, InterpolationMethod
from hydrolib.tools.extforce_convert.mdu_parser import INIFIELD_FILE_LINE
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser
from hydrolib.tools.extforce_convert.converters.converters import SpatialConverter
from hydrolib.core.base.models import DiskOnlyFileModel

__all__ = [
    "InifieldToSpatialConverter",
    "InifieldError",
]

class InifieldError(Exception):
    """The inifield file of the MDU could not be read, so it cannot be converted.

    Raised by `ExternalForcingConverter` when the inifield file exists but `IniFieldModel` cannot parse it. The
    message names the file.

    Examples:
        - Read the message of the error:
            ```python
            >>> from hydrolib.tools.extforce_convert.converters.inifield import InifieldError
            >>> error = InifieldError("The inifield file 'inifield.ini' could not be read")
            >>> str(error)
            "The inifield file 'inifield.ini' could not be read"

            ```
        - Catch it like any other exception:
            ```python
            >>> from hydrolib.tools.extforce_convert.converters.inifield import InifieldError
            >>> try:
            ...     raise InifieldError("The inifield file 'a.ini' could not be read")
            ... except InifieldError as error:
            ...     print(error)
            The inifield file 'a.ini' could not be read

            ```

    See Also:
        InifieldToSpatialConverter: Converts the blocks of an inifield file that could be read.
    """


class InifieldToSpatialConverter:
    """Convert an inifield `[Initial]` / `[Parameter]` block to a `[Spatial]` block.

    The inifield file is deprecated: its blocks move to the `[Spatial]` blocks of the new external forcings
    file (UNST-9273). `Spatial` is a superset of the inifield blocks, so every keyword of
    `AbstractSpatialField` has a counterpart; only the keywords that were explicitly set in the source block
    are copied, so the converted block does not gain defaults the source did not write.

    Keyword changes:

    - `extrapolationMethod` becomes `extrapolationAllowed`.
    - A polygon block with a `value` becomes `dataValue` + `targetMaskFile=<*.pol>` +
      `interpolationMethod=constant` (the polygon `dataFileType` is discouraged for "inside polygon" data).
    - A polygon block without a `value` (e.g. `initialverticalsalinityprofile`) keeps `dataFile` and
      `dataFileType=polygon`.
    - The legacy single-character `operand` values were already parsed into their word form on read.

    Examples:
        - Convert a gridded block; only the keywords set in the inifield are written:
            ```python
            >>> from pathlib import Path
            >>> from hydrolib.core.dflowfm.inifield.models import ParameterField
            >>> from hydrolib.tools.extforce_convert.converters.inifield import InifieldToSpatialConverter
            >>> block = ParameterField(
            ...     quantity="frictionCoefficient",
            ...     dataFile="friction.xyz",
            ...     dataFileType="sample",
            ...     interpolationMethod="triangulation",
            ...     operand="+",
            ... )
            >>> spatial = InifieldToSpatialConverter().convert(block, Path("friction.xyz"))
            >>> spatial.quantity, spatial.datafile.filepath.name
            ('frictionCoefficient', 'friction.xyz')
            >>> print(spatial.operand)
            add
            >>> sorted(spatial.model_fields_set)
            ['datafile', 'datafiletype', 'interpolationmethod', 'operand', 'quantity']

            ```
        - Convert a polygon with a value to the `dataValue` form:
            ```python
            >>> from pathlib import Path
            >>> from hydrolib.core.dflowfm.inifield.models import InitialField
            >>> from hydrolib.tools.extforce_convert.converters.inifield import InifieldToSpatialConverter
            >>> block = InitialField(
            ...     quantity="waterlevel",
            ...     dataFile="region.pol",
            ...     dataFileType="polygon",
            ...     interpolationMethod="constant",
            ...     value=1.5,
            ... )
            >>> spatial = InifieldToSpatialConverter().convert(block, Path("region.pol"))
            >>> spatial.datavalue, spatial.targetmaskfile.filepath.name
            (1.5, 'region.pol')
            >>> print(spatial.interpolationmethod)
            constant
            >>> print(spatial.datafile)
            None

            ```

    See Also:
        SpatialConverter: Converts the quantities of the old external forcings file to `[Spatial]` blocks.
    """

    # inifield attribute -> Spatial attribute, for the keywords copied when they were set in the source block
    KEYWORD_MAP = {
        "datafiletype": "datafiletype",
        "interpolationmethod": "interpolationmethod",
        "operand": "operand",
        "averagingtype": "averagingtype",
        "averagingrelsize": "averagingrelsize",
        "averagingnummin": "averagingnummin",
        "averagingpercentile": "averagingpercentile",
        "extrapolationmethod": "extrapolationallowed",
        "locationtype": "locationtype",
        "tracerfallvelocity": "tracerfallvelocity",
        "tracerdecaytime": "tracerdecaytime",
    }

    # quantity prefixes of the tracers / sediment fractions defined as `[Spatial]` and as `[Boundary]` blocks
    SPATIAL_TRACER_PREFIXES = ("initialtracer", "initialsedfrac")
    BOUNDARY_TRACER_PREFIXES = ("tracerbnd", "sedfracbnd")

    def __init__(self, mdu_parser: MDUParser | None = None):
        """Initialize the converter.

        Args:
            mdu_parser (MDUParser, optional):
                Parser of the MDU file that references the inifield file. Only needed to convert the whole
                inifield file (`convert_file`, `tracer_quantities`); converting a single block with `convert`
                does not need it.

        Attributes:
            unconverted_quantities (list[str]): Quantities of the converted blocks whose `value` has no
                counterpart in the `[Spatial]` block and was therefore dropped.
            legacy_files (list[Path]): The inifield file, once it is converted and may be removed with the
                legacy files; empty otherwise.
        """
        self.mdu_parser = mdu_parser
        self.unconverted_quantities: list[str] = []
        self.legacy_files: list[Path] = []
        self._model: IniFieldModel | None = None
        self._loaded = False
        self._converted = False
        self._tracer_order_warned = False
        self._blocks: list[Spatial] = []

    @property
    def converted(self) -> bool:
        """Whether the inifield file was found and converted by `convert_file`."""
        return self._converted

    @property
    def model(self) -> IniFieldModel | None:
        """The inifield model of the MDU, loaded on first use and cached.

        Returns:
            IniFieldModel | None: The model, or None when the MDU references no inifield file on disk.

        Raises:
            InifieldError: If the inifield file exists but cannot be read.
            ValueError: If the converter has no `mdu_parser`.
        """
        if not self._loaded:
            self._model = self._load_model()
            self._loaded = True
        return self._model

    def tracer_quantities(self) -> list[str]:
        """Collect the quantity names of the `[Initial]` and `[Parameter]` blocks of the inifield file.

        All quantities are returned, not only the tracer ones: the source/sink converter keeps the
        tracer / sediment-fraction ones by prefix.

        Returns:
            list[str]: Quantity names of the inifield blocks in the order of the file; empty when the MDU
                references no inifield file.
        """
        model = self.model
        blocks = model.blocks_in_file_order() if model else []
        return [block.quantity for block in blocks]

    def convert_file(self, ext_path: Path) -> list[Spatial]:
        """Convert all blocks of the inifield file to `[Spatial]` blocks, in the order of the file.

        The caller puts the blocks **in front of** the `[Spatial]` blocks of the new external forcings file,
        which is the order in which the kernel reads its sources (inifield, new ext, old ext). After the call
        `legacy_files` holds the inifield file, unless it is outside the MDU directory, a symbolic link, or has
        a `value` that could not be converted; a warning says so then.

        Args:
            ext_path (Path): The new external forcings file the blocks are written to; data file paths are
                made relative to it when the MDU has `pathsRelativeToParent`.

        Returns:
            list[Spatial]: The converted blocks; empty when the MDU has no inifield file or it was converted
                before.

        Raises:
            InifieldError: If the inifield file exists but cannot be read.
            ValueError: If the converter has no `mdu_parser`.
        """
        model = self.model
        blocks: list[Spatial] = []
        if model is not None and not self._converted:
            blocks = [
                self.convert(block, self._data_path(block, model, ext_path))
                for block in model.blocks_in_file_order()
            ]
            self._blocks = blocks
            self._converted = True
            problem = self._legacy_file_problem(Path(model.filepath))
            if self.unconverted_quantities:
                warnings.warn(
                    f"The inifield file '{model.filepath}' is not removed when the legacy files are cleaned: "
                    f"the value of {', '.join(self.unconverted_quantities)} was not converted.",
                    UserWarning,
                    stacklevel=4,
                )
            elif problem is not None:
                warnings.warn(
                    f"The inifield file '{model.filepath}' is {problem}, so it is not removed when the legacy "
                    "files are cleaned.",
                    UserWarning,
                    stacklevel=4,
                )
            else:
                self.legacy_files = [Path(model.filepath)]
        return blocks

    def prepend_to(self, ext_model: ExtModel) -> list[Path]:
        """Convert the inifield file and put its blocks in front of the `[Spatial]` blocks of `ext_model`.

        The blocks go **in front of** the `[Spatial]` blocks already in the new external forcings file, which
        are in front of the blocks converted from the old external forcings file. That is the order in which
        the kernel reads its sources (inifield, new ext, old ext), so blocks for the same quantity combine as
        before, and the tracer numbering follows the same precedence.

        Args:
            ext_model (ExtModel): The new external forcings model; its `spatial` list is extended in place.

        Returns:
            list[Path]: The inifield files that may be removed with the legacy files; empty when the MDU has no
                inifield file, when it cannot be removed, or when it was converted by an earlier call.

        Raises:
            InifieldError: If the inifield file exists but cannot be read.
            ValueError: If the converter has no `mdu_parser`.
        """
        was_converted = self._converted
        blocks = self.convert_file(ext_model.filepath)
        if self._converted and not was_converted:
            ext_model.spatial = blocks + list(ext_model.spatial)
        return [] if was_converted else list(self.legacy_files)

    def warn_on_tracer_order(self, boundary_quantities: list[str]) -> None:
        """Warn when inifield tracers end up behind the `[Boundary]` tracers of the new external forcings file.

        The kernel numbers the tracers in the order it meets them: inifield first, then the new external
        forcings file, then the old one. The `[Spatial]` blocks made from the inifield file are written after
        all `[Boundary]` blocks, so an inifield tracer (`initialtracer*`, `initialsedfrac*`) can come after a
        `[Boundary]` tracer (`tracerbnd*`, `sedfracbnd*`) and the tracers may then be numbered in another order.
        The warning is given once.

        Args:
            boundary_quantities (list[str]): Quantity names of the `[Boundary]` blocks of the new external
                forcings file.
        """
        spatial_tracers = [
            block.quantity
            for block in self._blocks
            if block.quantity.lower().startswith(self.SPATIAL_TRACER_PREFIXES)
        ]
        boundary_tracers = [
            quantity
            for quantity in boundary_quantities
            if quantity.lower().startswith(self.BOUNDARY_TRACER_PREFIXES)
        ]
        if spatial_tracers and boundary_tracers and not self._tracer_order_warned:
            self._tracer_order_warned = True
            warnings.warn(
                f"The inifield tracer(s) {', '.join(spatial_tracers)} were moved into [Spatial] blocks, which "
                f"are written after the [Boundary] blocks. The new external forcings file also has the "
                f"[Boundary] tracer(s) {', '.join(boundary_tracers)}, so D-Flow FM may number the tracers in a "
                "different order than before (inifield, new ext, old ext). Check the tracer order in the "
                "diagnostics (.dia) file.",
                UserWarning,
                stacklevel=3,
            )

    def _load_model(self) -> IniFieldModel | None:
        """Load the inifield file referenced by the MDU, if it exists on disk."""
        if self.mdu_parser is None:
            raise ValueError("Converting an inifield file needs an MDUParser.")
        model = None
        if self.mdu_parser.has_inifield_file():
            inifield_path = self.mdu_parser.get_inifield_file(None)
            if inifield_path is not None and Path(inifield_path).is_file():
                try:
                    model = IniFieldModel(filepath=inifield_path, recurse=False)
                    self._check_has_sections(Path(inifield_path))
                except (ValidationError, ValueError, TypeError) as error:
                    raise InifieldError(
                        f"The inifield file '{inifield_path}' could not be read, so it cannot be converted "
                        f"to [Spatial] blocks: {error}"
                    ) from error
        return model

    @staticmethod
    def _check_has_sections(inifield_path: Path) -> None:
        """Raise a `ValueError` when a non-empty inifield file has no `[section]` header.

        The ini parser reads such a file as an empty one, so it would be converted to nothing and then
        removed.
        """
        lines = [
            line.strip()
            for line in inifield_path.read_text(errors="replace").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if lines and not any(line.startswith("[") for line in lines):
            raise ValueError("the file has content but no [section] header")

    def _data_path(
            self, block: AbstractSpatialField, model: IniFieldModel, ext_path: Path
    ) -> Path:
        """Resolve the data file path of an inifield block for the new external forcings file.

        With the MDU setting `pathsRelativeToParent` a relative path is relative to the file it is written
        in, so it is re-expressed relative to the new external forcings file. Otherwise paths are relative to
        the MDU and stay as they are.
        """
        path = block.datafile.filepath
        if path is not None and not path.is_absolute() and self.mdu_parser.is_relative_to_parent:
            absolute = (model.filepath.parent / path).resolve()
            try:
                path = Path(os.path.relpath(absolute, ext_path.parent.resolve()))
            except ValueError:
                # no relative path exists between two drives (Windows)
                path = absolute
        return path

    def _legacy_file_problem(self, inifield_path: Path) -> str | None:
        """Say why the converted inifield file must not be removed with the legacy files, if so.

        The path comes from the MDU file, so a file outside the MDU directory (a file shared with other
        models) or a symbolic link is never removed. The link check looks at the path as written in the MDU,
        and at every folder between the MDU directory and the file, because the resolved path has no links
        left.

        Returns:
            str | None: The reason, or None when the file may be removed.
        """
        mdu_dir = Path(os.path.abspath(self.mdu_parser.mdu_path.parent))
        as_written = mdu_dir / self.mdu_parser.get_keyword(INIFIELD_FILE_LINE)
        written = Path(os.path.abspath(as_written))
        inside = written.is_relative_to(mdu_dir) and inifield_path.resolve().is_relative_to(
            mdu_dir.resolve()
        )
        # the links are looked up on the path before `..` is collapsed, as the file system follows them
        linked = any(
            element.is_symlink()
            for element in (as_written, *as_written.parents)
            if element != mdu_dir and element.is_relative_to(mdu_dir)
        )
        problem = None
        if not inside:
            problem = "outside the MDU directory"
        elif linked:
            problem = "a symbolic link or behind one"
        return problem

    @staticmethod
    def _is_inside_polygon_value(block: AbstractSpatialField) -> bool:
        """Whether the block sets a constant `value` inside a polygon (not a vertical profile polygon)."""
        return (
                block.datafiletype == DataFileType.polygon
                and block.value is not None
                and not block.quantity.lower().startswith("initialvertical")
        )

    def convert(self, block: AbstractSpatialField, new_data_path: Path) -> Spatial:
        """Convert an inifield block to a `Spatial` block.

        Args:
            block (AbstractSpatialField):
                The `[Initial]` or `[Parameter]` block of an inifield file.
            new_data_path (Path):
                The path of the data file (or polygon) as it must be written in the new external forcings file.

        Returns:
            Spatial: The equivalent `[Spatial]` block.

        Raises:
            SpatialError: If the converted keywords do not form a valid `Spatial` block.

        Warns:
            UserWarning: If a polygon block of an `initialvertical*` quantity has a `value`, which a `[Spatial]`
                block with `dataFile` cannot hold.

        Examples:
            - Convert the extrapolation setting and the operand:
                ```python
                >>> from pathlib import Path
                >>> from hydrolib.core.dflowfm.inifield.models import ParameterField
                >>> from hydrolib.tools.extforce_convert.converters.inifield import InifieldToSpatialConverter
                >>> block = ParameterField(
                ...     quantity="frictionCoefficient",
                ...     dataFile="a.xyz",
                ...     dataFileType="sample",
                ...     operand="*",
                ...     extrapolationMethod=True,
                ... )
                >>> spatial = InifieldToSpatialConverter().convert(block, Path("a.xyz"))
                >>> print(spatial.operand)
                multiply
                >>> spatial.extrapolationallowed
                True

                ```
            - Write another data file path than the one in the inifield:
                ```python
                >>> from pathlib import Path
                >>> from hydrolib.core.dflowfm.inifield.models import InitialField
                >>> from hydrolib.tools.extforce_convert.converters.inifield import InifieldToSpatialConverter
                >>> block = InitialField(quantity="salinity", dataFile="s.xyz", dataFileType="sample")
                >>> spatial = InifieldToSpatialConverter().convert(block, Path("../sub/s.xyz"))
                >>> spatial.datafile.filepath.as_posix()
                '../sub/s.xyz'

                ```
        """
        data: dict[str, Any] = {"quantity": block.quantity}

        for source, target in self.KEYWORD_MAP.items():
            if source in block.model_fields_set:
                data[target] = getattr(block, source)

        if self._is_inside_polygon_value(block):
            data.pop("datafiletype", None)
            data["targetmaskfile"] = DiskOnlyFileModel(new_data_path)
            data["datavalue"] = block.value
            data["interpolationmethod"] = InterpolationMethod.constant
        else:
            data["datafile"] = DiskOnlyFileModel(new_data_path)
            if block.value is not None:
                self.unconverted_quantities.append(block.quantity)
                warnings.warn(
                    f"The 'value' ({block.value}) of the {block.quantity} block is not converted: a [Spatial] "
                    "block with a dataFile has no keyword for it.",
                    UserWarning,
                    stacklevel=2,
                )

        return SpatialConverter._create_spatial_block(data)