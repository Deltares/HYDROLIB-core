# External Forcing Converter
### 2.1. High-Level Overview

`ExternalForcingConverter` converts legacy D-Flow FM external forcings files (old `.ext` format, represented by `ExtOldModel`) into the newer model structure consisting of:

- A new external forcings file (`ExtModel`) with `[Boundary]`, `[Lateral]`, `[SourceSink]` and `[Spatial]` blocks.
  Meteo, initial-condition and parameter quantities all become `[Spatial]` blocks; the converter no longer writes an
  initial field file. The `[Initial]` and `[Parameter]` blocks of the inifield file (`IniFieldFile`) are converted to
  `[Spatial]` blocks too, and the `IniFieldFile` entry is removed from the MDU file.
- A structures file (`StructureModel`) with `Structure` blocks.
- A mass balance area file (`MassBalanceAreaModel`) with `MassBalanceArea` blocks.

It orchestrates per-forcing conversion using a pluggable converter factory (`ConverterFactory`) that selects a concrete converter based on the forcing quantity. An MDU parser (`MDUParser`) is required: it supplies the model metadata the converters need, and the MDU file is updated to point to the newly generated files. The class can also back up/clean legacy artifacts.

Typical place in a larger system: infrastructure/tooling layer. It acts as a migration utility or pipeline step used to modernize project inputs.

### 2.2. Key Responsibilities and Collaborations

Primary responsibilities:

- Load a legacy external forcings file into `ExtOldModel` (or accept a provided instance).
- For each forcing block:
  - Detect and skip unsupported quantities (optionally strict or permissive via `debug`).
  - Choose and invoke the appropriate converter via `ConverterFactory`.
  - Append the converted block(s) to the correct target model (`ExtModel`, `StructureModel`, or `MassBalanceAreaModel`).
    A converter may return several blocks for one legacy quantity (e.g. a combined quantity split into one
    `[Spatial]` block per component); all of them are appended.
  - Make blocks that write the same `.bc` file share one `ForcingModel` (`ForcingFileRegistry`), so the file is
    written once instead of being overwritten.
- Update the MDU file to reference new outputs and remove the old external forcing file reference if fully converted.
- Persist new models to disk with optional backups; optionally remove legacy files produced during conversion.

Key collaborators and how they’re used:

- `hydrolib.core.dflowfm.extold.models.ExtOldModel` (input): Parsed representation of old `.ext`; the source of forcings.
- `hydrolib.core.dflowfm.ext.models.ExtModel` (output): Destination model for boundary, lateral, source/sink and spatial blocks.
- `hydrolib.core.dflowfm.structure.models.StructureModel` (output): Destination model for structures.
- `hydrolib.core.dflowfm.mba.models.MassBalanceAreaModel` (output): Destination model for mass balance areas.
- `hydrolib.tools.extforce_convert.converters.ConverterFactory` (strategy selection): Creates the correct converter class for a given quantity.
  - `BoundaryConditionConverter`, `LateralConverter`, `SourceSinkConverter`, `SpatialConverter` and `MassBalanceAreaConverter` are the concrete converters used depending on the quantity. Meteo, initial-condition and parameter quantities are routed to `SpatialConverter` (producing `[Spatial]` blocks); combined quantities (e.g. a wind vector) go to `CombinedQuantityConverter`, a `SpatialConverter` subclass that splits them into one block per component.
- `hydrolib.tools.extforce_convert.forcing_registry.ForcingFileRegistry`: Lets blocks that resolve to the same `.bc` path share one `ForcingModel`.
- `hydrolib.tools.extforce_convert.mdu_parser.MDUParser` (required): Reads MDU metadata (e.g., `refdate`, temperature/salinity flags, the inifield, structure and mass balance area files) and updates references to new files.
- `hydrolib.tools.extforce_convert.utils.CONVERTER_DATA` (capabilities): Reports unsupported quantities.
- `hydrolib.tools.extforce_convert.utils.construct_filemodel_new_or_existing` (model builder): Ensures destination models exist (new or from existing files) with minimal recursion.
- `hydrolib.tools.extforce_convert.utils.backup_file` (safety): Creates backups before overwriting.
- `tqdm` (UX): Progress bar during conversion.
- File system (I/O): Reading old file, writing new files, backups, optional deletions.

### 2.3. Public API Documentation

Class: `ExternalForcingConverter`

- Purpose: Convert legacy external forcing data to the new model structure and optionally update the MDU file.

Constructor

- `__init__(
    *,
    extold_model: PathOrStr | ExtOldModel | None,
    ext_file: PathOrStr | None = None,
    structure_file: PathOrStr | None = None,
    mdu_parser: MDUParser,
    verbose: bool = False,
    path_style: PathStyle | None = None,
    debug: bool | None = False,
    mba_file: PathOrStr | None = None,
  )`
  - All arguments are keyword-only.
  - Parameters:
    - `extold_model`: Path to legacy `.ext` or an `ExtOldModel` instance. If a path or str, the file is loaded via `_read_old_file()`. `None` for an MDU that has no legacy `.ext` file, only an inifield file to convert.
    - `ext_file`: Destination path for new external forcings (`ExtModel`). Defaults to `new-external-forcing.ext` in the directory of the MDU file. If the file exists, the converted quantities are appended to it.
    - `structure_file`: Destination path for `StructureModel`. Defaults to `new-structure.ini` in the MDU directory.
    - `mdu_parser`: **Required** `MDUParser`. Provides FM metadata (e.g., `refdate`, temperature/salinity), the root directory (the MDU's parent), and is used to update the MDU file.
    - `verbose`: If `True`, prints conversion details to stdout.
    - `path_style`: Controls conversion/interpretation of absolute paths (Windows/Unix style) when reading/writing models.
    - `debug`: If `True`, unsupported quantities are skipped (not converted) without raising; otherwise an error is raised.
    - `mba_file`: Destination path for `MassBalanceAreaModel`. Defaults to `new_mba.ini` in the MDU directory.
  - Side effects:
    - May read the legacy `.ext` file.
    - Creates model objects for new outputs (not yet written).
    - Snapshots the quantities already present in the new ext file, so the source/sink converter can order tracer columns by the kernel's precedence.
    - Computes `un_supported_quantities` early via `check_unsupported_quantities()`.
  - Exceptions:
    - `FileNotFoundError` if the path to the legacy file doesn’t exist.
    - `TypeError` if `extold_model` is neither a path nor an `ExtOldModel`.

Classmethod

- `from_mdu(
    mdu_file: PathOrStr,
    path_style: PathStyle | None = None,
    debug: bool = False,
  ) -> ExternalForcingConverter`
  - Purpose: Create a converter using paths resolved from an MDU file.
  - Parameters: `mdu_file`, `path_style` and `debug` as above. The output file paths cannot be overridden: the new
    external forcings, structure and mass balance area files are always read from the MDU. When the MDU references an
    existing file, the converted quantities are appended to it; otherwise a default file is created next to the MDU.
  - Returns: A fully initialized `ExternalForcingConverter`.
  - Side effects: Parses the MDU file; determines legacy `.ext` path and output file paths.
  - Exceptions (per docstring and expected behavior):
    - `FileNotFoundError` if MDU is missing.
    - `ValueError` if the MDU has neither a legacy ext file nor an existing inifield file (an empty `IniFieldFile =` entry, or one pointing to a missing file, does not count).
    - `DeprecationWarning` if unknown keywords in the MDU (raised by `MDUParser`).

Properties

- `legacy_files: list[Path]`
  - Get: Returns a list of legacy files produced during conversion (e.g., old `.tim` files) to potentially delete later.
  - Set: Appends given list of Paths to the internal list. Type-checked; raises `TypeError` if not a list.

- `verbose: bool`
  - Get/Set: Controls additional logging to stdout.

- `mdu_parser: MDUParser`
  - Get: Returns the `MDUParser` the converter was created with.

- `root_dir: Path`
  - Get: The directory of the MDU file (`mdu_parser.mdu_path.parent`).

- `path_style: Optional[PathStyle]`
  - Get: Path style used when saving models (absolute path handling).

- `extold_model: ExtOldModel`
  - Get: The loaded legacy model.

- `ext_model: ExtModel`
  - Get: Destination external forcings model. Raises `ValueError` if unexpectedly unset.
  - Set: `ext_model(path: PathOrStr)`: Replaces the destination model using `construct_filemodel_new_or_existing`.

- `structure_model: StructureModel`
  - Get/Set analogous to `ext_model`.

- `mba_model: MassBalanceAreaModel`
  - Get/Set analogous to `ext_model`.

- `un_supported_quantities: list[str]`
  - Set during initialization by `check_unsupported_quantities()`. Lowercased quantity names that are unsupported according to `CONVERTER_DATA`.

- Attribute: `temperature_salinity_data: Dict[str, int]`
  - Taken from `mdu_parser.temperature_salinity_data`; used for `SourceSink` conversions.

Public methods

- `check_unsupported_quantities(self) -> list[str]`
  - Returns: List of unsupported quantities found in `extold_model` (lowercased).
  - Side effects: None.
  - Exceptions: If `debug` is `False`, errors on unsupported quantities (raised by `CONVERTER_DATA.check_unsupported_quantities`).

- `update(self) -> tuple[ExtModel, StructureModel] | None`
  - Purpose: Convert all eligible forcings from the legacy model and append them to the correct destination models.
  - Behavior:
    - Logs details if `verbose`.
    - Converts the `[Initial]` and `[Parameter]` blocks of the inifield file first (see [Converted files](converted_files.md)).
    - Iterates forcings, shows a progress bar (`tqdm`).
    - For unsupported quantities: prints a message (with `debug` state) and skips.
    - For supported quantities: calls `_convert_forcing`, which returns one block or a list of blocks. Each block is registered with the `ForcingFileRegistry` (shared `.bc` files), mapped to the destination model by type (`_type_field_map`: `Boundary`, `Lateral`, `SourceSink`, `Spatial` -> `ExtModel`; `Structure` -> `StructureModel`; `MassBalanceArea` -> `MassBalanceAreaModel`) and appended.
    - Updates the MDU file (`_update_mdu_file`).
    - If any unsupported quantities exist, prunes `extold_model.forcing` to contain only those remaining unsupported forcings.
  - Returns: `(ext_model, structure_model)` for inspection by callers. Nothing is written to disk until `save()`; inspect `mba_model` through its property.
  - Side effects: Updates in-memory models and the MDU parser; prints progress/logs; modifies `extold_model.forcing` contents if unsupported quantities exist.
  - Exceptions:
    - `NotImplementedError` if a converted block’s type is unknown to `_type_field_map`.
    - `ValueError` from `_convert_forcing` if required MDU data is missing for certain converters.
    - `InifieldError` if the inifield file exists but cannot be parsed; the message names the file.

- `save(self, backup: bool = True, recursive: bool = True) -> None`
  - Purpose: Persist the new/updated models to disk and the updated MDU file.
  - Behavior:
    - Saves `StructureModel` if it has any `structure` entries (the `[General]` block is always written).
    - Saves `MassBalanceAreaModel` if it has any `massbalancearea` entries (the `[General]` block is always written).
    - If unsupported quantities exist, backs up and saves the old `ExtOldModel` (containing only unsupported entries after `update`).
    - Saves `ExtModel` if it has any forcing blocks (`n_forcing_blocks`), with a backup first if overwriting and `backup=True`; the `[General]` block is always written.
    - Calls `mdu_parser.clean()` and `mdu_parser.save(backup=backup)`.
  - Side effects: File I/O, backups, writes MDU.

- `clean(self) -> None`
  - Purpose: Remove legacy artifacts (e.g., time files) and delete the old `.ext` file if fully converted.
  - Behavior:
    - Deletes any files listed in `legacy_files` and prints their paths.
    - If there are no remaining unsupported quantities, deletes the legacy `.ext` file itself.
  - Side effects: File deletions.

Static/Protected helpers (summarized for completeness; not typically called by clients)

- `_read_old_file(ext_old_file: PathOrStr, path_style: Optional[PathStyle]) -> ExtOldModel`
- `_type_field_map(self) -> dict[type, tuple[Any, str]]` (maps block types to destination models/attributes).
- `_convert_forcing(self, forcing) -> Boundary | Lateral | Spatial | SourceSink | MassBalanceArea | list[...]`
  - Note: The annotation in code is narrower (`Boundary | Lateral | Meteo | SourceSink | MassBalanceArea`). Actual behavior also includes `Spatial` (for meteo, initial-condition and parameter quantities) and a list of blocks for combined quantities.
  - Exceptions: `ValueError` if MDU info missing for `SourceSink` or boundary conversions.
- `_resolve_forcing_path(self, forcing, ref_path) -> Path` (resolves the data file of a `[Spatial]` block relative to the new ext file, honouring `pathsRelativeToParent`).
- `_update_mdu_file(self) -> None` (also sets `mbaFile` and `mbaInterval` when mass balance areas were converted; `mbaInterval` is taken from `DtMassBalance`, falling back to `DtProcesses`, with a `UserWarning` if neither exists).
- `_save_structure_model(self, backup: bool, recursive: bool) -> None`
- `_save_mba_model(self, backup: bool, recursive: bool) -> None`
- `_log_conversion_details(self) -> None`

Example usage

- From legacy model object

```python
from pathlib import Path
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

# Prepare a minimal ExtOldModel in memory
root_dir = Path("path/to/your/root/dir")
forcing_data = {
    'QUANTITY': 'windspeedfactor',
    'FILENAME': rf'{root_dir}/my-poly-file.pol',
    'FILETYPE': '11',
    'METHOD': '4',
    'OPERAND': 'O',
}
forcing_model_data = {
    'comment': [' Example (old-style) external forcings file'],
    'forcing': [forcing_data]
}
old_model = ExtOldModel(**forcing_model_data)  
mdu_parser = MDUParser("path/to/your/model.mdu")  
converter = ExternalForcingConverter(  
    extold_model=old_model,  
    mdu_parser=mdu_parser,  
    verbose=True,  
)  
ext_model, struct_model = converter.update()
converter.save(backup=True)
```

- From legacy file path (requires an explicit `MDUParser`)

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

mdu_parser = MDUParser("model.mdu")  
converter = ExternalForcingConverter(  
    extold_model="old-external-forcing.ext",  
    mdu_parser=mdu_parser,  
    verbose=True,  
)  
converter.update()  
converter.save()  
```

- From MDU file (recommended for quantities needing FM metadata)

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter

converter = ExternalForcingConverter.from_mdu("model.mdu", debug=False)  
converter.update()  
converter.save(backup=True)  
# Optional: remove legacy artifacts if nothing left unsupported
converter.clean()  
```

### 2.4. Lifecycle & Control Flow Explanation

Typical creation and use:

1. Instantiate the converter:
   - Provide either a path to the legacy `.ext` or an `ExtOldModel` instance, together with an `MDUParser` (or use `from_mdu`, which builds both). The MDU supplies metadata for certain conversions:
     - `SourceSink` needs temperature/salinity flags and `refdate`.
     - Boundary condition conversion needs `refdate` (start time).
2. Call `update()`:
   - For each forcing block in `extold_model.forcing`:
     - If the quantity is unsupported, it is skipped and remains in `extold_model` (post-update the legacy model contains only these unsupported entries).
     - Otherwise, a concrete converter is created (`ConverterFactory.create_converter`) and `convert()` is invoked with the required context.
     - The converted block(s) are appended to the appropriate destination model, chosen by type.
   - `_update_mdu_file()` modifies MDU references to point to the new files and removes the old ext file reference if everything was converted.
3. Call `save()` to write outputs to disk, with backups as needed.
4. Optionally call `clean()` to delete any temporary legacy files and, when fully converted, remove the old `.ext` file.

Important invariants/constraints:

- `mdu_parser` is mandatory; `SourceSink` and boundary conversions raise a `ValueError` if the MDU lacks the needed `refdate` or temperature/salinity data.
- `un_supported_quantities` are determined at initialization:
  - `debug=False` (strict): raises on unsupported quantities during detection.
  - `debug=True` (permissive): allows conversion to proceed, skipping unsupported ones.
- Destination models are created (or opened if existing) in the MDU file’s directory unless the MDU references other paths (`from_mdu`) or explicit paths are passed to the constructor.
- Saved models use `exclude_unset=True`, and the `[General]` block of the ext, structure and mass balance area files is set explicitly so that it is always written.
- Same-quantity block order is preserved: blocks are appended in legacy file order, because the kernel applies them top to bottom.

---

### 3. Diagrams

#### 3.1. Component / Integration Diagram

```mermaid
graph LR
    subgraph Filesystem
      OldExt[(old.ext file)]
      NewExt[(new external forcings .ext)]
      NewStr[(structures.ini)]
      NewMba[(new_mba.ini)]
      Backups[(.bak backups)]
    end

    Client[[Caller]] --> Conv[ExternalForcingConverter]
    Conv --> OldExt
    Conv --> NewExt
    Conv --> NewStr
    Conv --> NewMba
    Conv -. optional .-> Backups

    subgraph FM
      MDU[MDUParser]
      MDUFile[(model.mdu)]
    end

    Conv <--> MDU
    MDU <--> MDUFile
```

#### 3.2. Class Structure Diagram

```mermaid
classDiagram
    class ExternalForcingConverter {
        + __init__(extold_model, ext_file, structure_file, mdu_parser, verbose, path_style, debug, mba_file)
        + from_mdu(mdu_file, path_style, debug) ExternalForcingConverter
        + update() tuple~ExtModel, StructureModel~
        + save(backup, recursive) void
        + clean() void
        + check_unsupported_quantities() list~str~
        + ext_model: ExtModel
        + structure_model: StructureModel
        + mba_model: MassBalanceAreaModel
        + extold_model: ExtOldModel
        + root_dir: Path
        + path_style: PathStyle
        + mdu_parser: MDUParser
        + legacy_files: list~Path~
        - debug: bool
        - un_supported_quantities: list~str~
        + temperature_salinity_data: Dict~str, int~
    }

    ExternalForcingConverter --> ExtOldModel : reads
    ExternalForcingConverter --> ExtModel : writes
    ExternalForcingConverter --> StructureModel : writes
    ExternalForcingConverter --> MassBalanceAreaModel : writes
    ExternalForcingConverter --> MDUParser : requires
    ExternalForcingConverter ..> ConverterFactory : uses
    ConverterFactory <.. ExternalForcingConverter : create_converter()
```

#### 3.3. Main Usage / Sequence Diagram

```mermaid
sequenceDiagram
    actor Client
    participant MDU as MDUParser
    participant Conv as ExternalForcingConverter
    participant Old as ExtOldModel
    participant NewExt as ExtModel
    participant NewStr as StructureModel
    participant NewMba as MassBalanceAreaModel
    participant CF as ConverterFactory
    participant FS as FileSystem

    Client->>Conv: from_mdu(model.mdu)
    Conv->>MDU: parse mdu file
    MDU-->>Conv: extforce file, refdate, temp/salinity flags
    Conv->>Old: load legacy ext (if given as path)
    Conv->>NewExt: load new ext (if given as path)
    Conv->>NewStr: load new structure file (if it exists)
    Conv->>NewMba: load new mass balance area file (if it exists)

    Client->>Conv: update
    loop each forcing in Old.forcing
        Conv->>Conv: check unsupported quantity
        alt unsupported
            Conv-->>Client: skip and log
        else supported
            Conv->>CF: create converter for quantity
            CF-->>Conv: converter instance
            alt needs MDU context
                Conv->>MDU: get refdate and temp/salinity
            end
            Conv->>Conv: convert forcing
            Conv->>NewExt: append if Boundary/Lateral/SourceSink/Spatial
            Conv->>NewStr: append if Structure
            Conv->>NewMba: append if MassBalanceArea
        end
    end
    Conv->>MDU: update file references

    Client->>Conv: save (backup=true)
    Conv->>NewStr: save (if any structures)
    Conv->>NewMba: save (if any mass balance areas)
    Conv->>Old: save unsupported-only (if any)
    Conv->>NewExt: save (if any forcing blocks)
    Conv->>MDU: clean
    Conv->>MDU: save

    opt cleanup
        Client->>Conv: clean
        Conv->>FS: delete legacy files
        Conv->>FS: delete old ext (if fully converted)
    end
```

#### 3.4. Control Flow / Logic Diagram

```mermaid
flowchart TD
    A[update] --> B[Log details if verbose]
    B --> C[Get number of forcings]
    C --> D{Loop forcings}
    D -->|each forcing| E{Quantity unsupported?}
    E -->|Yes| F[Leave the quantity in the \n old external forcing file]
    E -->|No| G[Convert forcing]
    G --> H{Map type to target model}
    H -->|Found| I[Append to target model]
    H -->|Not found| J[Raise error]
    I --> K[Increment progress]
    F --> L{More forcings?}
    K --> L
    L -->|Yes| D
    L -->|No| N[Update MDU file]
    N --> P{Unsupported quantities exist?}
    P -->|Yes| Q[Keep legacy model with unsupported only]
    P -->|No| R[The Legacy model is fully converted, \n clean deletes it]
    Q --> S[Return models]
    R --> S[Return models]

    subgraph convert
        G1[Convert forcing]
        G1 --> C1[Create converter for quantity]
        C1 --> D1{Converter type}
        D1 -->|SourceSink| E1[Needs temp salinity and refdate]
        D1 -->|Boundary| E2[Needs refdate]
        D1 -->|Spatial: meteo, initial or parameters| E3[Resolve relative path]
        D1 -->|Lateral or mass balance area| E4[Simple convert]
        E1 --> F1[Convert with quantities and start time]
        E2 --> F2[Convert with start time]
        E3 --> F3[Convert with forcing path]
        E4 --> F4[Convert]
    end
```


---

### 4. Design & Architecture Notes

- Patterns:
  - Factory/Strategy: `ConverterFactory` selects a specialized converter per quantity; each converter encapsulates conversion logic.
  - Facade/Coordinator: `ExternalForcingConverter` orchestrates multiple subsystems (models, MDU, converters, filesystem) to provide a simple `update/save/clean` workflow.
  - Factory Method: `from_mdu` is a named constructor that assembles a properly configured instance from an MDU file.
- Cohesion & scope: High cohesion around conversion concerns; the class mediates between input model, conversion strategies, and output models.
- Extension points:
  - Add new quantity support by adding a converter and registering it in `ConverterFactory` and `CONVERTER_DATA`.
  - Converters may return a list of blocks for one legacy quantity; `update()` appends each block separately.
  - `_type_field_map` defines how converted block types are routed; extending with new block types would require updating this mapping.
- Contracts/assumptions:
  - Some conversions require FM metadata (e.g., `refdate`, temperature/salinity flags) from `MDUParser`.
  - `path_style` must align with the environment if absolute paths appear in models.
  - When `debug=False`, unsupported quantities should be resolved before proceeding; otherwise initialization will error.
  - The annotation on `_convert_forcing` under-represents its actual return possibilities; callers should rely on `_type_field_map` (or concrete converter contracts) rather than the annotation.

---

### 5. Usage Examples

1) Convert using `from_mdu` (recommended)

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter

converter = ExternalForcingConverter.from_mdu("path/to/model.mdu", debug=True)  # debug: skip unsupported quantities
converter.update()     # performs conversion and updates MDU references
converter.save()       # writes new models and MDU; may back up existing files
# If everything converted and you want to remove legacy artifacts
converter.clean()
```

2) Convert using a legacy `.ext` path (an `MDUParser` is required)

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

converter = ExternalForcingConverter(
    extold_model="path/to/old-forcings.ext",
    mdu_parser=MDUParser("path/to/model.mdu"),
    verbose=True,
)
converter.update()
converter.save(backup=True)
```

3) Provide custom output file locations

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser

converter = ExternalForcingConverter(
    extold_model=".../old.ext",
    mdu_parser=MDUParser(".../model.mdu"),
    ext_file=".../new/forcings.ext",
    structure_file=".../new/structures.ini",
    mba_file=".../new/mba.ini",
)
converter.update()
converter.save()
```

4) Programmatic inspection after update

```python
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter

# Create a converter from the FM model so the required MDU metadata is available.
converter = ExternalForcingConverter.from_mdu("path/to/model.mdu")

ext_model, struct_model = converter.update()
print(len(ext_model.spatial), len(ext_model.boundary))
print(len(struct_model.structure))
print(len(converter.mba_model.massbalancearea))
```

---

### 6. Quality & Safety Requirements

- No undocumented behavior is assumed. Where converter internals are not shown, the documentation limits itself to what the class contracts expose.
- Assumption: Specifics of `MDUParser` exceptions and converter outputs align with their documented/typical behavior.
- Mermaid snippets above are valid and derived from the visible control flow in this module.
- This document is self-contained and suitable for inclusion in a docs site or repository README.
