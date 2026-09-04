# External forcings file
The external forcing .ext file contains the forcing data for a [D-Flow FM](../../glossary.md#d-flow-fm) model.
This includes open boundaries, lateral discharges, source/sink terms, bubble screens, and meteorological forcings.
The documentation below only concerns the 'new' format (`ExtForceFileNew` in the MDU file).

## Class hierarchy

The `[Meteo]` and `[Spatial]` blocks (this file) and the `[Initial]` / `[Parameter]` blocks
(the [initial field file](inifield.md)) are spatial-field blocks that share their field
validation. The shared logic lives in two plain validator mixins, while `INIBasedModel`
is mixed in only at the two concrete block bases.

```mermaid
classDiagram
    direction TB

    class INIBasedModel
    class OperandInterpolationValidators {
        <<mixin>>
    }
    class LocationTypeDataFileTypeValidators {
        <<mixin>>
    }
    class SpatialForcingBase {
        <<abstract>>
    }
    class AbstractSpatialField {
        <<abstract>>
    }
    class Meteo
    class Spatial
    class InitialField
    class ParameterField

    OperandInterpolationValidators <|-- SpatialForcingBase
    OperandInterpolationValidators <|-- AbstractSpatialField
    INIBasedModel <|-- SpatialForcingBase
    LocationTypeDataFileTypeValidators <|-- AbstractSpatialField
    INIBasedModel <|-- AbstractSpatialField
    SpatialForcingBase <|-- Meteo
    SpatialForcingBase <|-- Spatial
    LocationTypeDataFileTypeValidators <|-- Spatial
    AbstractSpatialField <|-- InitialField
    AbstractSpatialField <|-- ParameterField

    note for OperandInterpolationValidators "operand + interpolationMethod validators (all four blocks)"
    note for LocationTypeDataFileTypeValidators "locationType + dataFileType validators (not Meteo)"
    note for SpatialForcingBase "file-model resolution, shared comments, unknown-keyword policy"
    note for AbstractSpatialField "averagingType + datafile validators"
```

Reading the diagram:

- `OperandInterpolationValidators` and `LocationTypeDataFileTypeValidators` are **independent plain
  mixins** (not models, and neither inherits the other). The former holds the `operand` /
  `interpolationMethod` validators shared by all four blocks; the latter holds the `locationType` /
  `dataFileType` validators shared by `Spatial`, `InitialField` and `ParameterField` (not `Meteo`,
  which has neither field).
- `INIBasedModel` is inherited only by the two concrete block bases: `SpatialForcingBase`
  (`Meteo` / `Spatial`) and `AbstractSpatialField` (`InitialField` / `ParameterField`).
- Each block base inherits exactly the validator mixins it needs: `SpatialForcingBase` inherits
  `OperandInterpolationValidators`; `AbstractSpatialField` inherits both mixins; and `Spatial` adds
  `LocationTypeDataFileTypeValidators` on top of `SpatialForcingBase`.
- `averagingType` is validated per-class (`Spatial`, `AbstractSpatialField`) rather than in a shared
  mixin, because `Meteo` reaches `OperandInterpolationValidators` too and stores `averagingType` as a
  raw integer.

## Model
::: hydrolib.core.dflowfm.ext.models
