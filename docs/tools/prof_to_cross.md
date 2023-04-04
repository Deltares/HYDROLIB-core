prof_to_cross
=============
*Convert D-Flow FM legacy profile files to cross section files.*

Directly jump to [Usage](#Usage).

# Background
1D cross section specification in a D-Flow FM model used to go via two or three prof* files, the ones specified in the MDU file via `ProflocFile`, `ProfdefFile`
and optionally `ProfdefxyzFile`. They contain the location/placement and the type/geometry description, respectively.

Similar input is still needed, but now has the officially supported via .ini files.
These are the ones now specified in the MDU file via `CrsLocFile` and `CrsDefFile`.
## Automatic conversion choices
### Location
Location continues to be specified via original *x,y* coordinate, no branchId is available.

Vertical absolute placement (`ZMIN` vs. `shift`) still needs refinement.

### Type + conveyance
The following table lists the mapping from old to new cross section types:
|PROFTYPE|meaning|type in crsdef.ini|conveyanceType in crsdef.ini|
| :--- | :--- | :--- | :--- |
|1|`PIPE`|`circle`||N/A|
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
Not yet available in converter.

# Usage:

```bash
usage: prof_to_cross [-h] [--version] [--verbose] [--mdufile MDUFILE] [--proffiles [PROFFILE [PROFFILE ...]]]

```

# Arguments

|short|long|default|help|
| :--- | :--- | :--- | :--- |
|`-h`|`--help`||show this help message and exit|
|`-v`|`--version`||show program's version number and exit|
||`--verbose`||also print diagnostic information|
|`-m`|`--mdufile`|`None`|automatically take profile filenames from MDUFILE|
|`-p`|`--proffiles`|`None`|2 or 3 profile files: PROFLOCFILE PROFDEFFILE [PROFDEFXYZFILE]|