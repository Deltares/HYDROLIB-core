# Loading and Saving within HYDROLIB-core

*This article describes the architectural choices of saving and loading, if you are looking for how to save, please refer to the tutorials.*

The motivation of HYDROLIB-core is to provide a python library to interact with the
D-HYDRO suite files. These files generally form a sort of tree structure, with a single
root model (generally a DIMR or an FM model), and different layers of child models 
which are referenced in their parent models. These child models can either be 
referenced relative to their parent models or with absolute file paths. This leads to
potentially complex model structures, which need to be read and written correctly 
by HYDROLIB-core without any changes to either the contents or the structure.

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
design choice is to ensure models are read and written as is. Properties should
not be adjusted nor dropped when reading or writing (unless there is a very 
clear reason to do so). This behaviour should extend to the way the tree structure 
of the models is handled. Therefor, file paths, stored in the `filepath`
property, which are not explicitly set to be absolute are kept relative and resolved
while reading or writing. 

This has the drawback that the file location of a child model is not explicitly
defined without the root model it is part of. Within the current implementation,
child models have no reference to their parent. This simplifies the bookkeeping when
building models in memory, however it also means that it is not possible 
to resolve the absolute path of a child model without also providing the root
model it is part of. This behaviour is further documented in the following sections.
In order to alleviate this shortcoming, each file model internally keeps track of its 
resolved save location, which can be explicitly synchronized with the file path of the
root model, if this is required.

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
relative paths by keeping track of the current parent folder of a model. It also 
provides a cache for read models, which ensures files are not read more than once. 

A single `FileLoadContext` is created at the start of the constructor of the root
model as a context variable. Subsequent child models can then reference this 
`FileLoadContext`, by retrieving this same `FileLoadContext`. A convenience
context manager is provided through the `file_load_context()` method in the 
`basemodel.py`.

The constructor of the filepath performs the following tasks:

1. Request the context.
2. Register itself within the model cache with its file path.
3. Store the absolute file path anchor (i.e. the absolute path to its parent)
4. Resolve its absolute path, to read from.
5. Update the current parent directory.
6. Read all the model data including sub-models.
7. Remove itself as a parent directory.

Because the constructor recursively reads child models, and the data is only read after
the current parent directory has been updated, the child models will correctly resolve
their resolve their relative paths. 

The `FileModel` further overrides its `__new__`. During the `__new__` call, it will 
verify if the current (resolved) filepath which is being read, has already been 
defined in the file model cache. If it is, then this instance will be returned, 
instead of creating a new instance through the `__init__`. This ensures no duplicates
are created.

## Saving Models: Traversing the model tree with the `ModelTreeTraverser`

Currently, the save function on the `FileModel` offers the following options:

* `filepath`:  Allows the user to set a new file path. If none is defined, the current file path will be used.
* `recurse`: A flag indicating whether only this model needs to be saved, or also it child models.

As such it is possible to store both individual models, as well as model trees. 

When saving a model, it will be stored at the `save_location`. If `recurse` is true, then
the child model will be evaluated with regards to the root model. This may lead to some 
inconsistencies, especially with the deprecated `pathsRelativeToParent` set to false in 
the FlowFM model. As such care needs to be taken by the user.

The `save_location` of relative child models will **NOT** be automatically updated when the
parent `filepath` is updated. If such an update is required the user is expected to call 
`synchronize_filepaths` on the parent model.

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

1. Ensure the file paths of both the model and all of its children are set.
2. Save the the models and its children recursively.

We need to ensure all file paths are set before we store the models, in order to 
resolve the actual file paths during the save operation. As such these two operations
are done in separate steps. 

Both of these tasks make use of the `ModelTreeTraverser`. It will traverse through
any immediate file link model, and execute the pre and post functions for any file link. 
In case of task 1, it will generate the file paths if none is set. The save traversal
uses the pre and post traverse functions to maintain the parent path used to resolve the
relative file paths of any models. The post function is further used to actually
write the model to file through a dedicated `_save` function.

### Saving a sub-tree relative to some model tree

Saving a sub tree is in principle the same as calling `save` on the root model, but only
a child model. One thing that should be taken into account is, the save is called relative
to the current value in `save_location`. As such if changes were made to the `filepath`
of a parent model, `synchronize_filepaths` should be called on the root model.

### Saving individual models without their children

An individual model can be saved with the `save` and `recurse` set to `False` (i.e. 
the default behaviour). When this is done, only the model on which `save` was called
will be written to disk at the current `save_location`.

### Exporting / Save as

Exporting is currently not implemented, but will be as part of [issue #170](https://github.com/Deltares/HYDROLIB-core/issues/170).

## Inheritance hierachy of FileModels: SerializableFileModels and DiskOnlyFileModels

The `FileModel` is the abstract base class for any file model. It provides the logic 
to manage the file paths as well as the common logic to load and save models.
In order to do so, it requires child classes to implement a `_save` and a `_load`
method. Two child classes have been defined which extend the `FileModel`:

* `SerializableFileModel`: Abstract class which defines a `FileModel` with a 
    serializer and parser. This is the base model used by most in-memory models.
* `DiskOnlyFileModel`: A generic file model which does not read data into memory
    but does copy the underlying file when a parent `FileModel` is saved recursively.

### `SerializableFileModel`

The `SerializableFileModel` defines an abstract base class for in-memory models, it does so by
requiring child classes to define a parser, to read input files, and a serializer, to write the
data again. This forms the basis for most of the in-memory file models.

### `DiskOnlyFileModel`

The `DiskOnlyFileModel` provides a file model implementation for files which do not have a 
representation in `HYDROLIB.Core` (yet). The `DiskOnlyFileModel` ensures the underlying 
file, specified with the `filepath` of the `FileModel`, is copied when a parent model is
saved recursively. It does so by maintaining an internal source file path, which is initialized
at construction of the `DiskOnlyFileModel`. When a `DiskOnlyFileModel` is saved, the underlying
file is copied from this internal source file path to the new target path. If the file at the
source file model does not exist, or the target path is invalid, no file is copied.
Lastly, regardless of whether a file was copied, the internal source file path is updated.

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
