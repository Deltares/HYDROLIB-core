# INI format

The ini module provides the generic logic for parsing Deltares ini based files, such as the mdu, structures files, as well as more complex files such as the boundary condition (bc) files.

Note that specific attribute files that employ this ini format often have their own dedicated module (and separate API doc page). These include:

- [MDU file](mdu.md) (`hydrolibcore.io.dflowfm.mdu`)
- [External forcing file](ext.md) (`hydrolibcore.io.dflowfm.ext`)
- [Initial fields and parameter file](inifield.md) (`hydrolibcore.io.dflowfm.inifield`)
- [Structure file](structure.md) (`hydrolibcore.io.dflowfm.structure`)
- [1D roughness](friction.md) (`hydrolibcore.io.dflowfm.friction`)
- [Cross section files](crosssection.md) (`hydrolibcore.io.dflowfm.crosssection`)
- [Storage node file](storagenode.md) (`hydrolibcore.io.dflowfm.storagenode`)

Following below is the documentation for the INI format base classes.

## Model

::: hydrolibcore.io.dflowfm.ini.models

## Parser

::: hydrolibcore.io.dflowfm.ini.parser

## Serializer

::: hydrolibcore.io.dflowfm.ini.serializer