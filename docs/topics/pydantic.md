# Pydantic

## Pydantic override
We love using Pydantic :heart:, but we need have multiple overrides in place to enable specific functionality.
This document tries to document these instances, as they are in essence exceptions to an otherwise
well understood and documented architecture.

### BaseModel `__init__` override
We override de `__init__` method to catch all validation errors and reissue them with an better error message.

### FileModel override
We override both `__new__` and `__init__` of the `FileModel` to cache models from disk.
The `FileModel` utilises the `FileLoadContext` to resolve relative paths and to retrieve
models previously read as part of the loading of a root model. 


Specifically we also use it to load a filepath from disk.

This mostly happens in `validate`, a Pydantic override, to make
sure that if we initialize with a single unnamed argument (Pydantic only accepts keyword arguments)
we try to parse it as a filepath.

### ForcingBase, Structure and CrossSectionDefinition `validate` override
Validate is overriden to try to initialize the correct subclass of ForcingBase and CrossSectionDefinition, as discriminated unions do not work yet in Pydantic. I.e. if you specify Union{A, B} and A and B have clearly defined Literals it still can't choose whether to create A or B. The [PR](https://github.com/samuelcolvin/pydantic/pull/2336) to fix this hasn't been merged yet.

:thumbsdown: The code is duplicated in three places.

### INIBasedModel `validate` override
In INIBasedModel we override validate to make sure we can flatten any `Section` input coming from the parser.

:question: Couldn't this be done in the parser?


### Structure Root validator explicitely checks subclass
Because the validation behaviour is different for `Compound`, `Dambreak` etc. We might want to split these things once a new Pydantic release has been made that allows a root_validator to be overriden.
