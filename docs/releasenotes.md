## HYDROLIB-core 0.5.0 Release Notes
HYDROLIB-core 0.5.0 mainly adds more support for D-Flow FM 2D3D models in coastal applications.

### Compatibility Notes
Support for MacOS is temporarily dropped, due to an upgrade to MeshKernel 2.0.2, which has no MacOS version at the moment.
We aim to re-enable this support in future releases.

### New Features
* Support for cross-platform path style ({{gh_pr(361)}}), more info in the [loading and saving tutorial](tutorials/loading_and_saving_a_model/#saving-and-loading-models-between-different-operating-systems).
* Support for more MDU keywords (1D2D: see {{gh_issue(489)}}, 2D/3D: see {{gh_issue(474)}}, {{gh_issue(486)}}).
* Support for `[Meteo]` blocks in external forcings files ({{gh_issue(446)}})
* Support for various legacy file formats, to facilitate future model conversions:
    * Observation point `*.xyn` files ({{gh_issue(459)}}).
    * Observation crosssection `*.pli` files ({{gh_issue(364)}},{{gh_issue(461)}}).
    * Old external forcings file `*.ext`  ({{gh_issue(369)}}).
    * Support for timeseries in `*.tim` files ({{gh_issue(348)}}), also included in structure files ({{gh_issue(497)}}) and external meteo forcings ({{gh_issue(446)}}).

### Improvements
* All file-based model class constructors now accept file path as a `str`, in addition to the already existing `pathlib.Path` ({{gh_issue(365)}}).
* MeshKernel dependency was updated to version 2.0.2, which has more functionality in its API ({{gh_issue(450)}}).

### Bugfixes
See the detailed {{gh_repo("docs/changelog.md", "ChangeLog on GitHub")}}.

## Archive
Pre-0.5.0 release notes are available via the {{gh_repo("docs/changelog.md", "ChangeLog on GitHub")}}.
