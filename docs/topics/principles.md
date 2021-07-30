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
