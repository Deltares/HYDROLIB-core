# Net/grid file
The computational grid for [D-Flow FM](glossary.md#d-flow-fm) is stored in the net file.
It is an unstructured grid, where 1D and 2D can be combined. The file format is [NetCDF](glossary.md#netcdf),
using the [CF](glossary.md#cf-conventions)-, [UGRID](glossary.md#ugrid-conventions)-
and [Deltares](glossary.md#deltares-conventions)-conventions.

The net file is represented by the classes below.

## Model
::: hydrolib.core.io.net.models
