from abc import ABC, abstractclassmethod, abstractclassmethod
from enum import Enum
from hydrolib.core.io.ini.models import Property, Section
from pathlib import Path
from hydrolib.core.basemodel import BaseModel
from pydantic import validator
from pydantic.generics import GenericModel
from pydantic.types import constr
from typing import Any, Dict, Generic, List, Literal, Optional, Type, TypeVar, Union

TPropertyField = TypeVar("TPropertyField")


# This is more generic and should be moved to seperately
class PropertyField(GenericModel, Generic[TPropertyField]):
    key: str  # this really should be immutable
    value: TPropertyField
    comment: Optional[str] = None

    @classmethod
    def validate(cls: Type["PropertyField"], value: Any) -> "PropertyField":
        if isinstance(value, Property):
            value = value.dict(exclude={"line"})

        return super().validate(value)


# TODO: handle comment blocks
# TODO: handle duplicate keys
class IniBasedModel(BaseModel, ABC):
    unknown_properties: List[PropertyField[Optional[str]]]
    order: Optional[List[str]] = None

    @classmethod
    def validate(cls: Type["IniBasedModel"], value: Any) -> "IniBasedModel":
        if isinstance(value, Section):
            converted_content = cls._convert_section_content(value.content)
            underlying_dict = cls._convert_section_to_dict(value)
            value = {**underlying_dict, **converted_content}

        return super().validate(value)

    @classmethod
    @abstractclassmethod
    def _field_mapping(cls) -> Dict[str, str]:
        return {}

    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "datablock",
                "content",
            }
        )

    @classmethod
    def _convert_section_content(cls, content: List):
        data: Dict[str, Any] = {"unknown_properties": []}
        mapping = cls._field_mapping()

        for v in content:
            if not isinstance(v, Property):
                continue

            if v.key in mapping:
                data[mapping[v.key]] = v
            else:
                data["unknown_properties"].append(v)

        return data


class DataBlockIniBasedModel(IniBasedModel):
    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "content",
            }
        )


class Structure(IniBasedModel):
    id: PropertyField[constr(max_length=256)]  # type: ignore
    name: PropertyField[str]
    header: Literal["Structure"] = "Structure"

    # Either branchId and chainage are required or
    # numCoordinates, xCoordinates, yCoordinates
    # unless the Structure is a compound
    # TODO: verify whether we can change this to model it better
    # TODO: e.g. create a BranchLocation, LineLocation, and define a single location field as a Union[BranchLocation, LineLocation]
    # TODO: Handle compound separately. Technically this seems to be a difference between 1D and 2D structures.
    branch_id = PropertyField[Optional[str]](key="branchId", value=None)

    chainage = PropertyField[Optional[float]](key="chainage", value=None)

    n_coordinates = PropertyField[Optional[int]](key="numCoordinates", value=None)

    x_coordinates = PropertyField[Optional[List[float]]](key="xCoordinates", value=None)
    y_coordinates = PropertyField[Optional[List[float]]](key="yCoordinates", value=None)

    # TODO: Add validator for location
    @classmethod
    def _field_mapping(cls) -> Dict[str, str]:
        # TODO: Can we derive these automatically?
        structure_mappings = {
            "id": "id",
            "name": "name",
            "branchId": "branch_id",
            "chainage": "chainage",
            "numCoordinates": "n_coordinates",
            "xCoordinates": "x_coordinates",
            "yCoordinates": "y_coordinates",
        }
        return {**super()._field_mapping(), **structure_mappings}


class FlowDirection(Enum):
    NONE = "none"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOTH = "both"


class Weir(Structure):
    structure_type = PropertyField[Literal["weir"]](key="type", value="weir")

    allowed_flow_direction = PropertyField[FlowDirection](
        key="allowedFlowdir", value=FlowDirection.BOTH
    )

    # TODO: verify default value
    crest_level = PropertyField[Union[float, Path]](key="crestLevel", value=0.0)
    crest_width = PropertyField[Optional[float]](key="crestWidth", value=None)
    correction_coefficient = PropertyField[float](key="corrCoeff", value=1.0)
    use_velocity_height = PropertyField[bool](key="useVelocityHeight", value=True)

    @classmethod
    def _field_mapping(cls) -> Dict[str, str]:
        weir_mappings = {
            "type": "structure_type",
            "allowedFlowdir": "allowed_flow_direction",
            "crestLevel": "crest_level",
            "crestWidth": "crest_width",
            "corrCoeff": "correction_coefficient",
            "useVelocityHeight": "use_velocity_height",
        }
        return {**super()._field_mapping(), **weir_mappings}
