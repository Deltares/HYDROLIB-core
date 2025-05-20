from typing import Literal

from pydantic import Field

from hydrolib.core.dflowfm.research.models import ResearchFMModel, ResearchGeneral


class LegacyGeneralAsModel(ResearchGeneral):
    """
    The `[Model]` section in a legacy MDU file.

    This a small helper class to support legacy versions of .mdu files, where
    the `[General]` section with metadata did not exist yet, and was called
    `[Model]` instead.
    """

    _header: Literal["Model"] = "Model"
    mduformatversion: str = Field("1.06", alias="MDUFormatVersion")


class LegacyFMModel(ResearchFMModel):
    """
    Legacy version of an MDU file, specifically for: MDUFormatVersion <= 1.06.

    This a small wrapper class to support legacy versions of .mdu files, where
    the `[General]` section with metadata did not exist yet, and was called
    `[Model]` instead.
    """

    model: LegacyGeneralAsModel = Field(default_factory=LegacyGeneralAsModel)
