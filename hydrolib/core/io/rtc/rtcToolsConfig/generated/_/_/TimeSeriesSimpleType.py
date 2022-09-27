# generated by datamodel-codegen:
#   filename:  rtcToolsConfig.json
#   timestamp: 2022-09-27T13:34:13+00:00

from __future__ import annotations

from typing import Optional

from hydrolib.core.io.rtc.basemodel import RtcBaseModel
from pydantic import Extra, Field

from ... import (
    InputReferenceEnumStringType,
    TimeSeriesSimpleType,
    XsBoolean,
    XsDouble,
    XsString,
)


class Field1(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_id: XsString
    attr_selectingColumnId: Optional[XsString] = None


class Field10(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field11(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field12(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field13(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field14(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field15(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field16(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field17(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_factor: Optional[XsDouble] = None
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field18(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_nStepSeries: Optional[TimeSeriesSimpleType] = None
    attr_nStepSeriesStart: Optional[TimeSeriesSimpleType] = None
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field19(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_factor: Optional[XsDouble] = None


class Field2(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field20(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field21(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field22(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field23(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field24(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field25(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field3(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field4(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field5(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None


class Field6(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_factor: Optional[XsDouble] = None


class Field7(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_useAbsoluteAsSpillCap: Optional[XsBoolean] = None


class Field8(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_factor: Optional[XsDouble] = None


class Field9(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[TimeSeriesSimpleType] = Field(None, alias='$')
    attr_ref: Optional[InputReferenceEnumStringType] = None
