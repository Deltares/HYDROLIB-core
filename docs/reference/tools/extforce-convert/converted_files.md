## External Forcing files: Before and after

This section shows how a typical legacy external forcings file looked before, and how the files look after running `ExternalForcingConverter`.

Notes
- Examples are illustrative. Exact fields depend on the specific quantity and converter used.
- Paths may be rewritten according to `path_style` and the MDU location.
- When unsupported quantities exist and `debug=True`, those entries remain in the legacy `.ext` file after `update()`; only supported ones are moved to the new files.

### Example project layout

Before conversion
```
project/
├─ model.mdu
└─ old-forcings.ext
```

After conversion
```
project/
├─ model.mdu                      # updated to reference new files
├─ new-external-forcing.ext       # ExtModel: boundary/lateral/meteo/sourcesink
├─ new-initial-conditions.ini     # IniFieldModel: initial/parameter entries (if any)
└─ new-structure.ini              # StructureModel: structures (if any)
```

### Example MDU file
#### before the 
```ini

[General]
Program                             = D-Flow FM                  # Program
Version                             = 1.2.100.66357       		 # Version number of computational kernel
FileVersion                         = 1.09                       # File format version (do not edit this)
PathsRelativeToParent               = 0                          # Default: 0. Whether or not (1/0) to resolve file names (e.g. inside the *.ext file) relative to their direct parent, instead of to the toplevel MDU working dir.


[geometry]
NetFile                             = my-project_FM_grid_20190603_net.nc         # Unstructured grid file *_net.nc
IniFieldFile                        = inifield.ini                               # Initial values and parameter fields file
StructureFile                       = structures.ini                             # Hydraulic structure file (*.ini)
...

[physics]
...
Salinity                            = 1                                         # Include salinity, (0=no, 1=yes)
...
Temperature                         = 5                                         # Include temperature (0: no, 1: only transport, 3: excess model of D3D, 5: composite (ocean) model)
...

[time]
RefDate                             = 20160101                                  # Reference date (yyyymmdd)

[external forcing]
ExtForceFile                        = my-project-FM_bnd.ext                                              # Old format for external forcings file *.ext, link with tim/cmp-format boundary conditions specification
ExtForceFileNew                     =                                                                     # New format for external forcings file *.ext, link with bc-format boundary conditions specification
```
- The MDU file is updated to reference the new files.
- If the converter detects unsupported quantities, the `ExtForceFile` entry is left in place and the unsupported 
  quantities are reported in the log.
- If all the quantities are converted the `ExtForceFile` entry is removed and the `ExtForceFileNew` entry is updated to 
  point to the new file.
- If the `ExtForceFileNew`/`IniFieldFile`/`StructureFile` already exist, the converter will append the new entries to the existing 
  file.
- If the `ExtForceFileNew`/`IniFieldFile`/`StructureFile` does not exist, the converter will create it, add the new 
  entries, save it, and update the MDU file to reference it.


### Before: legacy `.ext` (old format)
A minimal legacy file with two forcings (boundary water level and global rainfall). Values (e.g., `FILETYPE`, `METHOD`) may differ in your model.

```ini
* Example (old-style) external forcings file

QUANTITY=waterlevelbnd
FILENAME=OB_001_orgsize.pli
FILETYPE=4
METHOD=3
OPERAND=O

QUANTITY=rainfall_rate
FILENAME=rainschematic.tim
FILETYPE=7
METHOD=1
OPERAND=O
```

### After: new external forcings (`new-external-forcing.ext`)
Converted forcings are routed to the appropriate sections in the new ExtModel file. For example:

```ini
[General]
fileVersion = 1.00
fileType    = extForce

[boundary]
quantity    = waterlevelbnd
nodeId      = OB_001                    # derived from your boundary setup
forcingfile = BoundaryConditions.bc     # converter provides the correct BC file

[meteo]
Quantity        = rainfall_rate
LocationType    = global
ForcingFile     = rainschematic.tim
ForcingFileType = uniform
```

- Boundary/lateral/meteorology/source-sink entries go to `new-external-forcing.ext`.
- Initial/parameter fields go to `new-initial-conditions.ini`.
- Structures go to `new-structure.ini`.

### After: initial/parameter fields (`new-initial-conditions.ini`)
Only created and saved if there are converted initial or parameter entries.

```ini
[General]
fileVersion = 1.00
fileType    = inifield

[initial]
quantity = waterlevel
value    = 0.0

[parameter]
quantity = roughness
value    = 0.03
```

### After: structures (`new-structure.ini`)
Only created and saved if there are converted structures.

```ini
[General]
fileVersion = 1.00
fileType    = structure

[structure]
id       = weir_001
class    = weir
branchId = main_channel
chainage = 1234.0
```

### MDU references: before vs after
If an `MDUParser` is supplied (e.g., when using `from_mdu`), the MDU file is updated to reference the new files.

Before (simplified)
```ini
[external forcing]
ExtForceFile = old-forcings.ext
```

After (simplified)
```ini
[external forcing]
ExtForceFileNew = new-external-forcing.ext

[geometry]
IniFieldFile   = new-initial-conditions.ini    ; only if inifield has entries
StructureFile  = new-structure.ini             ; only if structures exist
```

### Backups and cleanup
- `save(backup=True)` creates `.bak` backups for files that will be overwritten.
- `clean()` removes any converter-reported legacy artifacts (e.g., generated `.tim` files) and, if no unsupported quantities remain, deletes the legacy `old-forcings.ext`.


### Legacy files removed by ExternalForcingConverter.clean

The `clean()` method performs two types of removals after a successful conversion:

1) Converter-reported legacy artifacts
- What: Any files recorded in `converter.legacy_files` during `update()`.
- Source: Each concrete converter (boundary conditions, sources/sinks, etc.) adds to this list when it encounters legacy input files that are no longer needed after conversion.
- Typical examples (non-exhaustive):
  - `.tim` time-series files referenced by the legacy `.ext` for boundary or source/sink quantities.
  - `.t3d` 3D profile files used for boundary conditions (e.g., 3D salinity/temperature profiles).
  - `.cmp` composition files used for astronomic/harmonic boundary forcing compositions.
- Behavior: `clean()` prints a line for each removal (e.g., `Removing legacy file:<path>`) and deletes the file from disk.
- Safety: Only files explicitly collected by converters are deleted. If a converter did not mark a file as legacy, `clean()` will not remove it.

2) The legacy external forcings file (`.ext`)
- What: The original legacy external forcings file that you started from.
- Condition: Removed only when there are no remaining unsupported quantities.
  - If unsupported quantities exist (especially when running with `debug=True`), the legacy `.ext` is retained and contains only those unsupported entries after `update()`.
- Path: Resolved from `ExtOldModel.filepath`.

How are `legacy_files` populated?
- Boundary condition conversion scans for related time-series or composition files next to the location file (e.g., `.pli`) and records found `.tim`, `.t3d`, and `.cmp` files as legacy artifacts.
- Source/sink conversion records the corresponding `.tim` file for the polyline location.
- These paths are resolved relative to the converter `root_dir` (the MDU directory when using `from_mdu`, otherwise the legacy `.ext` directory).

How to trigger cleanup
- Programmatic:

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter

converter = ExternalForcingConverter("path/to/old-forcings.ext")
converter.update()
converter.save()
converter.clean()
```

- Batch conversion:

```python
from hydrolib.tools.extforce_convert.main_converter import recursive_converter
recursive_converter(root_dir="path/to/projects", remove_legacy=True)  # clean() is called per MDU
```

Recommendations and cautions
- Review `converter.legacy_files` and the console output to ensure none of the files are still needed by other workflows.
- Use version control or make backups of legacy artifacts if in doubt. Note that `save(backup=True)` creates backups for overwritten files, but deletions performed by `clean()` are permanent.



## Legacy formats and value mappings

This section explains how legacy files looked and how their values are mapped into the new files produced by `ExternalForcingConverter`.

Notes
- Examples are illustrative; exact keys depend on the quantity and converter.
- Field names use the new models’ casing (`quantity`, `forcingfile`, etc.).
- Some legacy options are no longer supported; see “Unsupported/changed fields”.

### 1) Legacy `.ext` blocks → new models

A single legacy block may be routed to different destination models depending on the quantity:
- Meteo quantities → `[meteo]` block in `new-external-forcing.ext`.
- Boundary quantities → `[boundary]` block in `new-external-forcing.ext` and a `.bc` file is generated/updated.
- Source/sink quantities → `[sourcesink]` block in `new-external-forcing.ext` and a `.bc` file is generated/updated.
- Initial/parameter quantities → `[initial]` / `[parameter]` block in `new-initial-conditions.ini`.
- Structures → `[structure]` in `new-structure.ini`.

#### 1.1) Meteo Block (new external forcing file)
```ini
QUANTITY=rainfall_rate
FILENAME=rainschematic.tim
FILETYPE=7
METHOD=1
OPERAND=O
```
Mapped to `[meteo]` (new external forcings):
- `QUANTITY` → `quantity`
- `FILENAME` → `forcingfile` (path preserved; path style may be normalized)
- `FILETYPE` → `forcingfiletype` via mapping (see table below)
- `METHOD` → `interpolationmethod` (and possibly `averaging*` fields; see below)
- `OPERAND` → `operand`
- Legacy `VARNAME` (if present) → `forcingVariableName`
- If `SOURCEMASK` is present → not supported (conversion raises error)
- Extrapolation options:
  - `EXTRAPOLATIONMETHOD`/`EXTRAPOLATION_METHOD` (int/flag) → `extrapolationAllowed` (boolean)
  - `MAXSEARCHRADIUS` → `extrapolationSearchRadius`

#### 1.2) Boundary block (new external forcing file)
```ini
QUANTITY=waterlevelbnd
FILENAME=OB_001_orgsize.pli
FILETYPE=4
METHOD=3
OPERAND=O
```
Mapped to `[boundary]` (new external forcings) plus a `.bc` file:
- `QUANTITY` → `quantity`
- `FILENAME` (polyline `.pli`) → `locationfile` (polyline is parsed to derive labels)
- Related time-series/profile/composition files are discovered next to the `.pli`:
  - `*.tim`, `*.t3d`, `*.cmp` with the same stem are located and merged/converted into a `ForcingModel`.
- `.bc` file path:
  - For boundary: same path as the `.pli` but with `.bc` extension (e.g., `OB_001_orgsize.bc`).
  - The new `[boundary]` block gets `forcingfile = <that bc file>`.
- Requires MDU `RefDate` (start time) for absolute-time conversion.
- Legacy files `*.tim`/`*.t3d`/`*.cmp` are recorded to `converter.legacy_files` (eligible for `clean()`).

#### 1.3) SourceSink block (new external forcing file) 
```ini
QUANTITY=discharge_salinity_temperature_sorsin
FILENAME=my_sourcesink.poly
FILETYPE=9
METHOD=1
```
Mapped to `[sourcesink]` (new external forcings) plus a `.bc` file:
- Polyline `FILENAME` → geometry (`numcoordinates`, `xcoordinates`, `ycoordinates`); optional `area` is preserved.
- A `*.tim` file is required next to the polyline (same stem). Columns in the TIM become separate time series in the generated `.bc` file.
- `.bc` file path: relative to MDU root, derived from the TIM path with `.bc` extension.
- MDU required: `RefDate`; temperature/salinity flags determine which quantities to include.
- If `zsource`/`zsink` elevations are present in the polyline, they are preserved.

#### 1.4) initial/parameter block (polygon)
```ini
QUANTITY=initialwaterlevel
FILENAME=start_area.pol
FILETYPE=10
METHOD=6
AVERAGINGTYPE=2
OPERAND=O
VALUE=0.15
```
Mapped to `new-initial-conditions.ini`:
- `QUANTITY` → `[initial].quantity` (with special-case rename for bedrock to `bedrockSurfaceElevation`)
- `FILENAME` → `datafile`
- `FILETYPE=10` → `datafiletype = polygon`
- `METHOD`/`AVERAGINGTYPE` → `interpolationmethod` and `averaging*` fields (see below)
- `OPERAND` → `operand`
- `VALUE` is preserved for polygon data
- Any `tracer*` keys present are copied as-is

##### FILETYPE mapping (legacy → new)
- 1 → `uniform`
- 2 → `unimagdir`
- 4 → `arcinfo`
- 5 → `spiderweb`
- 6 → `curvigrid`
- 7 → `sample`
- 10 → `polygon` (initial/parameter)
- 11 → `netcdf`
- 3 (spatially varying wind/pressure) → not supported (raises error)
- 8 (magnitude+direction timeseries on stations) → not supported (raises error)

##### METHOD and averaging mapping
- `METHOD` → `interpolationmethod`.
- When `METHOD = 6` (averaging), the following additional fields are set:
  - `averagingtype` from `AVERAGINGTYPE` using mapping:
    - 1 mean, 2 nearestnb, 3 max, 4 min, 5 invdist, 6 minabs, 7 median
  - `averagingrelsize` from `RELATIVESEARCHCELLSIZE`
  - `averagingnummin` from `NUMMIN`
  - `averagingpercentile` from `PERCENTILEMINMAX`

#### 2) Legacy `.tim` → new `.bc` (time series)

Minimal legacy TIM example
```
* time  value
0.0  10.0
3600  12.5
7200  15.0
```
How it’s used during conversion:
- Boundary conversion:
  - All `*.tim` files located for a boundary are merged into a single time series model.
  - Each TIM file contributes one column/series; its stem becomes the label in the `.bc` file.
  - The `.bc` filepath is `<polyline>.bc`.
- Source/sink conversion:
  - A single `*.tim` is parsed; its columns become separate series.
  - Labels are set to the polyline stem; the same `.bc` model is referenced for all series inside the `[sourcesink]` block.
- Time units:
  - Absolute time reference (e.g., `minutes since <RefDate>`) is derived from the MDU `RefDate`.


##### `.bc` (time series) file

```ini
[General]
fileVersion = 1.01
fileType    = boundConds

[Forcing]
name              = any-name-1
function          = timeseries
timeInterpolation = linear
offset            = 0.0
factor            = 1.0
quantity          = time
unit              = minutes since 2015-01-01 00:00:00
quantity          = waterlevelbnd
unit              = m
0.0    1.00
100.0  1.20
200.0  1.15
```

Notes
- Each `[Forcing]` block carries one series (or vector). The first `quantity`/`unit` pair describes time with an absolute reference derived from the MDU `RefDate`.
- Subsequent `quantity`/`unit` pairs describe the physical variable (e.g., `waterlevelbnd`, `dischargebnd`), followed by rows of `<time> <value>`.

#### 3) Legacy `.t3d` → new `.bc` (3D profiles)

- If `*.t3d` files are present next to the boundary polyline, they are parsed and converted to T3D forcing entries in the `.bc` file.
- Quantity names are repeated per vertical layer; user-defined labels are constructed from the polyline label and file stems.
- The same `.bc` file is used as for the time series.
- All `*.t3d` files that were used are added to `converter.legacy_files`.

At a glance: a `.t3d` file (input) and how it looks in `.bc`

##### Input `.t3d` (3D vertical profiles over time):
```text
LAYER_TYPE=SIGMA
LAYERS=0.0 0.2 0.6 0.8 1.0
TIME = 0 seconds since 2006-01-01 00:00:00 +00:00
1.0 1.0 1.0 1.0 1.0
TIME = 180 seconds since 2006-01-01 00:00:00 +00:00
2.0 2.0 2.0 2.0 2.0
```
Resulting `.bc` (function = `t3d`) snippet:
```ini
[Forcing]
name              = L1_0001
function          = t3d
vertPositions     = 0.0 0.2 0.6 0.8 1.0
vertInterpolation = linear
vertPositionType  = percBed
timeInterpolation = linear
quantity          = time
unit              = MINUTES SINCE 2006-01-01 00:00:00 +00:00
quantity          = salinitybnd
unit              = ppt
vertPositionIndex = 1
quantity          = salinitybnd
unit              = ppt
vertPositionIndex = 2
; ... one pair per vertical position
0.0   1.0  1.0  1.0  1.0  1.0
180.0 2.0  2.0  2.0  2.0  2.0
```

#### 4) Legacy `.cmp` → new `.bc` (harmonic/astronomic compositions)

- If `*.cmp` files are found next to the boundary polyline, their harmonic/astronomic records are converted to corresponding sections in the `.bc` file.
- Labels are derived from the polyline label and file stems.
- All `*.cmp` files that were used are added to `converter.legacy_files`.

At a glance: a `.cmp` file (input) and how it looks in `.bc`

##### Input `.cmp` (harmonic/astronomic components):
```text
* COLUMN1=Period (min) or Astronomical Component name
* COLUMN2=Amplitude
* COLUMN3=Phase (deg)
745.0000000     0.1053834     0.0000000
745.0000000     1.0000000     45.1200000
```
Resulting `.bc` harmonic snippet (period/amplitude/phase):
```ini
[Forcing]
name     = L1_0001
function = harmonic
quantity = harmonic component
unit     = minutes
quantity = waterlevelbnd amplitude
unit     = m
quantity = waterlevelbnd phase
unit     = deg
745.0  0.1053834  0.0
745.0  1.0000000  45.12
```
Resulting `.bc` astronomic snippet (named component):
```ini
[Forcing]
name     = L1_0002
function = astronomic
quantity = astronomic component
unit     = -
quantity = waterlevelbnd amplitude
unit     = m
quantity = waterlevelbnd phase
unit     = deg
M2  1.234  15.0
```

Tip
- The converter picks labels (`name = ...`) from the polyline label and file stems (e.g., `L1_0001`). Units for amplitude are taken from the CMP model when available; examples above are illustrative.

#### 5) Path handling rules (relative vs absolute)

- For boundary/sourcesink `.bc` paths:
  - Boundary: `<polyline>.bc` (same directory as the `.pli`).
  - Source/sink: relative to the MDU root based on the TIM file location, with `.bc` extension.
- For initial/parameter `datafile` paths:
  - If the MDU setting `PathsRelativeToParent = 1`, absolute or MDU-relative filenames inside the legacy `.ext` may be rewritten relative to the inifield file location to keep references consistent.
  - Otherwise, the original path is kept.

#### 6) Unsupported/changed fields

- `SOURCEMASK` is no longer supported for meteo/initial/parameter blocks; conversion raises an error when encountered.
- Some legacy `FILETYPE` values are no longer supported (see mapping table above).
- Boundary and source/sink conversions require MDU context:
  - `RefDate` must be present.
  - Temperature/salinity switches must be specified for source/sink to include corresponding series.

