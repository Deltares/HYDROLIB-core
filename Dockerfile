# Dockerfile to specify the devcontainer for HYDROLIB-Core.
#   A guide how to utilise dev containers within HYDROLIB can be found here:
#       https://deltares.github.io/HYDROLIB-core/guides/devcontainers/
# 
#   For more information about dev-containers in general, please refer to 
#       https://aka.ms/vscode-docker-python
FROM python:3.9-buster as python-base

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VERSION=1.1.11 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    POETRY_NO_ANSI=1\
    \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    # deps for installing poetry
    curl \
    # deps for building python deps
    build-essential

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python

# `development` image is used during development / testing
FROM python-base as development
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install git, to ensure the git tools work within vs-code
RUN apt-get update \
    && apt-get install git-all --no-install-recommends -y

COPY --from=python-base $POETRY_HOME $POETRY_HOME

WORKDIR /app

# The actual 'poetry install' is called after the code is mounted. 
# See '.devcontainer/devcontainer.json'

EXPOSE 8000
