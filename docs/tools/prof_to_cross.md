prof_to_cross
=============
*Convert D-Flow FM legacy profile files to cross section files.*

Directly jump to [Commandline usage](#Commandline-usage).

# Background
1D cross section specification in a D-Flow FM model used to go via two or three prof* files,
the ones specified in the MDU file under `[geometry]` via `ProflocFile`, `ProfdefFile`
and optionally `ProfdefxyzFile`. They contain the location/placement and the type/geometry description, respectively.

Similar input is still needed, but now is officially supported via .ini files.
These are the ones now specified in the MDU file under `[geometry]` via `CrsLocFile` and `CrsDefFile`.

## Automatic conversion choices
prof_to_cross makes the following automatic conversion choices.
### Location
Location continues to be specified via original *x,y* coordinate, no branchId is available.

Vertical absolute placement (`ZMIN` in profile *definition* file) only has a basic conversion
(as direct `shift` in crosssection *location* file).

### Type + conveyance
The following table lists the mapping from old to new cross section types:

|Profdef TYPE|meaning|type in crsdef.ini|conveyanceType in crsdef.ini|
| :--- | :--- | :--- | :--- |
|1|`PIPE`|`circle`|N/A|
|2|`RECTAN , HYDRAD = AREA / PERIMETER`|`rectangle`|N/A|
|3|`RECTAN , HYDRAD = 1D ANALYTIC CONVEYANCE`|`rectangle`|N/A|
|4|`V-SHAPE , HYDRAD = AREA / PERIMETER`|`yz`|`lumped`|
|5|`V-SHAPE , HYDRAD = 1D ANALYTIC CONVEYANCE`|`yz`|`segmented`|
|6|`TRAPEZOID, HYDRAD = AREA / PERIMETER`|`yz`|`lumped`|
|7|`TRAPEZOID, HYDRAD = 1D ANALYTIC CONVEYANCE`|`yz`|`segmented`|
|100|`YZPROF , HYDRAD = AREA / PERIMETER`|`yz`|`lumped`|
|101|`YZPROF , HYDRAD = 1D ANALYTIC CONVEYANCE METHOD`|`yz`|`segmented`|
|200|`XYZPROF , HYDRAD = AREA / PERIMETER`|`xyz`|`lumped`|
|201|`XYZPROF , HYDRAD = 1D ANALYTIC CONVEYANCE METHOD`|`xyz`|`segmented`|

### Friction
The following table lists the mapping from old to new friction types:

|Profdef FRCTP|frictionType in crsdef.ini
| :--- | :--- |
|`0`|`Chezy`|
|`1`|`Manning`|
|`2`|`WallLawNikuradse` (a.k.a. White-Colebrook Delft3D-style)|
|`3`|`WhiteColebrook`|


# Commandline usage:
```bash
usage: python hydrolib/tools/prof_to_cross.py [-h] [--version] [--verbose] \
              [--mdufile MDUFILE] \
              [--proffiles [PROFFILE [PROFFILE ...]]]  \
              [--outfiles CRSLOCFILE CRSDEFFILE]
```

## Arguments

|short|long|default|help|
| :--- | :--- | :--- | :--- |
|`-h`|`--help`||show this help message and exit|
|`-v`|`--version`||show program's version number and exit|
||`--verbose`||also print diagnostic information|
|`-m`|`--mdufile`|`None`|automatically take profile filenames from MDUFILE|
|`-p`|`--proffiles`|`None`|2 or 3 profile files: PROFLOCFILE PROFDEFFILE [PROFDEFXYZFILE]|
|`-o`|`--outfiles` |`crsloc.ini crsdef.ini`|save cross section locations and definitions to specified filenames|

# Python usage:
```python
from hydrolib.tools import prof_to_cross

# Option 1: via MDU file:
prof_to_cross.prof_to_cross_from_mdu('FlowFM.mdu')

# Option 2: directly via profile files:
prof_to_cross.prof_to_cross('profloc.xyz', 'profdef.txt', 'profdefxyz.pliz')
```
