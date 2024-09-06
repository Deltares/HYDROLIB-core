# Observation cross section files

Observation cross section files come in two flavours:

* the official `*_crs.ini` format [see below](#observation-cross-section-ini-files)
* the legacy `*.pli` format  [see below](#legacy-observation-cross-section-pli-files)

# Observation cross section .ini files
The `obscrosssection` module provides the specific logic for accessing observation cross section .ini files.
for a [D-Flow FM](glossary.md#d-flow-fm) model.

Generic parsing and serializing functionality comes from the generic hydrolib.core.dflowfm.ini modules.

An observation cross section .ini file is described by the classes below.

## Model

::: hydrolib.core.dflowfm.obscrosssection.models

# Legacy observation cross section .pli files
Legacy .pli files for observation points are supported via the generic `polyfile` module.

A polyfile (hence also an observation cross section .pli file) is described by the classes below.

## Model

::: hydrolib.core.dflowfm.polyfile.models
