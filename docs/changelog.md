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
