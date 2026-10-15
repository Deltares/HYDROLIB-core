# Initial and parameter field files
The inifield file contains the initial conditions and spatial parameter input fields
for a [D-Flow FM](../../glossary.md#d-flow-fm) model.

Generic parsing and serializing functionality comes from the generic hydrolib.core.dflowfm.ini modules.

The inifield file is represented by the classes below.

The `[Initial]` and `[Parameter]` blocks share their field validation with the `[Meteo]` /
`[Spatial]` blocks of the [external forcings file](ext.md); see the
[class hierarchy diagram](ext.md#class-hierarchy) for how the shared validator mixins and base
classes fit together.

## Model
::: hydrolib.core.dflowfm.inifield.models
