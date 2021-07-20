# First principles
hydrolib-core-core is structured around the input and output files (I/O) of the DHYDRO suite.

# Inheritance/file handling
In the `basemodel.py` a first hierarchy is given that will recursively load the implicit nested structure that we support in HYDROLIB.

For example, when parsing a DIMR file, one could happen upon a reference to an MDU file (defined as `model` here.)

```
DIMR(model=Path(test_data_dir / "test.mdu"))
```

Because `model` is defined as a `FMModel`, initializing this class
will try to load and parse this file as well, with its own
possible reference to other files, such as a network .nc file.
