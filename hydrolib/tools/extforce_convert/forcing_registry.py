"""Make the blocks that write the same `.bc` file share one `ForcingModel`.

Several old-style quantities can resolve to the same `.bc` path (e.g. `tracerbndIM1` and
`tracerbndIM2` on one polyline). Each `ForcingModel` is saved with the file opened in `"w"` mode, so
the one saved last would replace the others. Sharing one model writes the file once.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import ExtModel

# Names of the `ExtModel` lists whose blocks can hold a forcing file.
FORCING_BLOCK_LIST_NAMES = (
    "boundary",
    "lateral",
    "sourcesink",
    "bubblescreen",
    "meteo",
    "spatial",
)


def _get_forcing_model_or_disk_only_fields(block: Any) -> list[tuple[str, Any]]:
    """Return `(field name, field value)` of the fields of `block` holding a forcing model.

    A field is returned when its value is a `ForcingModel` or a `DiskOnlyFileModel` that has a path.
    """
    field_name_and_value_pairs = [
        (field_name, getattr(block, field_name, None))
        for field_name in type(block).model_fields
    ]

    return [
        (field_name, field_value)
        for field_name, field_value in field_name_and_value_pairs
        if isinstance(field_value, (ForcingModel, DiskOnlyFileModel))
        and field_value.filepath is not None
    ]


@dataclass
class BCFileOwner:
    # The first block field that holds the forcing file written to a `.bc` path.
    block: Any
    field_name: str

    @property
    def forcing_file(self) -> Any:
        # A `ForcingModel`, or a `DiskOnlyFileModel` placeholder when the file is not parsed yet.
        return getattr(self.block, self.field_name)

    def replace_forcing_file(self, forcing_model: ForcingModel) -> None:
        setattr(self.block, self.field_name, forcing_model)


class ForcingFileRegistry:
    """Remember which block writes which `.bc` path, so a new block can share its model.

    Call `share` for every converted block before adding it to the ext model.

    The blocks of an existing new external forcing file hold a `DiskOnlyFileModel` placeholder, not
    the parsed file. It is parsed only when a converted block writes the same path and the file
    exists, so the quantities it holds are kept instead of overwritten.

    Args:
        ext_model (ExtModel): The new external forcing model the converted blocks are added to.
    """

    def __init__(self, ext_model: ExtModel) -> None:
        self._ext_file_directory: Path = ext_model.filepath.parent
        # `.bc` path -> the first block field that holds its forcing file.
        self._owner_by_bc_path: dict[Path, BCFileOwner] = {}
        for block_list_name in FORCING_BLOCK_LIST_NAMES:
            for existing_block in getattr(ext_model, block_list_name):
                for (
                    field_name,
                    forcing_model_or_placeholder,
                ) in _get_forcing_model_or_disk_only_fields(existing_block):
                    self._owner_by_bc_path.setdefault(
                        forcing_model_or_placeholder.filepath,
                        BCFileOwner(existing_block, field_name),
                    )

    @property
    def owner_by_bc_path(self) -> dict[Path, BCFileOwner]:
        """The first block field that holds the forcing file written to each `.bc` path."""
        return self._owner_by_bc_path

    def share(self, block: Any) -> None:
        """Point the forcing models of `converted_block` at the ones already writing the same path.

        The forcings the shared model does not hold yet are appended to it, so an equal forcing is
        never written twice. A model nobody writes yet is remembered for the blocks that follow.

        Args:
            block (Any): The newly converted block, not yet added to the ext model.
        """
        # forcing file could be a ForcingModel or a DiskOnlyFileModel placeholder,
        # depending on whether the block was already added to the ext model
        for field_name, field_value in _get_forcing_model_or_disk_only_fields(
            block
        ):
            if isinstance(field_value, ForcingModel):
                shared_model = self._find_forcing_model(field_value.filepath)
                if shared_model is None:
                    self._owner_by_bc_path[field_value.filepath] = BCFileOwner(
                        block, field_name
                    )
                elif shared_model is not field_value:
                    # if the new forcing file from the current block is not the same as the shared one,
                    # append its forcings to the shared one
                    for forcing in field_value.forcing:
                        if forcing not in shared_model.forcing:
                            shared_model.forcing.append(forcing)
                    setattr(block, field_name, shared_model)

    def _find_forcing_model(self, bc_filepath: Path) -> ForcingModel | None:
        """Finds if there is a `ForcingModel` that writes to the given `bc_filepath`.

        Returns None when no block writes the path, or when its placeholder has no file on disk yet.

        Raises:
            ValueError: If the existing `.bc` file on disk cannot be parsed.

        Warns:
            UserWarning: When an existing `.bc` file is parsed to be merged into. It is written
                back by the model, so any comments or keywords the model does not know are not
                kept. The warning is raised whether or not the file has any.
        """
        found_model = None
        owner = self._owner_by_bc_path.get(bc_filepath)
        if owner is not None:
            # the forcing file could be a ForcingModel or a DiskOnlyFileModel placeholder,
            # depending on whether the block was already added to the ext model
            if isinstance(owner.forcing_file, ForcingModel):
                found_model = owner.forcing_file
            elif isinstance(owner.forcing_file, DiskOnlyFileModel):
                placeholder = owner.forcing_file
                bc_file_on_disk = self._ext_file_directory / placeholder.filepath
                if bc_file_on_disk.is_file():
                    try:
                        found_model = ForcingModel(bc_file_on_disk)
                    except (ValueError, OSError) as error:
                        raise ValueError(
                            f"Cannot add the converted quantities to the existing "
                            f"`{bc_file_on_disk}`: the file could not be parsed. Fix or "
                            f"remove the file and convert again."
                        ) from error
                    warnings.warn(
                        f"The existing `{bc_file_on_disk}` is rewritten to add the converted "
                        f"quantities. Any comments or keywords that the model does not know "
                        f"are not kept.",
                        UserWarning,
                        stacklevel=4,
                    )
                    found_model.filepath = placeholder.filepath
                    owner.replace_forcing_file(found_model)

        return found_model
