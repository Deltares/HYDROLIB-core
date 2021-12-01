# First steps

Let's import and create a first model.

```python
from hydrolib.core.io.structure.models import FlowDirection, StructureModel, Weir
from hydrolib.core.io.mdu.models import FMModel

fm = FMModel()
fm.filepath = "test.mdu"
```

<!---
We can now add and/or manipulate features within the model.
```python
# Start adding geometry
fm.geometry.netfile.network.mesh1d_add_branch()  # TODO fix example
```
-->

Add some structures, note this is invalid because it doesn't 
have a branch or coordinates yet, but it will work for demo purposes

```python
struc = Weir(branchId='someBranch', chainage = 123.0, allowedflowdir=FlowDirection.none, crestlevel=0.0)
struc.comments.crestlevel = "This is a comment"
fm.geometry.structurefile = [StructureModel(structure=[struc])]
```
Note that the creation of a `Weir` and other models always require
the use of keyword arguments. A `ValidationError` will be raised
when the model isn't correct or complete, for instance, in the case
that `StructureModel` was assigned directly to `structurefile` instead
of as a list.


Now let's add this model to a DIMR config and save it.
```python
from hydrolib.core.io.dimr.models import DIMR, FMComponent
from pathlib import Path
dimr = DIMR()
dimr.component.append(
    FMComponent(name="test", workingDir=".", inputfile=fm.filepath, model=fm)
)
dimr.save(folder=Path("."))
```
The save on the top of the model hierarchy will result in saves of all child models,
so this results in four files (`dimr_config.xml`, `network.nc`, `structures.ini`,`test.mdu`)
in the working directory.
