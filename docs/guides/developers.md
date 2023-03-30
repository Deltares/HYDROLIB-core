# Developer guide
This guide contains some more in-depth guidelines, tasks and examples that developers should adhere to when working on hydrolib-core.
In addition to being a useful resource for developing, this documentation can also be helpful for code reviews.

## Explicitly exposing the public API
Whenever you add new functionality that should (or could) be used by the users, make sure you explicitly expose them in the correct `__init__.py` files.

For example, let's say you have implemented a new `TimModel` that represents a `.tim` file. You have also added a new `TimParser` and `TimSerializer` to read and write from and to `.tim` files. The `TimModel` is a class that should be publicly exposed to the user so that they can use it to represent `.tim` files. The parser and serializer, however, do not need to be exposed, as these are implementation details that we do not want to bother our users with. To expose the `TimModel` explicitly for our users we have to update both the `hydrolib/core/dflowfm/tim/__init__.py` (assuming you created a new `tim` folder for this new functionality) and the `hydrolib/core/dflowfm/__init__.py`:

```python
# hydrolib/core/dflowfm/tim/__init__.py
from .models import TimModel

__all__ = [
    "TimModel",
]
```

```python
# hydrolib/core/dflowfm/__init__.py
...
...
from .tim import *
```

## Updating the documentation
In the hydrolib-core repository there are several reference files that are used to automatically generate the [API reference](../reference/api.md). If you add or make changes to the existing API, always make sure you check if the API reference is still up to date.

For example, let's use the example that was used above, where the `TimModel` was introduced in hydrolib-core. Since this is new functionality that affects the API, we have to update the reference files. The API reference files are located at `docs\reference`. Since the `TimModel` was newly introduced, we should create a new file named `tim.md`. The contents of this file include a short description about what the '.tim' file is and what it is used for, followed by the actual API. You do not have to manually write the API, that is done for us by mkdocs. Since the newly introduced `TimParser` and `TimSerializer` are not part of the public API, they should not be added to the reference file:

```md
# Timeseries .tim files
Timeseries .tim files are timeseries input files 
for a [D-Flow FM](glossary.md#d-flow-fm) model.
The support of .tim files is discontinued and are replaced by the [.bc file](#bc-file).

They are represented by the class below.

## Model
::: hydrolib.core.dflowfm.tim.models

```

## Testing models, parsers and 

## Adding new functionality

## docstrings postfix for attributes (of moet dit in contribute.md?)

## docstring public API