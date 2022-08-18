# INI format

The ini module provides the generic logic for parsing Deltares ini based files, such as the mdu, structures files, as well as more complex files such as the boundary condition (bc) files.

Note that specific attribute files that employ this ini format often have their own dedicated module (and separate API doc page). These include:

- [MDU file](mdu.md) (`hydrolib.core.io.mdu`)
- [External forcing file](ext.md) (`hydrolib.core.io.ext`)
- [Initial fields and parameter file](inifield.md) (`hydrolib.core.io.inifield`)
- [Structure file](structure.md) (`hydrolib.core.io.structure`)
- [1D roughness](friction.md) (`hydrolib.core.io.friction`)
- [Cross section files](crosssection.md) (`hydrolib.core.io.crosssection`)
- [Storage node file](storagenode.md) (`hydrolib.core.io.storagenode`)

Following below is the documentation for the INI format base classes.

## Model

::: hydrolib.core.io.ini.models

## Parser

::: hydrolib.core.io.ini.parser

## Serializer

::: hydrolib.core.io.ini.serializer