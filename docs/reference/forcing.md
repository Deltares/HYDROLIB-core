# Forcings .bc file
The forcings .bc files contain forcing data for point locations,
for example time series input for a boundary condition. Various
quantities and function types are supported.

The forcings file is represented by the classes below.

```mermaid
classDiagram
    class VerticalInterpolation {
        <<Enum>>
        +linear: str
        +log: str
        +block: str
    }

    class VerticalPositionType {
        <<Enum>>
        +percentage_bed: str
        +z_bed: str
        +z_datum: str
        +z_surf: str
    }

    class TimeInterpolation {
        <<Enum>>
        +linear: str
        +block_from: str
        +block_to: str
    }

    class QuantityUnitPair {
        +quantity: str
        +unit: str
        +vertpositionindex: Optional[int]
        +_to_properties()
    }

    class VectorQuantityUnitPairs {
        +vectorname: str
        +elementname: List[str]
        +quantityunitpair: List[QuantityUnitPair]
        +_validate_quantity_element_names()
        +_to_vectordefinition_string()
        +_to_properties()
    }

    class ScalarOrVectorQUP {
        <<Union>>
        +QuantityUnitPair
        +VectorQuantityUnitPairs
    }

    class ForcingBase {
        +name: str
        +function: str
        +quantityunitpair: List[ScalarOrVectorQUP]
        +_exclude_fields()
        +_supports_comments()
        +_duplicate_keys_as_list()
        +_validate_quantityunitpair()
        +_set_function()
        +validate()
        +_get_identifier()
        +_to_section()
    }

    class VectorForcingBase {
        +validate_and_update_quantityunitpairs()
        +_process_vectordefinition_or_check_quantityunitpairs()
        +_validate_vectordefinition_and_update_quantityunitpairs()
        +_find_and_pack_vector_qups()
        +_validate_vectorlength()
        +get_number_of_repetitions()
    }

    class TimeSeries {
        +function: str
        +timeinterpolation: TimeInterpolation
        +offset: float
        +factor: float
        +rename_keys()
    }

    class Harmonic {
        +function: str
        +factor: float
    }

    class HarmonicCorrection {
        +function: str
    }

    class Astronomic {
        +function: str
        +factor: float
    }

    class AstronomicCorrection {
        +function: str
    }

    class T3D {
        +function: str
        +offset: float
        +factor: float
        +vertpositions: List[float]
        +vertinterpolation: VerticalInterpolation
        +vertpositiontype: VerticalPositionType
        +timeinterpolation: TimeInterpolation
        +rename_keys()
    }

    class QHTable {
        +function: str
    }

    class Constant {
        +function: str
        +offset: float
        +factor: float
    }

    class ForcingGeneral {
        +fileversion: str
        +filetype: str
    }

    class RealTime {
        <<Enum>>
        +realtime: str
    }

    class ForcingData {
        <<Union>>
        +float
        +RealTime
        +ForcingModel
    }

    ScalarOrVectorQUP --> QuantityUnitPair
    ScalarOrVectorQUP --> VectorQuantityUnitPairs
    ScalarOrVectorQUP --> ForcingBase
    VerticalInterpolation --> ForcingBase
    VerticalPositionType --> T3D
    TimeInterpolation --> ForcingBase
    ForcingBase --> TimeSeries
    ForcingBase --> Harmonic
    ForcingBase --> HarmonicCorrection
    ForcingBase --> Astronomic
    ForcingBase --> AstronomicCorrection
    ForcingBase --> QHTable
    ForcingBase --> Constant
    QuantityUnitPair --> VectorQuantityUnitPairs
    ForcingBase <|-- VectorForcingBase
    VectorForcingBase --> T3D
    ForcingBase --> ForcingGeneral
    RealTime --> ForcingData
    ForcingModel --> ForcingData

```

## Model
::: hydrolib.core.dflowfm.bc.models
