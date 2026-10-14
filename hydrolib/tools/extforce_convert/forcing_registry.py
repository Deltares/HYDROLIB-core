"""Registry of the `.bc` files that the blocks of a new external forcing model write.

Several old-style quantities can resolve to the same `.bc` path: two quantities on one polyline
(e.g. `tracerbndIM1` and `tracerbndIM2`), two spatial quantities on one `.tim`, or a boundary and
a source/sink on one `.pliz`. Each `ForcingModel` is written with the file opened in `"w"` mode, so
the model saved last would silently replace the quantities saved before it. The registry makes
blocks that write the same path share one `ForcingModel`, so the file is written once.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import ExtModel


@dataclass
class _ForcingFileFieldRef:
    """A reference to a block field that holds a forcing file (a `ForcingModel` or a placeholder)."""

    block: Any
    field_name: str

    @property
    def value(self) -> Any:
        return getattr(self.block, self.field_name)

    def replace(self, value: Any) -> None:
        setattr(self.block, self.field_name, value)


class ForcingFileRegistry:
    """Index of the forcing files written by the blocks of an `ExtModel`, by path.

    Create it before converting, and call `share` for every converted block before the block is
    added to the ext model.

    The blocks of an existing new external forcing file are loaded without their child files, so
    their forcing fields hold a `DiskOnlyFileModel` placeholder. When a converted block writes the
    same path and the file exists, the file is parsed and replaces the placeholder, so that the
    quantities it already holds are kept instead of overwritten.

    Args:
        ext_model (ExtModel): The new external forcing model that the converted blocks are added to.

    Examples:
        ```python
        >>> registry = ForcingFileRegistry(ext_model) #doctest: +SKIP
        >>> registry.share(new_block) #doctest: +SKIP
        >>> ext_model.boundary = ext_model.boundary + [new_block] #doctest: +SKIP

        ```
    """

    # Names of the `ExtModel` lists whose blocks can hold a forcing file.
    BLOCK_LISTS = (
        "boundary",
        "lateral",
        "sourcesink",
        "bubblescreen",
        "meteo",
        "spatial",
    )

    def __init__(self, ext_model: ExtModel) -> None:
        self._base_dir: Path = ext_model.filepath.parent
        self._field_refs: Dict[Path, _ForcingFileFieldRef] = {}
        for list_name in self.BLOCK_LISTS:
            for block in getattr(ext_model, list_name):
                self._register_existing(block)

    def share(self, block: Any) -> None:
        """Make `block` share the forcing models of the blocks that write the same paths.

        For every `ForcingModel` held by `block`: when a block already writes the same `.bc` path,
        the forcings that model does not hold yet are appended to it and the field of `block` is
        pointed at it. Otherwise the model is registered for the blocks converted after this one.
        A forcing equal to one already in the shared model is not added again.

        Args:
            block (Any): The newly converted block, not yet added to the ext model.
        """
        for field_name, forcing_model in self._fields_holding(
            block, (ForcingModel,)
        ).items():
            filepath = forcing_model.filepath
            field_ref = self._field_refs.get(filepath)
            target = None if field_ref is None else self._resolve(field_ref)
            if target is None:
                # Nothing usable writes this path yet: this model becomes the one to share.
                self._field_refs[filepath] = _ForcingFileFieldRef(block, field_name)
            elif target is not forcing_model:
                self._append_missing(target, forcing_model)
                setattr(block, field_name, target)

    def _register_existing(self, block: Any) -> None:
        """Register the forcing files of a block of the existing ext model, first one wins."""
        for field_name, value in self._fields_holding(
            block, (ForcingModel, DiskOnlyFileModel)
        ).items():
            self._field_refs.setdefault(
                value.filepath, _ForcingFileFieldRef(block, field_name)
            )

    def _resolve(self, field_ref: _ForcingFileFieldRef) -> ForcingModel | None:
        """Return the `ForcingModel` of a field reference, parsing a placeholder whose file exists.

        Returns None for a placeholder whose file does not exist yet, so that a new file is
        simply written and the placeholder's block is left as it is.
        """
        value = field_ref.value
        if isinstance(value, DiskOnlyFileModel):
            value = self._load(value)
            if value is not None:
                field_ref.replace(value)

        return value

    def _load(self, placeholder: DiskOnlyFileModel) -> ForcingModel | None:
        """Parse the `.bc` file of a placeholder, keeping its (relative) path."""
        loaded = None
        resolved = self._base_dir / placeholder.filepath
        if resolved.is_file():
            loaded = ForcingModel(resolved)
            loaded.filepath = placeholder.filepath

        return loaded

    @staticmethod
    def _fields_holding(block: Any, types: Tuple[type, ...]) -> Dict[str, Any]:
        """Return the fields of `block` that hold one of `types` with a path, by field name."""
        fields = {}
        for field_name in type(block).model_fields:
            value = getattr(block, field_name, None)
            if isinstance(value, types) and value.filepath is not None:
                fields[field_name] = value

        return fields

    @staticmethod
    def _append_missing(target: ForcingModel, source: ForcingModel) -> None:
        """Append the forcings of `source` that `target` does not hold yet."""
        for forcing in source.forcing:
            if forcing not in target.forcing:
                target.forcing.append(forcing)
