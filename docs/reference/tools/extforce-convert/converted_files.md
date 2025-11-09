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
