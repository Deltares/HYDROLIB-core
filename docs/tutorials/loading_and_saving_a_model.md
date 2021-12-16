# Loading and saving a model

In this article we will look at loading and saving a model. First we will load a model,
and store it in a new location. Then make adjustments to one of the sub models, and 
store the model in place. Lastly, we will look at some caveats of saving and loading
models.

If you do not have a DIMR model, you can use [the example model in the test data](https://github.com/Deltares/HYDROLIB-core/tree/main/tests/data/input/e02/c11_korte-woerden-1d/dimr_model).

## Load the model

We can load a model by constructing a new DIMR model by calling the `DIMR` with the
file path to this model:

```python
# assuming the DIMR model is stored in your current working directory.
model_path = Path("./dimr_config.xml")
dimr_model = DIMR(filepath=model_path)
```

## Save the model in a new location

If we want to store the full model in a different location we can use the `save` function:

```python
# Adjust this new_path to a path convenient for you.
new_path = Path("some/other/path/dimr_config.xml")  
dimr_model.save(filepath=new_path, recurse=True)
```

By setting `recurse` to `True` we will ensure all files (which are supported by HYDROLIB-core) 
are written to the new location, relative to the file path of the root model. 
Providing the `filepath` argument has the same result as first setting the filepath, and then
calling save:

```python
new_path = Path("some/other/path/dimr_config.xml")  
dimr_model.filepath = new_path
dimr_model.save(recurse=True)
```

As such, when calling `filepath` after `save` it should be the same as `new_path`.
Once save has been called all files (supported by HYDROLIB-core) should be located in the parent folder.

## Adjust the model in a update it on disk

Now that we have written our model in a different location, we can make some adjustments to it.
We can retrieve the FM sub model as follows:

```python
fm_component = dimr_model.component[1]  # Index 0 corresponds with the RRComponent.
fm_model = fm_component.model
```

We can adjust the model, by for example changing some of the properties. For example let's change the 
`MapInterval` from 60 to 30:

```python
fm_model.output.mapinterval = 30.0
```

With that change made we can go ahead and save just this specific sub model, in order to update the values on disk:

```python
fm_model.save()
```

By default, if no `filepath` is selected, it will be stored in the current `save_location`. This should 
correspond with the place where it was last stored on disk. Furthermore, by default `recurse` is set to 
`False`, as such we will only rewrite the `.mdu` file.

If we now inspect the `.mdu` file, we should see that the `MapInterval` in the `output` header has been set to 30:

```
...
[output]
...
MapInterval       = 30.0
...
```

## Caveats when saving models

There are some caveats to take into account when saving models.

### Filepath changes do not automatically propagate

When changing the `filepath` property of a parent model, the changes in `save_location` will not
automatically propagate. As such, when saving a child model with a relative path, if the parent
model's `filepath` has been changed, the child model will still be saved at its original save location.
In order to update the save location, `synchronize_filepaths` should be called on the root model.

### Synchronizing filepaths is relative to the model it is called upon

`synchronize_filepaths` will only update the file paths of child models. As such it will not propagate
changes mode in a parent model:

```
dimr_model.filepath = Path("some/other/path/dimr_config.xml")
fm_model.synchronize_filepaths()  # This has no effect.
```

Because the `save_location` of the `fm_model` has not been changed, none of the child models will change either.

Furthermore, extra care needs to be taken when dealing with FM models with the `pathsRelativeToParent` set to 
`False`. This option will make all relative paths of child models relative to the `.mdu`. If `synchronize_filepaths` is called on a child model of the fm model, it will instead make all `save_locations` relative to this child model, which is incorrect.

It is recommended to not use `pathsRelativeToParent` set to `False`.
