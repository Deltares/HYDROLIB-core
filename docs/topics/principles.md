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

- The file resolver and the model cache are stored in context variable `context_file_loading`, such that referenced files can be found.
- During loading, the parsed data from files are cached in the `FileLoadContext` to ensure multiple references to the same model will not result in duplicate parsing and instances.
- Pydantic first calls the `FileModel.validate` and then the initializer (`FileModel.__new__` and `FileModel.__init__`).

## In detail:

**User initializes a new root FileModel from file**:

1. `FileModel.__new__(cls, filepath: str/Path)`
	- Returns the result of the default `__new__` function
2. `FileModel.__init__(self, filepath: str/Path)`
	- `self` holds the FileModel instance that was returned in step 1.  
	- `filepath` is holds the file path to the root file.
	- Registers this model in the `FileLoadContext` with the file path.
	- Resolves the absolute path to this model.
	- Adds the folder of this model to the file resolver, such that the children can be resolved as well.
	- Loads the data (`dict`) from the file.
	- Initialize `self` with the data.
	- **Pydantic tries to convert the data to objects, a.o. sub FileModels**:
3. `FileModel.validate(value: str)`
	- `value` holds a relative or absolute file path to the referenced file.
	- If `value` is not an absolute file path, resolves the absolute path by using the `FileLoadContext` stored in the `context_file_loading`, previously set in step 2.
	- Calls `super().validate(value)` with the file path stored in `value`.
	- **Pydantic create a new FileModel with the data**:
4. `FileModel.__new__(cls, filepath: str)`
	- `filepath` holds the file path.
	- If `FileModel._file_models_cache` already contains a FileModel instance with this `filepath`, returns the cached instance,
		- Otherwise, returns the result of the default `__new__` function.
6. Repeat steps 2-4

# Parsing and serializing `INIBasedModels`
Parsing an INI file should be case-insensitive. To achieve this, the parsable field names of each `INIBasedModel` should be equal to the expected key in the file in lower case. 

Some property values are explicitly made case-insensitive for parsing as well. This applies to enum values and values that represent a specific type of `INIBasedModel`, such as the type property of a structure. To support this, custom validators are placed to compare the given value with the available known values. Structures are initialized based on the value in the `type` field. The value of this field of each subclass of a `Structure` is compared to the input and the subclass with the corresponding type is initialized. 

The serialization of an `INIBasedModel` to an INI file should respect certain casing rules (overriding the casing used by the user):
- Property keys need to be "lowerCamelCase"
- Section headers need to be "UpperCamelCase"

To achieve this, each serializable field in a `INIBasedModel` has an alias. This alias will be written as property key to file. Each `INIBasedModel` that represents an INI section, has a field `_header`. The default value of this field will be written to file.
Enum values and the values that represent a specific type of `INIBasedModel` will be serialized to file by how they are defined.
