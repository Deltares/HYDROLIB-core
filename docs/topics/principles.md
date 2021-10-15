# First principles
hydrolib-core is structured around the input and output files (I/O) of the DHYDRO suite.

# Inheritance/file handling
Model setups often consist of different files, many implicitly linked to each other.
HYDROLIB makes these links explicit, by recursively loading all child configuration files.

For example, when parsing a DIMR file, one could happen upon a reference to an MDU file, which
contain references to other files, such as cross sections, etc.

```python
>>> dimr = DIMR(filepath=Path(test_data_dir / "dimr_config.xml"))
```

You can see this tree structure if you call `show_tree`.

```python
>>> dimr.show_tree()
  DIMR represented by dimr_config.xml.
    RRComponent
    FMComponent
     ∟ FMModel represented by FlowFM.mdu.
       ∟ Geometry
         ∟ StructureModel represented by structures.ini.
         ∟ CrossDefModel represented by crsdef.ini.
         ∟ CrossLocModel represented by crsloc.ini.
         ∟ FrictionModel represented by roughness-Main.ini.
         ∟ FrictionModel represented by roughness-Sewer1.ini.
         ∟ FrictionModel represented by roughness-Sewer2.ini.
       ∟ ExternalForcing
         ∟ ExtModel represented by FlowFM_bnd.ext.
           ∟ Boundary
             ∟ ForcingModel represented by FlowFM_boundaryconditions1d.bc.
           ∟ Boundary
             ∟ ForcingModel represented by FlowFM_boundaryconditions1d.bc.
           ∟ Boundary
             ∟ ForcingModel represented by FlowFM_boundaryconditions1d.bc.
```

# Program flow while recursively creating FileModels
## In short:
- The root folder is stored in the global variable `context_dir`, so that referenced files can be found.
- Parsed data from files will be cached in the class variable `FileModel._file_models_cache`, so that duplicate references do not lead to duplicate parsing and multiple object instances. For all duplicate references, the same cached `FileModel` instance is used.
- Pydantic first calls the `FileModel.validate` and then the initializer (`FileModel.__new__` and `FileModel.__init__`).

## In detail:
=> **User initializes a new root FileModel from file**:
1) `FileModel.__new__(cls, filepath: str/Path)`
	- Returns the result of the default `__new__` function
2) `FileModel.__init__(self, filepath: str/Path)`
	- `self` holds the FileModel instance that was returned in step 1.
	- `filepath` is *assumed* to hold the absolute file path to the root file.
	- Updates the global variable `context_dir` with the parent directory of `filepath`. 
	- Caches this FileModel instance (`self`) in the static class variable `FileModel._file_models_cache` with the `filepath`.
	- Loads the data (`dict`) from the file.
	- Initialize `self` with the data.
	- => **Pydantic tries to convert the data to objects, a.o. sub FileModels**:
3) `FileModel.validate(value: str)`
	- `value` holds a relative or absolute file path to the referenced file.
	- If `value` is not an absolute file path, resolves the absolute path by using the directory stored in the `context_dir`, previously set in step 2.
	- Calls `super().validate(value)` with the absolute file path stored in `value`.
	- => **Pydantic create a new FileModel with the data**:
4) `FileModel.__new__(cls, filepath: str)`
	- `filepath` holds the absolute file path that was resolved in step 3.
	- If `FileModel._file_models_cache` already contains a FileModel instance with this `filepath`, returns the cached instance,
		- Otherwise, returns the result of the default `__new__` function.
5) `FileModel.__init__(self, filepath: str)`
	- `self` holds the FileModel instance that was returned in step 4.
	- `filepath` holds the absolute file path that was resolved in step 3.
	- If `FileModel._file_models_cache` already contains a FileModel instance with this `filepath`, returns immediately: no initialization is done.
	- Else, caches this FileModel instance (`self`) in the static class variable `FileModel._file_models_cache` with the `filepath`.
	- Loads the data (`dict`) from the file.
	- Initialize `self` with the data.
	- => **Pydantic tries to convert the data to objects, a.o. sub FileModels**:
6) Repeat steps 3-5