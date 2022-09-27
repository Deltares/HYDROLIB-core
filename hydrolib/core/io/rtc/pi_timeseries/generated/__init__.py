# generated by datamodel-codegen:
#   filename:  pi_timeseries.json
#   timestamp: 2022-09-27T18:48:32+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import Extra, Field

from hydrolib.core.io.rtc.basemodel import RtcBaseModel

from . import _


class GeoDatumEnumStringType(str, Enum):
    """
    The geographical datum for the location data. Presently only WGS-1984, OS 1936 and LOCAL are recognised. LOCAL indicates a local grid.
    """

    LOCAL = 'LOCAL'
    WGS_1984 = 'WGS 1984'
    Ordnance_Survey_Great_Britain_1936 = 'Ordnance Survey Great Britain 1936'
    TWD_1967 = 'TWD 1967'
    Gauss_Krueger_Meridian2 = 'Gauss Krueger Meridian2'
    Gauss_Krueger_Meridian3 = 'Gauss Krueger Meridian3'
    Gauss_Krueger_Austria_M34 = 'Gauss Krueger Austria M34'
    Gauss_Krueger_Austria_M31 = 'Gauss Krueger Austria M31'
    Rijks_Driehoekstelsel = 'Rijks Driehoekstelsel'
    JRC = 'JRC'
    DWD = 'DWD'
    KNMI_Radar = 'KNMI Radar'
    CH1903 = 'CH1903'
    PAK1 = 'PAK1'
    PAK2 = 'PAK2'
    SVY21 = 'SVY21'


class GeoDatumStringTypeEnum(str, Enum):
    """
    The geographical datum for the location data. Presently only WGS-1984, OS 1936 and LOCAL are recognised. LOCAL indicates a local grid.
    """

    LOCAL = 'LOCAL'
    WGS_1984 = 'WGS 1984'
    Ordnance_Survey_Great_Britain_1936 = 'Ordnance Survey Great Britain 1936'
    TWD_1967 = 'TWD 1967'
    Gauss_Krueger_Meridian2 = 'Gauss Krueger Meridian2'
    Gauss_Krueger_Meridian3 = 'Gauss Krueger Meridian3'
    Gauss_Krueger_Austria_M34 = 'Gauss Krueger Austria M34'
    Gauss_Krueger_Austria_M31 = 'Gauss Krueger Austria M31'
    Rijks_Driehoekstelsel = 'Rijks Driehoekstelsel'
    JRC = 'JRC'
    DWD = 'DWD'
    KNMI_Radar = 'KNMI Radar'
    CH1903 = 'CH1903'
    PAK1 = 'PAK1'
    PAK2 = 'PAK2'
    SVY21 = 'SVY21'


class GeoDatumStringTypeItem(RtcBaseModel):
    __root__: str = Field(..., regex='^(UTM((0[1-9])|([1-5][0-9])|(UTM60))[NS])$')


class GeoDatumStringType(RtcBaseModel):
    __root__: Union[GeoDatumStringTypeEnum, GeoDatumStringTypeItem]


class LocationIdSimpleType(RtcBaseModel):
    __root__: str = Field(..., description='Location ID, defined by the model')


class ParameterSimpleType(RtcBaseModel):
    __root__: str = Field(
        ...,
        description='Content of the data (Discharge, Precipitation, VPD); defined by the model',
    )


class AttrUnit(int, Enum):
    integer_1 = 1
    integer_2 = 2
    integer_3 = 3
    integer_4 = 4


class TimeZoneSimpleType(RtcBaseModel):
    __root__: float = Field(
        ...,
        description='The timeZone (in decimal hours shift from GMT) e.g. -1.0 or 3.5. If not present the default timezone configured in the general adapter or import module is used. Always written when exported from FEWS',
    )


class UtmGeoDatumStringType(RtcBaseModel):
    __root__: str = Field(..., regex='^(UTM((0[1-9])|([1-5][0-9])|(UTM60))[NS])$')


class ValueTypeEnumStringType(str, Enum):
    boolean = 'boolean'
    int = 'int'
    float = 'float'
    double = 'double'
    string = 'string'


class BooleanStringTypeItem(RtcBaseModel):
    __root__: str = Field(..., regex='^([\\w\\D]*[@][\\w\\D]*)$')


class BooleanStringType(RtcBaseModel):
    __root__: Union[bool, BooleanStringTypeItem] = Field(
        ..., description=' \n\t\t\t\tBoolean that allows (global) properties\n\t\t\t'
    )


class CommentString(RtcBaseModel):
    __root__: str


class DateType(RtcBaseModel):
    __root__: str = Field(
        ..., regex='^([\\d][\\d][\\d][\\d]\\-[\\d][\\d]\\-[\\d][\\d])$'
    )


class DoubleStringTypeItem(RtcBaseModel):
    __root__: str = Field(..., regex='^([\\w\\D]*[@][\\w\\D]*)$')


class DoubleStringType(RtcBaseModel):
    __root__: Union[float, DoubleStringTypeItem] = Field(
        ...,
        description='\n\t\t\t\tDouble that allows use of location attributes\n\t\t\t',
    )


class EventCodeString(RtcBaseModel):
    __root__: str = Field(..., regex='^(\\^\\:)$')


class IdString(RtcBaseModel):
    __root__: str


class IdStringType(RtcBaseModel):
    __root__: str = Field(..., max_length=64, min_length=1)


class IntStringTypeItem(RtcBaseModel):
    __root__: int = Field(..., ge=-2147483648, le=2147483647)


class IntStringTypeItem1(RtcBaseModel):
    __root__: str = Field(..., regex='^([\\w\\D]*[@][\\w\\D]*)$')


class IntStringType(RtcBaseModel):
    __root__: Union[IntStringTypeItem, IntStringTypeItem1] = Field(
        ..., description='\n\t\t\t\tInteger that allows (global) properties\n\t\t\t'
    )


class NameString(RtcBaseModel):
    __root__: str


class NonEmptyStringType(RtcBaseModel):
    __root__: str = Field(..., min_length=1)


class PropertyReferenceString(RtcBaseModel):
    __root__: str = Field(..., regex='^([\\w\\D]*[@][\\w\\D]*)$')


class TimeSeriesType(str, Enum):
    """
    Type of data, either accumulative or instantaneous. For accumulative data the time/date of the event is the moment at which the data was gathered.
			
    """

    accumulative = 'accumulative'
    instantaneous = 'instantaneous'
    mean = 'mean'


class TimeSeriesTypeEnumStringType(str, Enum):
    external_historical = 'external historical'
    external_forecasting = 'external forecasting'
    simulated_historical = 'simulated historical'
    simulated_forecasting = 'simulated forecasting'
    temporary = 'temporary'


class TimeStepUnitEnumStringType(str, Enum):
    second = 'second'
    minute = 'minute'
    hour = 'hour'
    day = 'day'
    week = 'week'
    month = 'month'
    year = 'year'
    nonequidistant = 'nonequidistant'


class TimeType(RtcBaseModel):
    __root__: str = Field(..., regex='^([\\d][\\d]\\:[\\d][\\d]\\:[\\d][\\d])$')


class VersionString(str, Enum):
    field_1_2 = '1.2'
    field_1_3 = '1.3'
    field_1_4 = '1.4'
    field_1_5 = '1.5'
    field_1_6 = '1.6'
    field_1_7 = '1.7'
    field_1_8 = '1.8'
    field_1_9 = '1.9'
    field_1_10 = '1.10'
    field_1_11 = '1.11'
    field_1_12 = '1.12'
    field_1_13 = '1.13'
    field_1_14 = '1.14'


class XsBoolean(RtcBaseModel):
    __root__: bool


class XsDate(RtcBaseModel):
    __root__: str


class XsDouble(RtcBaseModel):
    __root__: float


class XsFloat(RtcBaseModel):
    __root__: float


class XsGDay(RtcBaseModel):
    __root__: str


class XsGMonth(RtcBaseModel):
    __root__: str


class XsGMonthDay(RtcBaseModel):
    __root__: str


class XsInt(RtcBaseModel):
    __root__: int = Field(..., ge=-2147483648, le=2147483647)


class XsNonNegativeInteger(RtcBaseModel):
    __root__: int = Field(..., ge=0)


class XsPositiveInteger(RtcBaseModel):
    __root__: int = Field(..., ge=1)


class XsString(RtcBaseModel):
    __root__: str


class XsTime(RtcBaseModel):
    __root__: str


class BoolPropertyComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_key: XsString
    attr_value: XsBoolean
    description: Optional[XsString] = None


class ColumnIdsComplexType(RtcBaseModel):
    """
    Column names for columns A through Z.
    """

    class Config:
        extra = Extra.forbid

    attr_A: XsString
    attr_B: Optional[XsString] = None
    attr_C: Optional[XsString] = None
    attr_D: Optional[XsString] = None
    attr_E: Optional[XsString] = None
    attr_F: Optional[XsString] = None
    attr_G: Optional[XsString] = None
    attr_H: Optional[XsString] = None
    attr_I: Optional[XsString] = None
    attr_J: Optional[XsString] = None
    attr_K: Optional[XsString] = None
    attr_L: Optional[XsString] = None
    attr_M: Optional[XsString] = None
    attr_N: Optional[XsString] = None
    attr_O: Optional[XsString] = None
    attr_P: Optional[XsString] = None
    attr_Q: Optional[XsString] = None
    attr_R: Optional[XsString] = None
    attr_S: Optional[XsString] = None
    attr_T: Optional[XsString] = None
    attr_U: Optional[XsString] = None
    attr_V: Optional[XsString] = None
    attr_W: Optional[XsString] = None
    attr_X: Optional[XsString] = None
    attr_Y: Optional[XsString] = None
    attr_Z: Optional[XsString] = None


class ColumnMetaDataComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_A: XsString
    attr_B: Optional[XsString] = None
    attr_C: Optional[XsString] = None
    attr_D: Optional[XsString] = None
    attr_E: Optional[XsString] = None
    attr_F: Optional[XsString] = None
    attr_G: Optional[XsString] = None
    attr_H: Optional[XsString] = None
    attr_I: Optional[XsString] = None
    attr_J: Optional[XsString] = None
    attr_K: Optional[XsString] = None
    attr_L: Optional[XsString] = None
    attr_M: Optional[XsString] = None
    attr_N: Optional[XsString] = None
    attr_O: Optional[XsString] = None
    attr_P: Optional[XsString] = None
    attr_Q: Optional[XsString] = None
    attr_R: Optional[XsString] = None
    attr_S: Optional[XsString] = None
    attr_T: Optional[XsString] = None
    attr_U: Optional[XsString] = None
    attr_V: Optional[XsString] = None
    attr_W: Optional[XsString] = None
    attr_X: Optional[XsString] = None
    attr_Y: Optional[XsString] = None
    attr_Z: Optional[XsString] = None
    attr_id: Optional[XsString] = None
    attr_type: Optional[ValueTypeEnumStringType] = None


class ColumnTypesComplexType(RtcBaseModel):
    """
    Value-types in the columns A through Z. If no type specified, type 'String' is assumed.
    """

    class Config:
        extra = Extra.forbid

    attr_A: ValueTypeEnumStringType
    attr_B: Optional[ValueTypeEnumStringType] = None
    attr_C: Optional[ValueTypeEnumStringType] = None
    attr_D: Optional[ValueTypeEnumStringType] = None
    attr_E: Optional[ValueTypeEnumStringType] = None
    attr_F: Optional[ValueTypeEnumStringType] = None
    attr_G: Optional[ValueTypeEnumStringType] = None
    attr_H: Optional[ValueTypeEnumStringType] = None
    attr_I: Optional[ValueTypeEnumStringType] = None
    attr_J: Optional[ValueTypeEnumStringType] = None
    attr_K: Optional[ValueTypeEnumStringType] = None
    attr_L: Optional[ValueTypeEnumStringType] = None
    attr_M: Optional[ValueTypeEnumStringType] = None
    attr_N: Optional[ValueTypeEnumStringType] = None
    attr_O: Optional[ValueTypeEnumStringType] = None
    attr_P: Optional[ValueTypeEnumStringType] = None
    attr_Q: Optional[ValueTypeEnumStringType] = None
    attr_R: Optional[ValueTypeEnumStringType] = None
    attr_S: Optional[ValueTypeEnumStringType] = None
    attr_T: Optional[ValueTypeEnumStringType] = None
    attr_U: Optional[ValueTypeEnumStringType] = None
    attr_V: Optional[ValueTypeEnumStringType] = None
    attr_W: Optional[ValueTypeEnumStringType] = None
    attr_X: Optional[ValueTypeEnumStringType] = None
    attr_Y: Optional[ValueTypeEnumStringType] = None
    attr_Z: Optional[ValueTypeEnumStringType] = None


class DateTimeComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_date: DateType
    attr_time: TimeType


class DateTimePropertyComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_date: DateType
    attr_key: XsString
    attr_time: TimeType
    description: Optional[XsString] = None


class DoublePropertyComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_key: XsString
    attr_value: XsDouble
    description: Optional[XsString] = None


class EnsembleMemberComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_index: XsNonNegativeInteger
    attr_weight: Optional[XsDouble] = None


class EnsembleMemberRangeComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_end: Optional[XsNonNegativeInteger] = None
    attr_start: XsNonNegativeInteger
    attr_weight: Optional[XsDouble] = None


class EventComplexType(RtcBaseModel):
    """
    unlimited number of events with a constant timeStep.
                Each TimeSeries should contain at least one element (records).
                The date, time and value attributes are required, the
                quality flag is optional. 
    """

    class Config:
        extra = Extra.forbid

    attr_comment: Optional[XsString] = None
    attr_date: DateType
    attr_flag: Optional[XsInt] = None
    attr_flagSource: Optional[XsString] = None
    attr_time: TimeType
    attr_user: Optional[XsString] = None
    attr_value: XsDouble


class FloatPropertyComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_key: XsString
    attr_value: XsFloat
    description: Optional[XsString] = None


class HighLevelThresholdsComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_groupId: Optional[XsString] = None
    attr_groupName: Optional[XsString] = None
    attr_id: XsString
    attr_name: Optional[XsString] = None
    attr_value: XsFloat


class IntPropertyComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_key: XsString
    attr_value: XsInt
    description: Optional[XsString] = None


class PeriodConditionComplexType(RtcBaseModel):
    """
    A period condition. If a date is specified without a timezone, e.g. 2002-10-10T12:00:00, then it is assumed to be in UTC.
    """

    class Config:
        extra = Extra.forbid

    day: Optional[List[XsGDay]] = None
    endDate: Optional[DateTimeComplexType] = Field(
        None, description='End date and time for this period.'
    )
    endMonthDay: Optional[XsGMonthDay] = Field(
        None, description='End month and day of this season.'
    )
    month: Optional[List[XsGMonth]] = None
    monthDay: Optional[List[XsGMonthDay]] = None
    startDate: Optional[DateTimeComplexType] = Field(
        None, description='Start date and time for this period.'
    )
    startMonthDay: Optional[XsGMonthDay] = Field(
        None, description='Start month and day of this season.'
    )
    timeZone: Optional[TimeZoneSimpleType] = Field(None, description='Timezone')
    validAfterDate: Optional[DateTimeComplexType] = Field(
        None, description='Valid for entire period after this date and time.'
    )
    validBeforeDate: Optional[DateTimeComplexType] = Field(
        None, description='Valid for entire period prior to this date and time.'
    )


class RowComplexType(RtcBaseModel):
    """
    Values in the columns A through Z. The values are entered as strings, however the value-type in each column should match the type as specified with columnTypes for this column. This wil be checked while reading the xml-file. If no column-type specified, 'String' type is assumed.
    """

    class Config:
        extra = Extra.forbid

    attr_A: XsString
    attr_B: Optional[XsString] = None
    attr_C: Optional[XsString] = None
    attr_D: Optional[XsString] = None
    attr_E: Optional[XsString] = None
    attr_F: Optional[XsString] = None
    attr_G: Optional[XsString] = None
    attr_H: Optional[XsString] = None
    attr_I: Optional[XsString] = None
    attr_J: Optional[XsString] = None
    attr_K: Optional[XsString] = None
    attr_L: Optional[XsString] = None
    attr_M: Optional[XsString] = None
    attr_N: Optional[XsString] = None
    attr_O: Optional[XsString] = None
    attr_P: Optional[XsString] = None
    attr_Q: Optional[XsString] = None
    attr_R: Optional[XsString] = None
    attr_S: Optional[XsString] = None
    attr_T: Optional[XsString] = None
    attr_U: Optional[XsString] = None
    attr_V: Optional[XsString] = None
    attr_W: Optional[XsString] = None
    attr_X: Optional[XsString] = None
    attr_Y: Optional[XsString] = None
    attr_Z: Optional[XsString] = None


class StringPropertyComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    attr_key: XsString
    attr_value: XsString
    description: Optional[XsString] = None


class ThresholdComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    highLevelThreshold: List[HighLevelThresholdsComplexType] = Field(..., min_items=1)


class TimeStepComplexType(RtcBaseModel):
    """
    The time unit element has three attributes, unit and divider and multiplier. the unit is second, minute, hour, week, month year. The divider attribute is optional (default = 1).
    """

    class Config:
        extra = Extra.forbid

    attr_divider: Optional[XsPositiveInteger] = None
    attr_multiplier: Optional[XsNonNegativeInteger] = None
    attr_unit: TimeStepUnitEnumStringType


class TimeStepUnitComplexType(RtcBaseModel):
    """
    The time unit element has two attributes, unit and divider. the unit is required and can be 1, 2, 3, or 4 meaning: year, month, day and hour. The divider attribute is optional (default = 1).
    """

    class Config:
        extra = Extra.forbid

    attr_divider: Optional[XsInt] = None
    attr_unit: AttrUnit


class ArchiveTimeSeriesSetComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    ensembleId: Optional[IdStringType] = Field(
        None,
        description="Optional field for running ensembles. Ensemble id's in a time series set will override ensemble id's defined in the workflow.",
    )
    locationId: List[IdStringType] = Field(..., min_items=1)
    moduleInstanceId: IdStringType
    parameterId: IdStringType
    qualifierId: Optional[List[IdStringType]] = None
    timeSeriesType: TimeSeriesTypeEnumStringType
    timeStep: TimeStepComplexType


class GlobalTableComplexType(RtcBaseModel):
    """
    Intended for the configuration of any table
    """

    class Config:
        extra = Extra.forbid

    columnIds: Optional[ColumnIdsComplexType] = None
    columnMetaData: Optional[List[ColumnMetaDataComplexType]] = None
    columnTypes: Optional[ColumnTypesComplexType] = None
    columnUnits: Optional[ColumnIdsComplexType] = None
    row: List[RowComplexType] = Field(..., min_items=1)


class HeaderComplexType(RtcBaseModel):
    """
    The header is used to specify the link to the location
                and the contents
    """

    class Config:
        extra = Extra.forbid

    creationDate: Optional[XsDate] = Field(
        None,
        description='Date on which this TimeSeries was\n                        created',
    )
    creationTime: Optional[XsTime] = Field(
        None,
        description='Time on which this TimeSeries was\n                        created',
    )
    endDate: DateTimeComplexType = Field(..., description='date/time of the last event')
    ensembleId: Optional[IdString] = Field(
        None,
        description="\n\t\t\t\t\t\t\tSince version 1.4\n\t\t\t\t\t\t\tAn ensemble forecast consists of a number of simulations made by making small changes to the\n\t\t\t\t\t\t\testimate of the current state used to initialize the simulation. These small changes are\n\t\t\t\t\t\t\tdesigned to reflect the uncertainty in the estimate. Every simulation has it's own ensembleMemberIndex\n\t\t\t\t\t\t\tWhen specified the ensembleMemberIndex is required\n\t\t\t\t\t\t",
    )
    ensembleMemberId: Optional[IdString] = Field(
        None,
        description="\n\t\t\t\t\t\t\t\tSince version 1.10 An ensemble forecast consists of a number of simulations made by making small changes to the estimate of the current state used to initialize the simulation. These small changes are designed to reflect the uncertainty in the estimate. Every simulation has it's own ensembleMemberId. Ensemble id is not required when the ensembleMemberId is specified\n\t\t\t\t\t\t\t",
    )
    ensembleMemberIndex: Optional[XsNonNegativeInteger] = Field(
        None,
        description="\n\t\t\t\t\t\t\t\tSince version 1.4 An ensemble forecast consists of a number of simulations made by making small changes to the estimate of the current state used to initialize the simulation. These small changes are designed to reflect the uncertainty in the estimate. Every simulation has it's own ensembleMemberIndex. Ensemble id is not required when the ensembleMemberIndex is specified\n\t\t\t\t\t\t\t",
    )
    fileDescription: Optional[XsString] = Field(
        None,
        description='Description of (the content of)\n                        this file',
    )
    forecastDate: Optional[DateTimeComplexType] = Field(
        None,
        description='\n\t\t\t\t\t\tSince version 1.5\n\t\t\t\t\t\tdate/time of the forecast. By default the forecastDate equals the start time',
    )
    lat: Optional[XsDouble] = Field(None, description='Latitude of station')
    locationId: LocationIdSimpleType
    lon: Optional[XsDouble] = Field(None, description='Longitude of station')
    longName: Optional[XsString] = Field(
        None, description='Optional long (descriptive) name'
    )
    missVal: XsDouble = Field(
        ...,
        description='Missing value definition for this TimeSeries. Defaults to NaN if left empty',
    )
    parameterId: ParameterSimpleType
    qualifierId: Optional[List[IdString]] = None
    region: Optional[XsString] = Field(
        None,
        description="code/description of the region. Needed if the id's\n                        can be the same in different regions.",
    )
    sourceOrganisation: Optional[XsString] = None
    sourceSystem: Optional[XsString] = None
    startDate: DateTimeComplexType = Field(
        ..., description='date/time of the first event'
    )
    stationName: Optional[NameString] = Field(None, description='Station name')
    thresholds: Optional[ThresholdComplexType] = None
    timeStep: TimeStepComplexType = Field(
        ..., description='The timeStep element provides three choices'
    )
    type: TimeSeriesType = Field(
        ...,
        description='\n                        Type of data, either accumulative or instantaneous.\n                        For accumulative data the time/date of the event is\n                        the moment at which the data was gathered.\n                    ',
    )
    units: Optional[XsString] = Field(
        None, description='Optional string that identifies the units used'
    )
    x: Optional[XsDouble] = Field(None, description='X coordinate of station')
    y: Optional[XsDouble] = Field(None, description='Y coordinate of station')
    z: Optional[XsDouble] = Field(None, description='Z coordinate of station')


class PropertiesComplexType(RtcBaseModel):
    class Config:
        extra = Extra.forbid

    bool: Optional[List[BoolPropertyComplexType]] = None
    dateTime: Optional[List[DateTimePropertyComplexType]] = None
    description: Optional[XsString] = None
    double: Optional[List[DoublePropertyComplexType]] = None
    float: Optional[List[FloatPropertyComplexType]] = None
    int: Optional[List[IntPropertyComplexType]] = None
    string: Optional[List[StringPropertyComplexType]] = None


class TimeSeriesComplexType(RtcBaseModel):
    """
    Time series data represent data collected over a given
                period of time at a specific location
    """

    class Config:
        extra = Extra.forbid

    comment: Optional[CommentString] = Field(
        None,
        description='use this field as a notebook to add comments, suggestions\n                        description of data entered etc.',
    )
    event: Optional[List[EventComplexType]] = None
    header: HeaderComplexType = Field(
        ...,
        description='\n                        The header is used to specify the link to the location\n                        and the contents',
    )
    properties: Optional[List[PropertiesComplexType]] = None


class TimeSeriesCollectionComplexType(RtcBaseModel):
    """
    Time series data represent data collected over a given period of time at a specific location
    """

    class Config:
        extra = Extra.forbid

    attr_version: Optional[VersionString] = None
    series: List[TimeSeriesComplexType] = Field(..., min_items=1)
    timeZone: Optional[TimeZoneSimpleType] = None


class Model(RtcBaseModel):
    """
    JSON Schema generated by XMLSpy v2019 rel. 3 sp1 (x64) (http://www.altova.com)
    """

    class Config:
        extra = Extra.forbid

    attr_xmlns: Optional[Any] = 'http://www.wldelft.nl/fews/PI'
    attr_xmlns_xs: Optional[Any] = Field(
        'http://www.w3.org/2001/XMLSchema', alias='attr_xmlns:xs'
    )
    TimeSeries: Optional[_.TimeSeries] = None
