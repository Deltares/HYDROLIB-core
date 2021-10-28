# Glossary
The list below is a nonexhaustive list of terminology and concepts used in HYDROLIB(-core) and Delft3D Flexible Mesh.

## A
---

## B
---
### BC file
Input file containing the actual forcing data for model forcings specified elsewhere in the model input, for example time series or astronomical components.
Originates from boundary conditions as specified in the [external forcings file](#external-forcings-file), but nowadays also used in [structure files](#structure-file). More details about the syntax and the various supported function types in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.E.2.3).

### Boundary condition
Flow (or constituent) boundary condition that forces a [D-Flow FM](#d-flow-fm) model, such as waterlevel and discharge boundary conditions. Defined in the [external forcings file](#external-forcings-file). More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.C.5.2.1).

### Branch
The network edges in a network topology of 1D models. The computational [grid](#grid) points are positioned on these branches using branch id and a [chainage](#chainage) value.

### Branch Id
Identification text string for a particular [branch](#branch) in a 1D network.

## C
---
### Chainage
The distance along a 1D network [branch](#branch) to define a specific location on that branch. Always used in combination with a [branch Id](#branch-id).

### CF conventions
Established metadata conventions for storing all kinds of data, e.g., model input and output, in NetCDF files. More details on: https://cfconventions.org/.
HYDROLIB-core and Delft3D Flexible Mesh rely on CF, and extend this with [UGRID conventions](#ugrid-conventions) where unstructured grids are applicable.

### Computational backend
Computational core, also called kernel. The program/library of simulation software that does the actual calculations. Often also available with a graphical user interface on top of it.

### Cross section files
Input files for [D-Flow FM](#d-flow-fm) that define the 1D network's cross sections.
Two parts: [cross section definition file](#cross-section-definition-file) and [cross section location files](#cross-section-location-file). Not to be confused with [observation cross section files](#observation-cross-section-file)!

### Cross section definition file
Input file for [D-Flow FM](#d-flow-fm) that defines the various cross section shapes in a model with a 1D network. Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1).

### Cross section location file
Input file for [D-Flow FM](#d-flow-fm) that defines the location of cross section shapes in a model with a 1D network. Each location refers to a (possible shared) [cross section definition](#cross-section-definition-file). Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.2).

## D
---
### Deltares conventions
A proposal for additional NetCDF conventions that build on the existing [UGRID conventions](#ugrid-conventions), intended to properly describe 1D network topologies as a coordinate space on which 1D computational grids are defined. Also 1D2D grid couplings are included.
More details in: the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.B.2).

### D-Flow FM
D-Flow Flexible Mesh. The computational backend that solves 1D/2D/3D hydrodynamics in the Delf3D Flexible Mesh Suite.
Toplevel input is the [MDU file](#mdu-file). More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf).

### D-HYDRO Suite 1D2D (Beta)
Integral software suite for hydraulic 1D2D modelling, including rainfall runoff and realtime control.
More details on: https://www.deltares.nl/nl/d-hydro-suite-1d2d-beta/.

### DIMR
Deltares Integrated Model Runner. Executable/library that runs [integrated models](#integrated-model) by coupling multiple [computational backends](#computational-backend) in a simulation timeloop. Uses a single [DIMR config file](#dimr-config-file) as input.

### DIMR config file
Input file for [DIMR](#dimr) (typically ``dimr_config.xml``) for an [integrated model](#integrated-model) run, describing which models are coupled and which quantities need to be exchanged.

## E
---
### Edge (mesh)
A geometrical "line" in a 1D, 2D or 3D mesh. Connects two [mesh nodes](#node-mesh) as its end points. Building block of the [UGRID-conventions](#ugrid-conventions).

### External forcings file
Input file for [D-Flow FM](#d-flow-fm) describing model forcings such as [boundary conditions](#boundary-condition), [laterals](#lateral) and [meteo](#meteo). Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2).

## F
---
### Face (mesh)
A geometrical "cell" in a 2D mesh. Formed by 3 or more [mesh nodes](#node-mesh) as its vertices. Building block of the [UGRID-conventions](#ugrid-conventions).

### Flow link
An open connection/interface between two [flow nodes](#flow-node) in the [staggered](#staggered-grid) [D-Flow FM](#d-flow-fm) model grid. Is the same as a "velocity point", and corresponds with (but is not equal to) an [edge](#edge-mesh), both in 1D and in 2D. In 3D a flow link corresponds with a 3D [face](#face-mesh) between two [volumes](#volume-mesh).

### Flow node
A single finite volume "cell" in the [staggered](#staggered-grid) [D-Flow FM](#d-flow-fm) model grid. Is the same as a "pressure point", and is in fact a [face](#face-mesh) in 2D/3D or a [node](#node-mesh) in 1D.

## G
---
### Grid
The computational grid on which a flow simulation is done. The grid for [D-Flow FM](#d-flow-fm) is defined in an input [net file](#net-file]), and also appears (slightly differently) in the output [map file](#map-file).

### Grid snapping
The snapping of [D-Flow FM](#d-flow-fm) model input in x,y-coordinates to discrete locations in the [staggered model grid](#staggered-grid). This process makes most model input independent of the chosen model grid and grid resolution.
Snapping is done either to (sets of) [flow nodes](#flow-node) or (sequence of) [flow links](#flow-link), depending on whether pressure-point data or velocity-point data is concerned.

## H
---
### His file
Output file of [D-Flow FM](#d-flow-fm) containing model results as time series on a specific set of discrete locations, which are typically the hydraulic structures, observation stations and more.
More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.F.3.1).

## I
---
### Integrated model
Model consisting of more than one model. Typically used when multiple [computational backends](#computational-backend) are coupled, for example [D-Flow FM](#d-flow-fm) and [Rainfall Runoff](#rainfall-runoff) or [D-Flow FM](#d-flow-fm) and [Real Time Control](#real-time-control).
Integrated models can be run using the [Deltares Integrated Model Runner (DIMR)](#dimr).

### INI-files
Delft3D FM uses several input files that are formatted in an INI-like syntax. The abstract syntax depends on the particular file type, see: [cross section files](#cross-section-files), [initial field file](#initial-field-file), [external forcings file](#external-forcings-file), [MDU file](#mdu-file), [observation files](#observation-files), [rougness file](#roughness-file), [structure file](#structure-file).

### Initial field file
Input file for [D-Flow FM](#d-flow-fm) describing initial conditions and other spatially varying parameter fields.
Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.D.2).

## J
---

## K
---

## L
---
### Lateral
Lateral discharge in [D-Flow FM](#d-flow-fm), which acts as a source (or sink) of volume. Defined in the [external forcings file](#external-forcings-file). The actual forcing data may come from timeseries in a [.bc file](#bc-file) or from [RR](#rainfall-runoff) a coupled/integrated model. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.C.5.2.2).

## M
---
### Map file
Output file of [D-Flow FM](#d-flow-fm) containing the model results on all grid points.
More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.F.3.1).

### MDU file
Main input file of [D-Flow FM](#d-flow-fm). Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#appendix.A).

### meteo
Meteorological forcings of a model. Typically sources (or sinks) of volume via precipitation and evaporation, or forcing via wind. For [D-Flow FM](#d-flow-fm) defined in the [external forcings file](#external-forcings-file). More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.C.5.2.3).

### mesh
See [grid](#grid).

## N
---
### Net file
Or grid file. Input file for [D-Flow FM](#d-flow-fm) containing the computational model grid. Format is NetCDF, adhering to [CF](#cf-conventions)- and [UGRID](#ugrid-conventions)-conventions, and optionally also the [Deltares-extension](#deltares-conventions) for 1D network topology and geometry.

### NetCDF
File format used by HYDROLIB-core and Delft3D Flexible Mesh for the model input grid and for model results in output files. These files typically adhere to the [CF conventions](#CF-conventions) and sometimes [UGRID conventions](#UGRID-conventions).

### Node (mesh)
A geometrical "point" in a 1D, 2D or 3D mesh. Defined by x- and y-coordinate, in 3D also a z-coordinate. Can be connected by [mesh edges](#edge-mesh), and can form the vertices of a [mesh face](#face-mesh). Building block of the [UGRID-conventions](#ugrid-conventions).

## O
---
### Observation files
Files that define the model locations for which output should be produced in the [his file](#his-file).
Two types: [observation point file](#observation-point-file) and [observation cross section file](#observation-cross-section-file).

### Observation cross section file
Input file for [D-Flow FM](#d-flow-fm) that describes the model locations for which (cumulative) flow "flux" output should be produced in the [his file](#his-file). For example: cumulative discharge, salinity transport. Applies both to 1D, 2D, 1D2D and 3D models. Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.F.2.4.2).

### Observation point file
Input file for [D-Flow FM](#d-flow-fm) that describes the model point locations for which local output should be produced in the [his file](#his-file). For example: waterlevel, velocity vector/magnitude, tracer concentration as instantanous values. Applies both to 1D, 2D, 1D2D and 3D models. Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.F.2.2.1).


## P
---
### Polyline file
File containing a sequence of polylines in model coordinates. Each polyline has header lines with a label and row+column count, and at least a list of x, y-points. More than 2 columns may be present (z, data1, ...) for particular model inputs, see for example the [fixed weir file](#fixed-weir-file). More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.C.2).

### Polygon file
See [polyline file](#polyline-file). The point sequences are interpreted as closed polygons.

## Q
---

## R
---
### Rainfall runoff
RR for short. The computational backend that solves lumped rainfall runoff, offering various runoff concepts. Toplevel input is the ``sobek_3b.fnm`` file. Part of the D-Hydrology software module. More details on: https://www.deltares.nl/en/software/module/d-hydrology.

### Real Time Control
RTC for short. The computational backend for real-time control of hydraulic model components (typically hydraulic structures).
Toplevel input is in various ``rtc*.xml`` files. Part of the D-Real Time Control software module. More details on: https://www.deltares.nl/en/software/module/d-real-time-control.

### Roughness file
Input file for [D-Flow FM](#d-flow-fm) describing roughness values on the 1D network.
Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.C.15).

## S
---
### Sample file
File containing an unstructured set of sample point values. Typically used as input file for initial fields or other spatially varying fields in the [initial fields file](#initial-field-file). More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.C.3).

### Staggered grid
Discretization method used in [D-Flow FM](#d-flow-fm) where the PDE variables are not all defined on the same topological grid locations. Water level, concentrations and other volume-related variables are defined on the pressure points (also: [flow nodes](#flow-node)), and the fluxes and other transport-related variables are defined on the velocity points (also: [flow links](#flow-link)).

### Structure file
Input file for [D-Flow FM](#d-flow-fm) containing the hydraulic structures. Format is INI-like. More details in the [Delft3D FM User Manual](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.C.12).

## T
---

## U
---

### UGRID conventions
Metadata conventions for storing unstructured grids in NetCDF files. More details on: http://ugrid-conventions.github.io/ugrid-conventions/.

## V
---
### volume (mesh)
A geometrical "cell" in a 3D mesh. Formed by 4 or more [mesh nodes](#node-mesh) as its vertices (or: 4 or more [mesh faces](#face-mesh) as its "sides"). Building block of the [UGRID-conventions](#ugrid-conventions).


## W
---

## X
---
### XYZ file
See [sample file](#sample-file).

## Y
---

## Z
---


 [Delft3D FM User Manual]: https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf
 