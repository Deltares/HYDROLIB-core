# INI format

The ini module provides the generic logic for parsing Deltares ini based files, such as the mdu, structures files, as well as more complex files such as the boundary condition (bc) files.

Note that specific attribute files that employ this ini format often have their own dedicated module (and separate API doc page). These include:

- [MDU file](mdu.md) (`hydrolib.core.io.dflowfm.mdu`)
- [External forcing file](ext.md) (`hydrolib.core.io.dflowfm.ext`)
- [Initial fields and parameter file](inifield.md) (`hydrolib.core.io.dflowfm.inifield`)
- [Structure file](structure.md) (`hydrolib.core.io.dflowfm.structure`)
- [1D roughness](friction.md) (`hydrolib.core.io.dflowfm.friction`)
- [Cross section files](crosssection.md) (`hydrolib.core.io.dflowfm.crosssection`)
- [Storage node file](storagenode.md) (`hydrolib.core.io.dflowfm.storagenode`)

Following below is the documentation for the INI format base classes.

## Model

::: hydrolib.core.io.dflowfm.ini.models

## Parser

::: hydrolib.core.io.dflowfm.ini.parser

## Serializer

::: hydrolib.core.io.dflowfm.ini.serializer