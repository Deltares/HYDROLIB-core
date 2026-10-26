"""Make the blocks that write the same `.bc` file share one `ForcingModel`.

Several old-style quantities can resolve to the same `.bc` path (e.g. `tracerbndIM1` and
`tracerbndIM2` on one polyline). Each `ForcingModel` is saved with the file opened in `"w"` mode, so
the one saved last would replace the others. Sharing one model writes the file once.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, get_origin

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.tools.extforce_convert.utils import backup_file

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

    Two blocks write the same file when their `.bc` paths compare equal after `os.path.normcase`.
    On Windows that lower-cases, so `a.bc` and `A.bc` collapse to one entry and are merged into a
    single file; on Linux it does nothing, so they stay separate (matching the manual, which treats
    filenames as case-sensitive). Only the lookup is normalized: the filename stored and written to
    disk keeps its original casing, so nothing about the output changes except that the Windows
    overwrite is prevented.

    Args:
        ext_model (ExtModel): The new external forcing model the converted blocks are added to.
    """

    def __init__(self, ext_model: ExtModel) -> None:
        self._ext_file_directory: Path = ext_model.filepath.parent
        # Normalized `.bc` path -> the first block field that holds its forcing file.
        self._owner_by_bc_path: dict[str, BCFileOwner] = {}
        for block_list_name in self._block_list_field_names(ext_model):
            for existing_block in getattr(ext_model, block_list_name):
                for (
                    field_name,
                    forcing_model_or_placeholder,
                ) in self._get_forcing_model_or_disk_only_fields(existing_block):
                    self._owner_by_bc_path.setdefault(
                        self._normalize(forcing_model_or_placeholder.filepath),
                        BCFileOwner(existing_block, field_name),
                    )

    @staticmethod
    def _block_list_field_names(ext_model: ExtModel) -> list[str]:
        """Return the names of the `ExtModel` fields that are lists of blocks.

        Derived from `ExtModel.model_fields`, so a block list added later (e.g. a new quantity
        type) is picked up without editing this class. Which fields of a block can hold a forcing
        file is decided per block by `_get_forcing_model_or_disk_only_fields`.
        """
        return [
            field_name
            for field_name, field in type(ext_model).model_fields.items()
            if get_origin(field.annotation) is list
        ]

    @property
    def owner_by_bc_path(self) -> dict[str, BCFileOwner]:
        """The first block field that holds the forcing file written to each normalized `.bc` path."""
        return self._owner_by_bc_path

    @staticmethod
    def _normalize(bc_filepath: Path) -> str:
        """Return the dedup key for a `.bc` path.

        `os.path.normcase` lower-cases on case-insensitive file systems (Windows) and is a no-op on
        case-sensitive ones (Linux), so two names that are the same file on disk share one key while
        the stored filename, and what is written, keeps its original casing.
        """
        return os.path.normcase(str(bc_filepath))

    def share(self, block: Any) -> None:
        """Point the forcing models of `converted_block` at the ones already writing the same path.

        The forcings the shared model does not hold yet are appended to it, so an equal forcing is
        never written twice. A model nobody writes yet is remembered for the blocks that follow.

        Args:
            block (Any): The newly converted block, not yet added to the ext model.
        """
        for field_name, field_value in self._get_forcing_model_or_disk_only_fields(
            block
        ):
            if isinstance(field_value, ForcingModel):
                shared_model = self._find_forcing_model(field_value.filepath)
                if shared_model is None:
                    self._owner_by_bc_path[self._normalize(field_value.filepath)] = (
                        BCFileOwner(block, field_name)
                    )
                elif shared_model is not field_value:
                    # if the new forcing file from the current block is not the same as the shared one,
                    # append its forcings to the shared one
                    self._append_missing_forcings(shared_model, field_value)
                    setattr(block, field_name, shared_model)

    @staticmethod
    def _get_forcing_model_or_disk_only_fields(block: Any) -> list[tuple[str, Any]]:
        """Return `(field name, field value)` of the fields of `block` holding a forcing model.

        A field is returned when its value is a `ForcingModel` or a `DiskOnlyFileModel` that has a
        path.
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

    @staticmethod
    def _append_missing_forcings(
        shared_model: ForcingModel, new_model: ForcingModel
    ) -> None:
        """Append the forcings of `new_model` that `shared_model` does not hold yet."""
        for forcing in new_model.forcing:
            if forcing not in shared_model.forcing:
                shared_model.forcing.append(forcing)

    def _find_forcing_model(self, bc_filepath: Path) -> ForcingModel | None:
        """Finds if there is a `ForcingModel` that writes to the given `bc_filepath`.

        Returns None when no block writes the path, or when its placeholder has no file on disk yet.

        Raises:
            ValueError: If the existing `.bc` file on disk cannot be parsed.

        Warns:
            UserWarning: When an existing `.bc` file is parsed to be merged into. It is written
                back by the model, so any comments or keywords the model does not know are not
                kept; the original file is backed up to `<name>.bc.bak` first. The warning is
                raised whether or not the file has any.
            UserWarning: When the existing ext references a `.bc` that is not on disk. There is
                nothing to merge, so the converted block creates it.
        """
        found_model = None
        owner = self._owner_by_bc_path.get(self._normalize(bc_filepath))
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
                    # the original file is moved to `<name>.bc.bak` before the merged model
                    # rewrites it, so its original content is never lost
                    backup_file(bc_file_on_disk)
                    warnings.warn(
                        f"The existing `{bc_file_on_disk}` is rewritten to add the converted "
                        f"quantities. Any comments or keywords that the model does not know "
                        f"are not kept; the original file is backed up to "
                        f"`{bc_file_on_disk.name}.bak`.",
                        UserWarning,
                        stacklevel=4,
                    )
                    found_model.filepath = placeholder.filepath
                    owner.replace_forcing_file(found_model)
                else:
                    # the existing ext references a `.bc` that is not on disk; there is nothing
                    # to merge, so the converted block creates it from its own quantities
                    warnings.warn(
                        f"The existing external forcing file references `{bc_file_on_disk}`, "
                        f"which is not on disk. It is created from the converted quantities.",
                        UserWarning,
                        stacklevel=4,
                    )

        return found_model
