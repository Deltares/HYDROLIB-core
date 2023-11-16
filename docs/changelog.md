## 0.6.0 (2023-11-16)

### Feat

- Add filetype 10 (polyfile) to class ExtOldFileType (#565)
- Add missing oldext quantities (#557)

### Fix

- Rainfall Runoff .bui file with multiple stations gives parse error

## 0.5.2 (2023-04-19)

### Fix

- failing unittest + SonarCloud security issue (#541)

## 0.5.1 (2023-04-17)

### Feat

- Add the quantity `nudge_salinity_temperature` to ext old file header.
- Support the old style external forcings file
- Add support for several coastal MDU keywords
- Add support for *.tim files and *.bc files in the structure file
- Support meteo blocks in external forcings file (#477)
- Remove indentation from MDU file
- Add 4 missing 1D2D settings to FMModel
- Support *.tim files
- Add XYN classes to public API (#492)
- Include old and new observation crossections into MDU FMModel.output class (#470)
- Support observation crosssection .pli via existing PolyFile class (#464)
- Add support for 3D Z-sigma settings in MDU
- Support loading+saving models with configurable OS path style formats (#361)
- Add support for observation point xyn files (#472)
- Support filepath as str besides Path for all model classes under FileBasedModel (#469)
- Add validation for NaN values in datablocks

### Fix

- Fixed issues with the new release script
- Special characters should be parsed correctly from file
- MDU keywords such as 1d2dLinkFile are written to file without comments (#528)
- UGRID network files without faces should be accepted
- correct handling of whitespace and comments in observation point .xyn files (#508)
- Fix resolving of relative paths containing `..` when not using the `resolve_casing` option.
- ignore trailing values or text on polyline data lines to better support boundary polyfiles (#482)
- Reading invalid formatted plifile should raise error instead of warning
- polyline serializer should print empty trailing comment lines

### Refactor

- Make sure of the new Pydantic 1.10 functionality

## 0.4.1 (2023-01-26)

### Fix
- `_add_nodes_to_segments` fixed ({{gh_pr(440)}})

## 0.4.0 (2023-01-23)

### Feat

- Remove io namespace and add convenient imports/API at several directory levels ({{gh_pr(438)}})
- Added the option for all supported files to customize the float formatting when saving ({{gh_pr(406)}})
- Suppress warning in polyfile parser that the white space at the start of the line is ignored ({{gh_pr(409)}})
- Change data block default spacing from 4 to 2 ({{gh_pr(407)}})
- Add support for non-recursively loading models ({{gh_pr(401)}})

### Fix

- Fixed polylinefile validation for Structure and its subclasses ({{gh_pr(416)}})
- Rename variable in generate_nodes function ({{gh_pr(437)}})
- Ensure that QuantityUnitPairs that are not part of a vector are correctly parsed ({{gh_pr(420)}})
- Enum values are incorrectly written to files ({{gh_pr(403)}})

### Refactor

- Small refactoring of the VectorQuantityUnitPairs and VectorForcingBase ({{gh_pr(422)}})
- Move the base module in XYZ back to IO ({{gh_pr(418)}})
- Refactored support for vectors in .bc files ({{gh_pr(394)}})

## 0.3.1 (2022-10-25)

### Feat

- option `resolve_casing` to fix filepath casing between different OS's.
- Added support for the use of vectors within forcing models with a t3d or timeseries function type.
- Added possibility to take structure positions into account when discretizing 1d mesh
- Add support for branches.gui file ({{gh_pr(333)}})
- Drop extra fields for INIBasedModels if they are not in file format definition
- Support crs file for observation cross sections ({{gh_pr(289)}})
- implement mesh generation for pipes ({{gh_pr(294)}}) and fix support different reference system ({{gh_pr(298)}}) ({{gh_pr(299)}})
- removed the writeBalanceFile keyword from the mdu
- support copying generic files/models ({{gh_pr(281)}})
- Support extra MDU sections ({{gh_pr(284)}})
- add binder support with a dockerfile ({{gh_pr(264)}})

### Fix

- Add backwards compatibility for the old "percentage from bed" vertical position type.
- Fix freeze when printing a ForcingModel with multiple [forcing] blocks by omitting the datablocks.
- T3D header is not correct ({{gh_pr(356)}})
- Change AutoStart type from bool to int ({{gh_pr(349)}})
- Skip serialization of empty INI properties when configured ({{gh_pr(336)}})
- Net writer should not produce NaN as fill values ({{gh_pr(363)}})
- Change type of xcoordinates and ycoordinates in Lateral class from int to float ({{gh_pr(351)}})
- Fix that single structure in StructureModel class is correctly converted to a list ({{gh_pr(352)}})
- Ensure poly files can be saved ({{gh_pr(344)}})
- write correct branchorder to net file ({{gh_pr(335)}})
- add zdatum vertical position type ({{gh_pr(324)}})
- parse vertical positions to list ({{gh_pr(325)}})
- make `has_z_values` parameter optional in `polyfile.parser.read_polyfile` ({{gh_pr(312)}})
- Remove unnessary indent in .bc datablocks ({{gh_pr(304)}})
- Fix the types of 4 fields in the MDU file ({{gh_pr(283)}})

### Refactor
- Location specification root validator ({{gh_pr(347)}})

## 0.3.0 (2022-07-11)

### Fix

- Add water level location validation DamBreaks
- allow empty file paths in the .fnm file
- Add modeltype 21 to RR node for open water precipitation/evaporation ({{gh_pr(261)}})
- **filemodel**: ResolveRelativeMode is incorrectly set when reading a model with 'pathsRelativeToParent' set to false ({{gh_pr(259)}})

### Feat

- **network**: additional mesh funcs dhydamo
- support .bc files and more in lateral discharge ({{gh_pr(244)}})
- add support for observation point ini file ({{gh_pr(236)}})
- support .bc files and more in lateral discharge

### Refactor

- **rr**: place all RR-related code+tests in own rr subpackage ({{gh_pr(235)}})
- remove dead code of _process_edges_for_branch

## 0.2.1 (2022-03-15)

### Fix

- **parser**: correctly parse model input fields with leading digits, such as 1D2DLinkFile.
- **parser**: allow empty friction specification in all crossdef types. ({{gh_pr(206)}}).

## 0.2.0 (2021-12-17)
### Added
* RainfallRunoff files: [NodeFile][hydrolib.core.io.rr.topology.models.NodeFile] ({{gh_issue(138)}})
  and [LinkFile][hydrolib.core.io.rr.topology.models.LinkFile] ({{gh_issue(140)}})
* D-Flow FM files:
    * Initial field files: [IniFieldModel][hydrolib.core.io.inifield.models.IniFieldModel],
      also added 1D Field INI format: [OneDFieldModel][hydrolib.core.io.onedfield.models.OneDFieldModel] ({{gh_issue(119)}}).
    * 1D Roughness INI files: [FrictionModel][hydrolib.core.io.friction.models.FrictionModel] ({{gh_issue(118)}}).
    * Storage node files: [StorageNodeModel][hydrolib.core.io.storagenode.models.StorageNodeModel] ({{gh_issue(131)}}).
    * General structure:  [GeneralStructure][hydrolib.core.io.structure.models.GeneralStructure] ({{gh_issue(79)}}).
* Many additions to the [API documentation](reference/api.md).
    

### Changed
* All classes that have fields with "keyword values" (such as `frictionType = WhiteColebrook`) now use Enum classes for those values.
  See for example [FrictionType][hydrolib.core.io.friction.models.FrictionType] and [FlowDirection][hydrolib.core.io.structure.models.FlowDirection]
  ({{gh_issue(98)}})
* All crosssection definition type now supported as subclasses of
  [CrossSection][hydrolib.core.io.crosssection.models.CrossSectionDefinition] ({{gh_issue(117)}})
* Cross section definition and location classes have been moved from `hydrolib.core.io.ini.models`
  to `hydrolib.core.io.crosssection.models`. ({{gh_issue(149)}})
* Changed behavior for file paths in saved files ({{gh_issue(96)}}).
  More information about: [technical background](topics/loadsave.md) and a [tutorial](tutorials/loading_and_saving_a_model.md).
  

### Fixed
* Too strict validation of optional fields in culvert ({{gh_issue(75)}}), pump ({{gh_issue(76)}}),
  weir ({{gh_issue(77)}}), orifice ({{gh_issue(78)}}).
* Floating point parser breaks reading/writing of keyword UnifFrictCoef1D2D ({{gh_issue(103)}})
* DIMR config has invalid control element for a single component model ({{gh_issue(127)}})
* DataBlockINIBasedModel.datablock should also support strings (astronomic in .bc files) ({{gh_issue(137)}})
* Saving .bc files incorrectly writes repeated key names as a semicolon-separated list ({{gh_issue(101)}})
* Do not write absolute file paths to file ({{gh_issue(96)}})

## 0.1.5 (2021-11-02)

## 0.1.4 (2021-11-02)

## 0.1.3 (2021-08-05)

### Fix

- netcdf serialization path.

## 0.1.2 (2021-08-05)

### Fix

- **test_version**: Fix updated version

## 0.1.1 (2021-08-05)

### Fix

- **NetworkModel**: Fix default init of Network within NetworkModel
