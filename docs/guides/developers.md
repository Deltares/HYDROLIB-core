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

## Updating documentation

## Testing models, parsers and 

## Adding new functionality

## docstrings postfix for attributes (of moet dit in contribute.md?)

## docstring public API