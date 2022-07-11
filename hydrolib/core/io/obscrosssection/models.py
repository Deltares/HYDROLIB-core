from typing import List, Literal

from pydantic.fields import Field

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel


class ObservationPointCrossSectionGeneral(INIGeneral):
    filetype: Literal["obsCross"] = Field("obsCross", alias="fileType")


class ObservationPointCrossSection(INIBasedModel):
    pass


class ObservationPointCrossSectionModel(INIModel):
    """
    The overall observation point crosssection model that contains the contents
    of one observation point crosssection file.
    """

    general: ObservationPointCrossSectionGeneral = ObservationPointCrossSectionGeneral()
    crosssections: List[ObservationPointCrossSection] = []
