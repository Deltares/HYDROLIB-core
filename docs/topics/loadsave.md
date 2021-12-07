# Loading and Saving within HYDROLIB-core

The motivation of HYDROLIB-core is to provide a python library to interact with the
D-HYDRO suite files. These files generally form a sort of tree structure, with a single
root model (generally a DIMR or FM model), and different layers of child models which 
are defined in their parent models. These child models can either be defined relative
to their parent models or with absolute file paths. This leads to potentially complex
model structures, which need to be read and written correctly HYDROLIB-core without 
any implicit changes to either the contents or the structures.

This article discusses the architectural choices made when designing the read and write 
capabalities, as well as the considerations that should be taken when implementing your
own models. As such we will discuss the following topics:

- Motivation: HYDROLIB-core should not adjust files when reading and writing
- Structure of Models
- Loading Models: Resolving the tree structure with the `FileLoadContext`
- Saving Models: Traversing the model tree with the `ModelTreeTraverser`
- Extensions: Caveats to ensure your model plays nice with HYDROLIB-core

## Motivation: HYDROLIB-core should not adjust files when reading and writing

When implementing the model read and write behaviour of HYDROLIB-core, the main 
motivation is to ensure models are read and written as is. Properties should
not be adjusted nor dropped (unless there is a very clear reason for such changes), 
when either reading or writing. This behaviour should extend to the way the tree 
structure of the models is handled. Therefor, file paths, stored in the `filepath`
property, which are not explicitly set to be absolute are kept relative and resolved
while reading or writing. 

This comes at the cost that the file location of a child model is not explicitly
defined without the root model it is part of. Within the current implementation,
child models have no reference to their parent. This eases the bookkeeping when
building your models in memory, however it also means that it is not possible 
to resolve the absolute path of a child model without also providing the root
model it is part of. This behaviour is further documented in the following sections.

## Loading Models: Resolving the tree structure with the `FileLoadContext`

In order to load a model from disk, we need to call the appropriate constructor with a
file path to an existing model file. The constructor will then ensure the model, and 
its child models are read. Multiple references to the same sub-model will reference
the same sub-model after reading.

### Current Behaviour: Root models are read through the constructor while caching sub-models

Currently, a model is loaded by calling the constructor with the filepath of the input
file. HYDROLIB-core will then load the model as well as any children. Every child will
only be read once, multiple references to the same child in the input files will result
in references to the same child model in memory. When reading the model and its 
children, the file structure will be kept intact. Any models with absolute paths will
still reference the same absolute paths, while models with relative paths will also 
have the same relative paths as within the original file. 

### Architectural Choices: The tree structure is resolved with the `FileLoadContext` 

In order to properly resolve the model tree, we need to be able to keep track of the
current parent of a model, as well as a way to store and retrieve read models. Both
of these tasks are handled by the `FileLoadContext`. The context can be used to resolve
relative paths by keeping track of the current parent folder of a model. It also provides
a cache for read models, which files are not read more than once. 

A single `FileLoadContext` is created at the start of the constructor of the root
model as a context variable. Subsequent child models can then reference this 
`FileLoadContext`, by retrieving this same `FileLoadContext`. A convenience
context manager is provided through the `file_load_context()` method in the 
`basemodel.py`. 

The constructor of the filepath performs the following tasks:

1. Request the context.
2. Register itself within the model cache with its file path.
3. Resolve its absolute path, to read from.
4. Update the current parent directory.
5. Read all the model data including sub-models.
6. Remove itself as a parent directory.

Because the constructor recursively reads child models, and the data is only read after
the current parent directory has been updated, the child models will correctly resolve
their resolve their relative paths. 

The `FileModel` further overrides its `__new__`. During the `__new__` call, it will 
verify if the current (resolved) filepath which is being read, has already been 
defined in the file model cache. If it is, then this instance will be returned, 
instead of creating a new instance through the `__init__`. This ensures no duplicates
are created.

## Saving Models: Traversing the model tree with the `ModelTreeTraverser`

Currently, the save / write logic corresponds with writing the full model tree. This 
can be done through the `save` method provided on any `FileModel`. This will resolve
the relative file paths with respect to the model from which `save` is called, and
maintains the absolute file paths.

### `ModelTreeTraverser`

For writing the models to file, as well as other operations, we need to be able to
traverse the model tree. In order to do so, the `ModelTreeTraverser` is provided.
It can be configured with the following 4 functions:

- **should_traverse**: Evaluates whether to traverse to the provided BaseModel.
- **should_execute**: Determines whether the traverse functions are executed for the given model.
- **pre_traverse_func**: Function called with the current model before traversal into the children, i.e. top-down behaviour.
- **post_traverse_func**: Function called with the current model after traversal into the children, i.e. bottom-up behaviour.

All functions receive an accumulator, which flows through the program and is finally
returned to the caller. This can be used to store state in between calls to traverse
or to build an output value while traversing the model tree.

### Saving a complete model tree

In order to store a model as well as its children, we need to perform the following 
tasks.

1. Ensure the file path of the model as well as its children is set.
2. Save the the models and its children recursively.

We need to ensure all file paths are set before we store the models, in order to 
resolve the actual file paths during the save operation. As such this is done in a
separate step. 

Both of these tasks make use of the `ModelTreeTraverser`. It will traverse through
any immediate file link model, and execute for any file link. In case of the task
1, it will generate the file paths if none is set. The save traversal uses the 
pre and post traverse functions to maintain the parent path used to resolve the
relative file paths of any models. The post function is further used to actually
write the model to file through a dedicated `_save` function.

### Saving a sub-tree relative to some model tree

Currently, saving sub-trees is not supported, however additional discussion related to
this subject can be found in [issue \#96](https://github.com/Deltares/HYDROLIB-core/issues/96).

### Saving individual models without their children

Currently, Saving individual models without their children is not supported, however 
additional discussion related to this subject can be found in 
[issue \#96](https://github.com/Deltares/HYDROLIB-core/issues/96).

### Exporting / Save as

You can export your models by calling the `save` function with the `folder` argument.
This will flatten your model hierarchy to the single provided `folder` and change the
state

## Extensions: Caveats to ensure your model plays nice with HYDROLIB-core

In the most common case, all of the file reading and writing is handled in the `FileModel`
as such, just inheriting from the `FileModel` and providing the required parser and 
setting the `_parser` and `_serializer` will be enough to ensure your model works as
expected. There might be however some exceptions to your model that require additional
configuration. The file model provides several hooks for this:

**For loading:** 

- `_post_init_load`: function called after a model is initialised but before the current `FileLoadContext` is changed. This allows the user to put any actions here which require a `FileLoadContext`. Examples of this can be found in the `DIMR` and `NetworkModel` classes.
- Overwrite `__init__`: We can overwrite the `__init__` of a child the `FileModel` however some care needs to be taken in this case. In particular the `__super__` needs to be called in order to ensure the model is loaded appropriately. Furthermore, if the `FileLoadContext` is required within the `__init__`, the `file_load_context` should be called before `__super__`:

```python

def __init__(self, ...):
    with file_load_context() as context:
        __super__().__init__()
        ...
        # your code using the context
        ...

```

**For saving:**

- `_save`: provides the save functionality called by the recursive saving of models. Overwriting this will allow you complete control over how the model is saved. An example of this can be found in the `NetworkFile`.
- `_serialize`: provides the method to serialize your model. This can be overwritten in case a more specialised serialization is required, for example as done in `IniBasedModel` children.
- `self._resolved_filepath`: will provide you with a resolved absolute version of the `filepath`. This only works in the context of `_save` and `_serialize`, as it relies on the context being started in the `save` method.
