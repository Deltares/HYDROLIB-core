# INI format

The ini module provides the generic logic for parsing Deltares ini based files, such as the mdu, structures files, as well as more complex files such as the boundary condition (bc) files.

Note that specific attribute files that employ this ini format often have their own dedicated module (and separate API doc page). These include:

- [MDU file](../dflowfm/mdu/mdu.md) (`hydrolib.core.dflowfm.mdu`)
- [External forcing file](../dflowfm/external-forcing/ext.md) (`hydrolib.core.dflowfm.ext`)
- [Initial fields and parameter file](../dflowfm/external-forcing/inifield.md) (`hydrolib.core.dflowfm.inifield`)
- [Structure file](../dflowfm/external-forcing/structure.md) (`hydrolib.core.dflowfm.structure`)
- [1D roughness](../dflowfm/cross-sections/friction.md) (`hydrolib.core.dflowfm.friction`)
- [Cross section files](../dflowfm/cross-sections/crosssection.md) (`hydrolib.core.dflowfm.crosssection`)
- [Storage node file](../dflowfm/topology-network/storagenode.md) (`hydrolib.core.dflowfm.storagenode`)

Following below is the documentation for the INI format base classes.

## Model

::: hydrolib.core.dflowfm.ini.models

## Parser

::: hydrolib.core.dflowfm.ini.parser

## Serializer

::: hydrolib.core.dflowfm.ini.serializer