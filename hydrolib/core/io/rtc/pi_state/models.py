# generated by datamodel-codegen:
#   filename:  pi_state.json
#   timestamp: 2022-09-23T08:47:48+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Extra, Field, conint, constr

from . import _


class FewsGeoDatumEnumStringType(Enum):
    LOCAL = "LOCAL"
    WGS_1984 = "WGS 1984"
    Ordnance_Survey_Great_Britain_1936 = "Ordnance Survey Great Britain 1936"
    TWD_1967 = "TWD 1967"
    Gauss_Krueger_Meridian2 = "Gauss Krueger Meridian2"
    Gauss_Krueger_Meridian3 = "Gauss Krueger Meridian3"
    Gauss_Krueger_Austria_M34 = "Gauss Krueger Austria M34"
    Gauss_Krueger_Austria_M31 = "Gauss Krueger Austria M31"
    Rijks_Driehoekstelsel = "Rijks Driehoekstelsel"
    JRC = "JRC"
    DWD = "DWD"
    KNMI_Radar = "KNMI Radar"
    CH1903 = "CH1903"
    PAK1 = "PAK1"
    PAK2 = "PAK2"
    SVY21 = "SVY21"


class FewsGeoDatumStringTypeEnum(Enum):
    LOCAL = "LOCAL"
    WGS_1984 = "WGS 1984"
    Ordnance_Survey_Great_Britain_1936 = "Ordnance Survey Great Britain 1936"
    TWD_1967 = "TWD 1967"
    Gauss_Krueger_Meridian2 = "Gauss Krueger Meridian2"
    Gauss_Krueger_Meridian3 = "Gauss Krueger Meridian3"
    Gauss_Krueger_Austria_M34 = "Gauss Krueger Austria M34"
    Gauss_Krueger_Austria_M31 = "Gauss Krueger Austria M31"
    Rijks_Driehoekstelsel = "Rijks Driehoekstelsel"
    JRC = "JRC"
    DWD = "DWD"
    KNMI_Radar = "KNMI Radar"
    CH1903 = "CH1903"
    PAK1 = "PAK1"
    PAK2 = "PAK2"
    SVY21 = "SVY21"


class FewsGeoDatumStringType(BaseModel):
    __root__: Union[
        FewsGeoDatumStringTypeEnum,
        constr(regex=r"^(UTM((0[1-9])|([1-5][0-9])|(UTM60))[NS])$"),
    ]


class FewsLocationIdSimpleType(BaseModel):
    __root__: str = Field(..., description="Location ID, defined by the model")


class FewsParameterSimpleType(BaseModel):
    __root__: str = Field(
        ...,
        description="Content of the data (Discharge, Precipitation, VPD); defined by the model",
    )


class _Type(Enum):
    file = "file"
    directory = "directory"


class _Unit(Enum):
    integer_1 = 1
    integer_2 = 2
    integer_3 = 3
    integer_4 = 4


class FewsTimeZoneSimpleType(BaseModel):
    __root__: float = Field(
        ...,
        description="The timeZone (in decimal hours shift from GMT) e.g. -1.0 or 3.5. If not present the default timezone configured in the general adapter or import module is used. Always written when exported from FEWS",
    )


class FewsUtmGeoDatumStringType(BaseModel):
    __root__: constr(regex=r"^(UTM((0[1-9])|([1-5][0-9])|(UTM60))[NS])$")


class FewsValueTypeEnumStringType(Enum):
    boolean = "boolean"
    int = "int"
    float = "float"
    double = "double"
    string = "string"


class FewsBooleanStringType(BaseModel):
    __root__: Union[bool, constr(regex=r"^([\w\D]*[@][\w\D]*)$")] = Field(
        ..., description=" \n\t\t\t\tBoolean that allows (global) properties\n\t\t\t"
    )


class FewsCommentString(BaseModel):
    __root__: str


class FewsDateType(BaseModel):
    __root__: constr(regex=r"^([\d][\d][\d][\d]\-[\d][\d]\-[\d][\d])$")


class FewsDoubleStringType(BaseModel):
    __root__: Union[float, constr(regex=r"^([\w\D]*[@][\w\D]*)$")] = Field(
        ...,
        description="\n\t\t\t\tDouble that allows use of location attributes\n\t\t\t",
    )


class FewsEventCodeString(BaseModel):
    __root__: constr(regex=r"^(\^\:)$")


class FewsIdString(BaseModel):
    __root__: str


class FewsIdStringType(BaseModel):
    __root__: constr(min_length=1, max_length=64)


class FewsIntStringType(BaseModel):
    __root__: Union[
        conint(ge=-2147483648, le=2147483647), constr(regex=r"^([\w\D]*[@][\w\D]*)$")
    ] = Field(
        ..., description="\n\t\t\t\tInteger that allows (global) properties\n\t\t\t"
    )


class FewsNameString(BaseModel):
    __root__: str


class FewsNonEmptyStringType(BaseModel):
    __root__: constr(min_length=1)


class FewsPropertyReferenceString(BaseModel):
    __root__: constr(regex=r"^([\w\D]*[@][\w\D]*)$")


class FewsTimeSeriesType1(Enum):
    accumulative = "accumulative"
    instantaneous = "instantaneous"
    mean = "mean"


class FewsTimeSeriesTypeEnumStringType(Enum):
    external_historical = "external historical"
    external_forecasting = "external forecasting"
    simulated_historical = "simulated historical"
    simulated_forecasting = "simulated forecasting"
    temporary = "temporary"


class FewsTimeStepUnitEnumStringType(Enum):
    second = "second"
    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"
    nonequidistant = "nonequidistant"


class FewsTimeType(BaseModel):
    __root__: constr(regex=r"^([\d][\d]\:[\d][\d]\:[\d][\d])$")


class FewsVersionString(Enum):
    field_1_2 = "1.2"
    field_1_3 = "1.3"
    field_1_4 = "1.4"
    field_1_5 = "1.5"
    field_1_6 = "1.6"
    field_1_7 = "1.7"
    field_1_8 = "1.8"
    field_1_9 = "1.9"
    field_1_10 = "1.10"
    field_1_11 = "1.11"
    field_1_12 = "1.12"
    field_1_13 = "1.13"
    field_1_14 = "1.14"


class XsAnyURI(BaseModel):
    __root__: str


class XsBoolean(BaseModel):
    __root__: bool


class XsDouble(BaseModel):
    __root__: float


class XsFloat(BaseModel):
    __root__: float


class XsGDay(BaseModel):
    __root__: str


class XsGMonth(BaseModel):
    __root__: str


class XsGMonthDay(BaseModel):
    __root__: str


class XsInt(BaseModel):
    __root__: conint(ge=-2147483648, le=2147483647)


class XsNonNegativeInteger(BaseModel):
    __root__: conint(ge=0)


class XsPositiveInteger(BaseModel):
    __root__: conint(ge=1)


class XsString(BaseModel):
    __root__: str


class FewsEnsembleId(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsIdStringType] = Field(None, alias="$")


class FewsLocationIdItem(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsIdStringType] = Field(None, alias="$")


class FewsModuleInstanceId(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsIdStringType] = Field(None, alias="$")


class FewsParameterId(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsIdStringType] = Field(None, alias="$")


class FewsQualifierIdItem(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsIdStringType] = Field(None, alias="$")


class FewsTimeSeriesType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsTimeSeriesTypeEnumStringType] = Field(None, alias="$")


class FewsDescription(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsBoolPropertyComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _key: XsString = Field(..., alias="@key")
    _value: XsBoolean = Field(..., alias="@value")
    fews_description: Optional[FewsDescription] = Field(None, alias="fews:description")


class FewsColumnIdsComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _A: XsString = Field(..., alias="@A")
    _B: Optional[XsString] = Field(None, alias="@B")
    _C: Optional[XsString] = Field(None, alias="@C")
    _D: Optional[XsString] = Field(None, alias="@D")
    _E: Optional[XsString] = Field(None, alias="@E")
    _F: Optional[XsString] = Field(None, alias="@F")
    _G: Optional[XsString] = Field(None, alias="@G")
    _H: Optional[XsString] = Field(None, alias="@H")
    _I: Optional[XsString] = Field(None, alias="@I")
    _J: Optional[XsString] = Field(None, alias="@J")
    _K: Optional[XsString] = Field(None, alias="@K")
    _L: Optional[XsString] = Field(None, alias="@L")
    _M: Optional[XsString] = Field(None, alias="@M")
    _N: Optional[XsString] = Field(None, alias="@N")
    _O: Optional[XsString] = Field(None, alias="@O")
    _P: Optional[XsString] = Field(None, alias="@P")
    _Q: Optional[XsString] = Field(None, alias="@Q")
    _R: Optional[XsString] = Field(None, alias="@R")
    _S: Optional[XsString] = Field(None, alias="@S")
    _T: Optional[XsString] = Field(None, alias="@T")
    _U: Optional[XsString] = Field(None, alias="@U")
    _V: Optional[XsString] = Field(None, alias="@V")
    _W: Optional[XsString] = Field(None, alias="@W")
    _X: Optional[XsString] = Field(None, alias="@X")
    _Y: Optional[XsString] = Field(None, alias="@Y")
    _Z: Optional[XsString] = Field(None, alias="@Z")


class FewsColumnMetaDataComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _A: XsString = Field(..., alias="@A")
    _B: Optional[XsString] = Field(None, alias="@B")
    _C: Optional[XsString] = Field(None, alias="@C")
    _D: Optional[XsString] = Field(None, alias="@D")
    _E: Optional[XsString] = Field(None, alias="@E")
    _F: Optional[XsString] = Field(None, alias="@F")
    _G: Optional[XsString] = Field(None, alias="@G")
    _H: Optional[XsString] = Field(None, alias="@H")
    _I: Optional[XsString] = Field(None, alias="@I")
    _J: Optional[XsString] = Field(None, alias="@J")
    _K: Optional[XsString] = Field(None, alias="@K")
    _L: Optional[XsString] = Field(None, alias="@L")
    _M: Optional[XsString] = Field(None, alias="@M")
    _N: Optional[XsString] = Field(None, alias="@N")
    _O: Optional[XsString] = Field(None, alias="@O")
    _P: Optional[XsString] = Field(None, alias="@P")
    _Q: Optional[XsString] = Field(None, alias="@Q")
    _R: Optional[XsString] = Field(None, alias="@R")
    _S: Optional[XsString] = Field(None, alias="@S")
    _T: Optional[XsString] = Field(None, alias="@T")
    _U: Optional[XsString] = Field(None, alias="@U")
    _V: Optional[XsString] = Field(None, alias="@V")
    _W: Optional[XsString] = Field(None, alias="@W")
    _X: Optional[XsString] = Field(None, alias="@X")
    _Y: Optional[XsString] = Field(None, alias="@Y")
    _Z: Optional[XsString] = Field(None, alias="@Z")
    _id: Optional[XsString] = Field(None, alias="@id")
    _type: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@type")


class FewsColumnTypesComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _A: FewsValueTypeEnumStringType = Field(..., alias="@A")
    _B: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@B")
    _C: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@C")
    _D: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@D")
    _E: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@E")
    _F: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@F")
    _G: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@G")
    _H: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@H")
    _I: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@I")
    _J: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@J")
    _K: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@K")
    _L: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@L")
    _M: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@M")
    _N: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@N")
    _O: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@O")
    _P: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@P")
    _Q: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@Q")
    _R: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@R")
    _S: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@S")
    _T: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@T")
    _U: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@U")
    _V: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@V")
    _W: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@W")
    _X: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@X")
    _Y: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@Y")
    _Z: Optional[FewsValueTypeEnumStringType] = Field(None, alias="@Z")


class FewsDateTimeComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _date: FewsDateType = Field(..., alias="@date")
    _time: FewsTimeType = Field(..., alias="@time")


class FewsDescription1(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsDateTimePropertyComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _date: FewsDateType = Field(..., alias="@date")
    _key: XsString = Field(..., alias="@key")
    _time: FewsTimeType = Field(..., alias="@time")
    fews_description: Optional[FewsDescription1] = Field(None, alias="fews:description")


class FewsDescription2(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsDoublePropertyComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _key: XsString = Field(..., alias="@key")
    _value: XsDouble = Field(..., alias="@value")
    fews_description: Optional[FewsDescription2] = Field(None, alias="fews:description")


class FewsEnsembleMemberComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _index: XsNonNegativeInteger = Field(..., alias="@index")
    _weight: Optional[XsDouble] = Field(None, alias="@weight")


class FewsEnsembleMemberRangeComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _end: Optional[XsNonNegativeInteger] = Field(None, alias="@end")
    _start: XsNonNegativeInteger = Field(..., alias="@start")
    _weight: Optional[XsDouble] = Field(None, alias="@weight")


class FewsDescription3(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsFloatPropertyComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _key: XsString = Field(..., alias="@key")
    _value: XsFloat = Field(..., alias="@value")
    fews_description: Optional[FewsDescription3] = Field(None, alias="fews:description")


class FewsDescription4(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsIntPropertyComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _key: XsString = Field(..., alias="@key")
    _value: XsInt = Field(..., alias="@value")
    fews_description: Optional[FewsDescription4] = Field(None, alias="fews:description")


class FewsDayItem(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsGDay] = Field(None, alias="$")


class FewsEndMonthDay(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsGMonthDay] = Field(None, alias="$")


class FewsMonthItem(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsGMonth] = Field(None, alias="$")


class FewsMonthDayItem(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsGMonthDay] = Field(None, alias="$")


class FewsStartMonthDay(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsGMonthDay] = Field(None, alias="$")


class FewsTimeZone(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsTimeZoneSimpleType] = Field(None, alias="$")


class FewsPeriodConditionComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    fews_day: Optional[List[FewsDayItem]] = Field(None, alias="fews:day")
    fews_endDate: Optional[FewsDateTimeComplexType] = Field(
        None, alias="fews:endDate", description="End date and time for this period."
    )
    fews_endMonthDay: Optional[FewsEndMonthDay] = Field(
        None, alias="fews:endMonthDay", description="End month and day of this season."
    )
    fews_month: Optional[List[FewsMonthItem]] = Field(None, alias="fews:month")
    fews_monthDay: Optional[List[FewsMonthDayItem]] = Field(None, alias="fews:monthDay")
    fews_startDate: Optional[FewsDateTimeComplexType] = Field(
        None, alias="fews:startDate", description="Start date and time for this period."
    )
    fews_startMonthDay: Optional[FewsStartMonthDay] = Field(
        None,
        alias="fews:startMonthDay",
        description="Start month and day of this season.",
    )
    fews_timeZone: Optional[FewsTimeZone] = Field(
        None, alias="fews:timeZone", description="Timezone"
    )
    fews_validAfterDate: Optional[FewsDateTimeComplexType] = Field(
        None,
        alias="fews:validAfterDate",
        description="Valid for entire period after this date and time.",
    )
    fews_validBeforeDate: Optional[FewsDateTimeComplexType] = Field(
        None,
        alias="fews:validBeforeDate",
        description="Valid for entire period prior to this date and time.",
    )


class FewsDescription5(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsRowComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _A: XsString = Field(..., alias="@A")
    _B: Optional[XsString] = Field(None, alias="@B")
    _C: Optional[XsString] = Field(None, alias="@C")
    _D: Optional[XsString] = Field(None, alias="@D")
    _E: Optional[XsString] = Field(None, alias="@E")
    _F: Optional[XsString] = Field(None, alias="@F")
    _G: Optional[XsString] = Field(None, alias="@G")
    _H: Optional[XsString] = Field(None, alias="@H")
    _I: Optional[XsString] = Field(None, alias="@I")
    _J: Optional[XsString] = Field(None, alias="@J")
    _K: Optional[XsString] = Field(None, alias="@K")
    _L: Optional[XsString] = Field(None, alias="@L")
    _M: Optional[XsString] = Field(None, alias="@M")
    _N: Optional[XsString] = Field(None, alias="@N")
    _O: Optional[XsString] = Field(None, alias="@O")
    _P: Optional[XsString] = Field(None, alias="@P")
    _Q: Optional[XsString] = Field(None, alias="@Q")
    _R: Optional[XsString] = Field(None, alias="@R")
    _S: Optional[XsString] = Field(None, alias="@S")
    _T: Optional[XsString] = Field(None, alias="@T")
    _U: Optional[XsString] = Field(None, alias="@U")
    _V: Optional[XsString] = Field(None, alias="@V")
    _W: Optional[XsString] = Field(None, alias="@W")
    _X: Optional[XsString] = Field(None, alias="@X")
    _Y: Optional[XsString] = Field(None, alias="@Y")
    _Z: Optional[XsString] = Field(None, alias="@Z")


class FewsComment(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsCommentString] = Field(None, alias="$")


class FewsStateId(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsIdString] = Field(None, alias="$")


class FewsStateName(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsNameString] = Field(None, alias="$")


class FewsTimeZone1(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[FewsTimeZoneSimpleType] = Field(None, alias="$")


class FewsReadLocation(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsAnyURI] = Field(None, alias="$")


class FewsWriteLocation(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsAnyURI] = Field(None, alias="$")


class FewsStateReadWriteDirectoryComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _type: _Type = Field(..., alias="@type")
    fews_readLocation: FewsReadLocation = Field(
        ...,
        alias="fews:readLocation",
        description="The name of the input state of the model. The write location is imported by the general adapter. This imported file is renamed to the read location internally",
    )
    fews_writeLocation: FewsWriteLocation = Field(
        ...,
        alias="fews:writeLocation",
        description="The name of the output state of the model. The write location is imported by the general adapter. This imported file is renamed to the read location internally",
    )


class FewsDescription6(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    __1: Optional[XsString] = Field(None, alias="$")


class FewsStringPropertyComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _key: XsString = Field(..., alias="@key")
    _value: XsString = Field(..., alias="@value")
    fews_description: Optional[FewsDescription6] = Field(None, alias="fews:description")


class FewsTimeStepComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _divider: Optional[XsPositiveInteger] = Field(None, alias="@divider")
    _multiplier: Optional[XsNonNegativeInteger] = Field(None, alias="@multiplier")
    _unit: FewsTimeStepUnitEnumStringType = Field(..., alias="@unit")


class FewsTimeStepUnitComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _divider: Optional[XsInt] = Field(None, alias="@divider")
    _unit: _Unit = Field(..., alias="@unit")


class FewsArchiveTimeSeriesSetComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    fews_ensembleId: Optional[FewsEnsembleId] = Field(
        None,
        alias="fews:ensembleId",
        description="Optional field for running ensembles. Ensemble id's in a time series set will override ensemble id's defined in the workflow.",
    )
    fews_locationId: List[FewsLocationIdItem] = Field(
        ..., alias="fews:locationId", min_items=1
    )
    fews_moduleInstanceId: FewsModuleInstanceId = Field(
        ..., alias="fews:moduleInstanceId"
    )
    fews_parameterId: FewsParameterId = Field(..., alias="fews:parameterId")
    fews_qualifierId: Optional[List[FewsQualifierIdItem]] = Field(
        None, alias="fews:qualifierId"
    )
    fews_timeSeriesType: FewsTimeSeriesType = Field(..., alias="fews:timeSeriesType")
    fews_timeStep: FewsTimeStepComplexType = Field(..., alias="fews:timeStep")


class FewsGlobalTableComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    fews_columnIds: Optional[FewsColumnIdsComplexType] = Field(
        None, alias="fews:columnIds"
    )
    fews_columnMetaData: Optional[List[FewsColumnMetaDataComplexType]] = Field(
        None, alias="fews:columnMetaData"
    )
    fews_columnTypes: Optional[FewsColumnTypesComplexType] = Field(
        None, alias="fews:columnTypes"
    )
    fews_columnUnits: Optional[FewsColumnIdsComplexType] = Field(
        None, alias="fews:columnUnits"
    )
    fews_row: List[FewsRowComplexType] = Field(..., alias="fews:row", min_items=1)


class FewsPropertiesComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    fews_bool: Optional[List[FewsBoolPropertyComplexType]] = Field(
        None, alias="fews:bool"
    )
    fews_dateTime: Optional[List[FewsDateTimePropertyComplexType]] = Field(
        None, alias="fews:dateTime"
    )
    fews_description: Optional[FewsDescription5] = Field(None, alias="fews:description")
    fews_double: Optional[List[FewsDoublePropertyComplexType]] = Field(
        None, alias="fews:double"
    )
    fews_float: Optional[List[FewsFloatPropertyComplexType]] = Field(
        None, alias="fews:float"
    )
    fews_int: Optional[List[FewsIntPropertyComplexType]] = Field(None, alias="fews:int")
    fews_string: Optional[List[FewsStringPropertyComplexType]] = Field(
        None, alias="fews:string"
    )


class FewsStateComplexType(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _version: FewsVersionString = Field(..., alias="@version")
    fews_comment: Optional[FewsComment] = Field(
        None,
        alias="fews:comment",
        description="use this field as a notebook to add comments, suggestions\n                        description of data entered etc.",
    )
    fews_dateTime: Optional[FewsDateTimeComplexType] = Field(
        None,
        alias="fews:dateTime",
        description="date and time this state is valid for/was taken",
    )
    fews_stateId: FewsStateId = Field(
        ..., alias="fews:stateId", description="id of this state, defined by the module"
    )
    fews_stateLoc: List[FewsStateReadWriteDirectoryComplexType] = Field(
        ..., alias="fews:stateLoc", min_items=1
    )
    fews_stateName: Optional[FewsStateName] = Field(
        None,
        alias="fews:stateName",
        description="optional descriptive name of this state",
    )
    fews_timeZone: Optional[FewsTimeZone1] = Field(
        None,
        alias="fews:timeZone",
        description="the time zone of the pi input files is assumed when the time zone in a pi output file is missing",
    )


class Model(BaseModel):
    class Config:
        extra = Extra.forbid

    _: Optional[str] = Field(None, alias="#")
    _xmlns_fews: Optional[Any] = Field(
        "http://www.wldelft.nl/fews/PI", alias="@xmlns:fews"
    )
    _xmlns_xs: Optional[Any] = Field(
        "http://www.w3.org/2001/XMLSchema", alias="@xmlns:xs"
    )
    fews_State: Optional[_.FewsState] = Field(None, alias="fews:State")
