## ini

The ini module provides the generic logic for parsing Deltares ini based files, such as the mdu, structures files, as well as more complex files such as the boundary condition (bc) files.

Note that specific attribute files that employ this ini format often have their own dedicated module (and separate API doc page). These include:

- [MDU file](mdu.md) (```hydrolib.core.io.mdu```)
- [cross section files](crosssection.md) (```hydrolib.core.io.crosssection```)
- [external forcing file](ext.md) (```hydrolib.core.io.ext```)
- [friction](friction.md) (```hydrolib.core.io.friction```)
- [structure file](structure.md) (```hydrolib.core.io.structure```)



### Model

::: hydrolib.core.io.ini.models

### Parser

::: hydrolib.core.io.ini.parser

### Serializer

::: hydrolib.core.io.ini.serializer