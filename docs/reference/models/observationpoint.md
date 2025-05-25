# Observation point files
Observation point files come in two flavours:

* the official `*_obs.ini` format [see below](#observation-point-ini-files)
* the legacy `*.xyn` format  [see below](#legacy-observation-point-xyn-files)

# Observation point .ini files
The `obs` module provides the specific logic for accessing observation point .ini files
for a [D-Flow FM](glossary.md#d-flow-fm) model.

Generic parsing and serializing functionality comes from the generic hydrolib.core.dflowfm.ini modules.

An observation point .ini file is described by the classes below.

## Model

::: hydrolib.core.dflowfm.obs.models

# Legacy observation point .xyn files
The `xyn` module provides the specific logic for accessing legacy observation point files
for a [D-Flow FM](glossary.md#d-flow-fm) model.

An observation point .xyn file is described by the classes below.

## Model

::: hydrolib.core.dflowfm.xyn.models
