# generated by datamodel-codegen:
#   filename:  rtcDataConfig.json
#   timestamp: 2022-09-27T13:10:33+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Extra, Field

from . import _


class AggregationTypeEnumStringType(str, Enum):
    BLOCK = 'BLOCK'
    LINEAR = 'LINEAR'


class EnsembleModeEnumStringType(str, Enum):
    JOINT = 'JOINT'
    TREE = 'TREE'
    INDEPENDENT = 'INDEPENDENT'


class ExternalBooleanSimpleTypeItem(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str = Field(..., regex='^([\\$][\\(-_a-z]+[\\$])$')


class ExternalBooleanSimpleType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: Union[bool, ExternalBooleanSimpleTypeItem]


class ExternalIntegerSimpleTypeItem(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str = Field(..., regex='^([\\$][\\(-_a-z]+[\\$])$')


class ExternalIntegerSimpleType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: Union[int, ExternalIntegerSimpleTypeItem]


class ExternalParameterSimpleTypeItem(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str = Field(..., regex='^([#-\\$][\\(-_a-z]+[#-\\$])$')


class ExternalParameterSimpleType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: Union[float, ExternalParameterSimpleTypeItem]


class PIExtrapolationOptionEnumStringType(str, Enum):
    BLOCK = 'BLOCK'
    PERIODIC = 'PERIODIC'


class PIInterpolationOptionEnumStringType(str, Enum):
    BLOCK = 'BLOCK'
    LINEAR = 'LINEAR'


class AttrValidation(str, Enum):
    NO = 'NO'
    STATE = 'STATE'
    UPDATE = 'UPDATE'
    UPDATE_EXCEPT_STATE = 'UPDATE_EXCEPT_STATE'
    FORECAST = 'FORECAST'
    FORECAST_EXCEPT_T0 = 'FORECAST_EXCEPT_T0'
    ALL = 'ALL'
    ALL_EXCEPT_STATE = 'ALL_EXCEPT_STATE'


class SeparatorEnumStringType(str, Enum):
    _ = '.'
    __1 = ','
    __2 = ';'


class TimeSeriesSimpleType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str = Field(..., min_length=1)


class TimeZoneSimpleType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: float = Field(
        ...,
        description='The timeZone (in decimal hours shift from GMT)\n            e.g. -1.0 or 3.5. If not present GMT is assumed',
    )


class UnitEnumStringType(str, Enum):
    m = 'm'
    m_2 = 'm^2'
    m_3 = 'm^3'
    m_3_s = 'm^3/s'
    s = 's'


class VariableTypeEnumStringType(str, Enum):
    CONTINUOUS = 'CONTINUOUS'
    INTEGER = 'INTEGER'
    TIMEINSTANCE = 'TIMEINSTANCE'


class DateType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str = Field(
        ..., regex='^([\\d][\\d][\\d][\\d]\\-[\\d][\\d]\\-[\\d][\\d])$'
    )


class TimeSeriesType(str, Enum):
    """
    Type of data, either accumulative or instantaneous.
                        For accumulative data the time/date of the event is
                        the moment at which the data was gathered.
            
    """

    accumulative = 'accumulative'
    instantaneous = 'instantaneous'


class TimeStepUnitEnumStringType(str, Enum):
    second = 'second'
    minute = 'minute'
    hour = 'hour'
    day = 'day'
    week = 'week'


class TimeType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str = Field(..., regex='^([\\d][\\d]\\:[\\d][\\d]\\:[\\d][\\d])$')


class XsBoolean(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: bool


class XsPositiveInteger(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: int = Field(..., ge=1)


class XsString(BaseModel):
    class Config:
        allow_population_by_field_name = True

    __root__: str


class CSVTimeSeriesFileComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    attr_adjointOutput: Optional[XsBoolean] = None
    attr_decimalSeparator: Optional[SeparatorEnumStringType] = None
    attr_delimiter: Optional[SeparatorEnumStringType] = None


class DateTimeComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    attr_date: DateType
    attr_time: TimeType


class OpenMIExchangeItemComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    elementId: XsString = Field(
        ..., description='OpenMI element ID, corresponds to the locationId'
    )
    quantityId: XsString = Field(
        ..., description='OpenMI quantity ID, corresponds to the parameterId'
    )
    unit: UnitEnumStringType = Field(..., description='Selection of supported units')


class PITimeSeriesExportFileComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    adjointOutput: Optional[XsBoolean] = None
    timeSeriesFile: XsString = Field(
        ..., description='Name of the file containing timeseries data. '
    )
    useBinFile: Optional[XsBoolean] = Field(
        None,
        description='When true the events in the PI time series file are read from / written into a binairy file instead of the xml file.\nThe xml file only contains the time series headers and optionally a time zone.\nThe binairy file has the same name as the xml file only the extension is "bin" instead of "xml". The byte order in the bin file is always Intel x86.\n                ',
    )


class PITimeSeriesImportFileComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    timeSeriesFile: XsString = Field(
        ..., description='Name of the file containing timeseries data. '
    )
    useBinFile: Optional[XsBoolean] = Field(
        None,
        description='OBSOLETE. Still here for backwards compatibility. Remove after next release.',
    )


class TimeStepComplexType(BaseModel):
    """
    The timeunit element has three attributes, unit and devider and multiplier.
            the unit is second, minute, hour, week, month year.
            The divider attribute is optional (default = 1).
    """

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    attr_divider: Optional[XsPositiveInteger] = None
    attr_multiplier: Optional[XsPositiveInteger] = None
    attr_unit: TimeStepUnitEnumStringType


class PITimeSeriesComplexType(BaseModel):
    """
    The header is used to specify the link to the location
                and the contents
    """

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    locationId: XsString = Field(
        ..., description='Location ID in Delft-FEWS PI-XML file'
    )
    parameterId: XsString = Field(
        ..., description='Parameter ID in Delft-FEWS PI-XML file'
    )
    interpolationOption: Optional[PIInterpolationOptionEnumStringType] = Field(
        None, description='Interpolation option in data import'
    )
    extrapolationOption: Optional[PIExtrapolationOptionEnumStringType] = Field(
        None, description='Extrapolation option in data import'
    )
    qualifierId: Optional[List[XsString]] = None
    timeStep: Optional[TimeStepComplexType] = Field(
        None,
        description='Equidistant time step of time series with optional multiplier of divider',
    )
    unit: Optional[XsString] = Field(
        None,
        description='Optional check for this unit during import, write this unit optionally when export the time series',
    )


class RtcTimeSeriesComplexType(BaseModel):
    """
    The header is used to specify the link to the location
                and the contents
    """

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    attr_id: str = Field(..., min_length=1)
    attr_validation: Optional[AttrValidation] = None
    attr_vectorLength: Optional[int] = Field(None, ge=1, le=2147483647)
    OpenMIExchangeItem: Optional[OpenMIExchangeItemComplexType] = Field(
        None,
        description='Time series definition of the OpenMI format for the online coupling of models during runtime',
    )
    PITimeSeries: Optional[PITimeSeriesComplexType] = Field(
        None,
        description='Time series definition of the PI XML time series format of Delft-FEWS',
    )


class RtcSeriesExportComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    CSVTimeSeriesFile: Optional[CSVTimeSeriesFileComplexType] = Field(
        None,
        description='Comma-separated file for data exports. Note that this option is only used in the exportSeries element. If selected, all available time series will be exported.',
    )
    PITimeSeriesFile: Optional[PITimeSeriesExportFileComplexType] = None
    timeSeries: List[RtcTimeSeriesComplexType] = Field(..., min_items=1)


class RtcSeriesImportComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    PITimeSeriesFile: Optional[PITimeSeriesImportFileComplexType] = None
    timeSeries: List[RtcTimeSeriesComplexType] = Field(..., min_items=1)


class RtcDataConfigComplexType(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    importSeries: RtcSeriesImportComplexType = Field(
        ...,
        description='Import time series RTC-Tools imports from XML files or other interfaces',
    )
    exportSeries: RtcSeriesExportComplexType = Field(
        ...,
        description='Export time series RTC-Tools genenerates and exports to XML or csv files or supplies to other applications via other interfaces',
    )


class Model(BaseModel):
    """
    JSON Schema generated by XMLSpy v2019 rel. 3 sp1 (x64) (http://www.altova.com)
    """

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    attr_xmlns: Optional[Any] = 'http://www.wldelft.nl/fews'
    attr_xmlns_xs: Optional[Any] = Field(
        'http://www.w3.org/2001/XMLSchema', alias='attr_xmlns:xs'
    )
    rtcDataConfig: Optional[_.RtcDataConfig] = None
