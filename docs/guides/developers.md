# Developer guide
This guide contains some more in-depth guidelines, tasks and examples that developers should adhere to when working on hydrolib-core.
In addition to being a useful resource for developing, this documentation can also be helpful for code reviews.

## Explicitly exposing the public API
Whenever you add new functionality that should (or could) be used by the users, make sure you explicitly expose them in the correct `__init__.py` files.

For example, you have developed a new `TimModel` class that represents a `.tim` file. The `TimModel` makes use of the `TimParser` class and `TimSerializer` class. While the `TimModel` class should be publicly exposed to the users, because it is part of the public API, the parser and serializer classes are implementation details that users should not be concerned with. The parser and serializer should therefore not be publicly exposed to the users. 

To expose the `TimModel` explicitly to our users, you have to update both the `hydrolib/core/dflowfm/tim/__init__.py` (assuming you created a new `tim` folder for this new functionality) and the `hydrolib/core/dflowfm/__init__.py`:

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
In the hydrolib-core repository there are several reference files that are used to automatically generate the [API reference](../reference/api.md). If you add or make changes to the existing API, always make sure the API reference is still up to date.

For example, let's use the example that was used above, where the `TimModel` was introduced in hydrolib-core. Since this is new functionality that affects the API, we have to update the reference files. The API reference files are located at `docs\reference`. Since the `TimModel` was newly introduced, we should create a new file named `tim.md`. The contents of this file include a short description about what the '.tim' file is and what it is used for, followed by the actual API. You do not have to manually write the API, that is done for us by mkdocs. Since the newly introduced `TimParser` and `TimSerializer` are not part of the public API, they should not be added to the reference file. 

An example of such an `.md` can be found below:

```md
# Timeseries .tim files
Timeseries .tim files are timeseries input files 
for a [D-Flow FM](glossary.md#d-flow-fm) model.
The support of .tim files is discontinued and are replaced by the [.bc file](#bc-file).

They are represented by the class below.

## Model
::: hydrolib.core.dflowfm.tim.models

```

### Updating the functionalities sheet
To generate a list of D-HYDRO functionalities, grouped by kernel, and the current status of support inside hydrolib-core, we use an Excel sheet. This Excel sheet can be found at `docs\topics\dhydro_support_hydrolib-core.xlsx`. Each time you add support for new D-HYDRO functionalities, this Excel file has to be updated. Detailed information on how to update the Excel file correctly can be found inside the Excel file itself.
