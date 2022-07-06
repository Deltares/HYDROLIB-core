# Devcontainers: Developing HYDROLIB in an isolated environment

A common struggle while working on any software project, is to ensure all of your 
dependencies are available and you can actually build the software, run the tests etc.
While any developer is free to choose their own toolchain, environment etc, HYDROLIB-Core
includes the necessary files to run the project within a so called devcontainer within
Visual Studio Code. With the help of Docker, we can spin up an independent development environment,
ensuring that HYDROLIB-Core works out of the box and you are insulated from any specific local
configurations on your machines. This should allow you to start working on HYDROLIB-Core quickly. 

The following sub sections will walk you through the necessary dependencies, and how to use it, 
and modify it, to fit your own needs. This will be done in the following order:

* Requirements: Docker and Visual Studio Code Remote - Containers extension
* Dockerfile configures python, poetry and other dependencies
* devcontainer.json specifies how visual studio code should be configured
* External references

## Requirements: Docker and Visual Studio Code Remote - Containers extension

In order to run HYDROLIB in a dev container we need the following dependencies

* [Docker](https://www.docker.com/)
* [Visual Studio Code](https://code.visualstudio.com/)
* [Visual Studio Code Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

Docker will ensure we can spin up an isolated container. A full tutorial on how to use Docker is
outside the scope of this tutorial, however the [Getting Started guide of Docker](https://www.docker.com/get-started) should provide you with the steps to install Docker on your machine.

[Visual Studio Code](https://code.visualstudio.com/) is the editor we will use. The website should provide you with the necessary steps to install it.

Lastly, we need to install the [Visual Studio Code Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers). 
The install button on the marketplace should walk you through the steps to install it. 

## Run HYDROLIB in a devcontainer by executing "Reopen in container" command

With all of the dependencies set up, we should be able to run HYDROLIB within our devcontainer. When opening the HYDROLIB-Core 
repository in Visual Studio Code, we should either get a pop-up asking us to reopen the project within a remote container, 
or we can select the  "Open a Remote Window" button, the green button in the bottom left corner of your visual studio 
code window, after which we can select "Reopen in container". Both will then spin up a new container in which we can work.
Note that if it is the first time starting our repository, or if we have made changes to the Docker Images we might need to build the container, which could take a few moments.

Once opened in a separate container, we can start a terminal to verify everything is 
working correctly. First, we need to ensure the correct python interpreter is used. 
We want to use the virtual environment created by poetry, which default resides in 
`./.venv/`. Visual Studio Code might prompt you to select an interpreter. If it does
press the 'Select Python Interpreter', and select the virtual environment residing in
`./.venv/`. If it does not explicitly prompt you (or if you want to change it later on),
press `ctrl + shift + p`, and select 'Python: Select Interpreter'. If it currently is 
not set to the virtual environment, change it to the correct interpreter.

It should now be possible to run the HYDROLIB-Core tests within our container by opening 
the 'Testing' tab. If the 'Testing' is not already configured in the 
`./.vscode/settings.json`, we will need to configure the Python tests:

1. click the 'Configure Python Tests' button in the 'Testing' tab
2. Select 'pytest' in the pop-up window
3. Select 'tests', this will ensure tests are located in our 'tests' directory

Once this is done all tests should pass as they would normally.

##  Dockerfile configures python, poetry and other dependencies

The Dockerfile which specifies our specific devcontainer can be found [here in the repository](https://github.com/Deltares/HYDROLIB-core/blob/main/Dockerfile).
Currently, it extends the python 3.9 buster image provided by the Python foundation. It then does 
the following:

* Installs Poetry 1.1.11 and configure the necessary paths
* Copies the poetry.lock and pyproject.toml and installs the project
* Installs git within the container

This should provide us with a ready to go environment to run HYDROLIB-Core with.

## devcontainer.json specifies how visual studio code should be configured

We can further customise our environment by editing the [devcontainer.json located here in the repository](https://github.com/Deltares/HYDROLIB-core/blob/main/.devcontainer/devcontainer.json). 
In particular, you can add any Visual Studio Code extensions you require for your work to the extensions field.
Currently it is populated with several common Python extensions which we use to develop HYDROLIB.

For a full overview how to customise this file, [you can find the documentation here](https://code.visualstudio.com/docs/remote/devcontainerjson-reference)

## External references:

* [Developing inside a Container - VS Code docs](https://code.visualstudio.com/docs/remote/containers)
* [Develop with containers - VS Code docs (guide specific for  python)](https://code.visualstudio.com/learn/develop-cloud/containers)
* [Document docker poetry best practices - Poetry issue](https://github.com/python-poetry/poetry/discussions/1879)
