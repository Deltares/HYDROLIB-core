# Installation using pip

You can use a pip-based installation if you simply
want to use hydrolib-core, without making contributions
to the package yourself.

You should be able to install hydrolib-core with:
``` bash
pip install hydrolib-core
```

## Conda specifics
!!! note
    If you use `conda`, it is advisable to install hydrolib-core
    within a new environment with only `conda-forge` as channel. 

If you want to create a fresh test environment for hydrolib-core, you could use the following command (only once):
``` bash
conda create -n hydrolib python=3.8 -c conda-forge
```
Prior to the `pip install`, first activate the desired environment:
``` bash
conda activate hydrolib
```

<!--- or if you prefer (especially on Windows)

``` bash
conda install hydrolib-core -c conda-forge
```

-->

After successful installation, you should be able to do the ["Basic Model" tutorial](../tutorials/build_basic_model.ipynb).
