# Migration & Deprecations

This page lists deprecated public API symbols in HYDROLIB-core, the version
in which they were deprecated, the version in which they will be removed,
and the migration path for each one.

If you depend on a deprecated name, your code will keep working for the
current release line but will emit a `DeprecationWarning` at runtime. We
recommend migrating before the listed removal release.

## How to surface deprecation warnings in your project

Python suppresses `DeprecationWarning` by default outside of test runs. To
surface them in your own application or scripts:

```python
import warnings
warnings.filterwarnings("default", category=DeprecationWarning,
                        module=r"hydrolib\..*")
```

Or run a one-off check with:

```bash
python -W default::DeprecationWarning your_script.py
```

To fail your test suite on any HYDROLIB-core deprecation, configure pytest:

```ini
# pyproject.toml or pytest.ini
[tool.pytest.ini_options]
filterwarnings = [
    "error::DeprecationWarning:hydrolib.*",
]
```

## Quick reference

| Symbol                            | Deprecated in | Removal target | Replacement                       |
|-----------------------------------|---------------|----------------|-----------------------------------|
| `Meteo.forcingVariableName`       | 1.1.0         | 2.0.0          | `Meteo.forcingvariablename`       |
| `Meteo.extrapolationAllowed`      | 1.1.0         | 2.0.0          | `Meteo.extrapolationallowed`      |
| `Meteo.extrapolationSearchRadius` | 1.1.0         | 2.0.0          | `Meteo.extrapolationsearchradius` |
| `Meteo.averagingType`             | 1.1.0         | 2.0.0          | `Meteo.averagingtype`             |
| `Meteo.averagingNumMin`           | 1.1.0         | 2.0.0          | `Meteo.averagingnummin`           |
| `Meteo.averagingPercentile`       | 1.1.0         | 2.0.0          | `Meteo.averagingpercentile`       |

---

## 1.1.0

### `Meteo` attribute names lowercased

The Python attribute names on
[`hydrolib.core.dflowfm.ext.models.Meteo`][hydrolib.core.dflowfm.ext.models.Meteo]
were inconsistent: most fields used lowercase identifiers
(`forcingfile`, `targetmaskfile`, `interpolationmethod`, …) while six fields
used camelCase. These six have been renamed to match the convention.

The on-disk INI key names (e.g. `forcingVariableName = …` in `.ext` files)
**are unchanged** — only Python attribute access changes. Construction by
keyword argument also keeps working with the camelCase form (it goes
through the unchanged Pydantic alias).

**Renamed attributes**

| Old (deprecated)            | New                         |
|-----------------------------|-----------------------------|
| `forcingVariableName`       | `forcingvariablename`       |
| `extrapolationAllowed`      | `extrapolationallowed`      |
| `extrapolationSearchRadius` | `extrapolationsearchradius` |
| `averagingType`             | `averagingtype`             |
| `averagingNumMin`           | `averagingnummin`           |
| `averagingPercentile`       | `averagingpercentile`       |

**Migration — attribute access**

```python
# Before
if meteo.extrapolationAllowed:
    radius = meteo.extrapolationSearchRadius
meteo.averagingType = 1

# After
if meteo.extrapolationallowed:
    radius = meteo.extrapolationsearchradius
meteo.averagingtype = 1
```

**Migration — `model_dump()` output keys**

If you call `meteo.model_dump()` *without* `by_alias=True`, the returned dict
keys reflect the new lowercase attribute names:

```python
# Before:                                After:
{"extrapolationAllowed": True, ...}     {"extrapolationallowed": True, ...}
```

If you need the on-disk INI key names, pass `by_alias=True`:

```python
meteo.model_dump(by_alias=True)
# -> {"extrapolationAllowed": True, ...}
```

The library's own INI serializer always uses `by_alias=True`, so the
contents of `.ext` files on disk are unaffected.

**Not affected**

- Reading existing `.ext` files via `ExtModel(filepath=...)` — wire-format
  keys are unchanged and parsing is case-insensitive.
- Writing `.ext` files via `model.save(...)` — output is byte-identical.
- Constructing `Meteo` with keyword arguments using either the old or new
  name: both work via Pydantic alias resolution.

  ```python
  Meteo(quantity="rainfall",
        forcingfile=ForcingModel(),
        forcingfiletype=MeteoForcingFileType.uniform,
        extrapolationAllowed=True)        # still works, no warning
  ```

