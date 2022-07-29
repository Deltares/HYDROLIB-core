# HYDROLIB-Core - Binder Support

HYDROLIB-Core binder support is done via Docker. This allows us to get python 3.9 and 
all necessary dependencies. [The Dockerfile](Dockerfile) copies the current 
HYDROLIB-Core root directory to home, and installs it, after which HYDROLIB-Core and all
necessary dependencies are available from within binder.

## binder directory

The `binder` directory stores all files related to the binder set up. The name is picked up
automatically by binder, as such the name should not change.

## References

* [mybinder Dockerfile documentation](https://mybinder.readthedocs.io/en/latest/tutorials/dockerfile.html)
* [the Dockerfile binder example repository](https://github.com/binder-examples/minimal-dockerfile)