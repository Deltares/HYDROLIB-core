# Bubble screens

A **bubble screen** (also called an air curtain) is a row of nozzles on the bed of a waterway
that releases a continuous stream of air bubbles. The rising plume entrains water and creates
a vertical circulation that acts as a hydraulic barrier — for example, to limit salt
intrusion through a lock, hold back sediment, or deter fish from entering a pump inlet.

In D-Flow FM, a bubble screen is declared in the **new-format external forcings file**
(`ExtForceFileNew`) as a `[BubbleScreen]` block. HYDROLIB-core exposes it as the
[`BubbleScreen`][hydrolib.core.dflowfm.ext.models.BubbleScreen] model.

> BubbleScreen is a **new-format-only** construct. There is no legacy `QUANTITY=…` form
> for it, so `extforce-convert` does not produce or consume `BubbleScreen` blocks.

## Anatomy of a `[BubbleScreen]` block

Every block has four required pieces of information:

| Key         | Type                                 | Meaning                                          |
|-------------|--------------------------------------|--------------------------------------------------|
| `id`        | string                               | Unique identifier within the ext file            |
| location    | polyline                             | Where the screen sits, horizontally              |
| `zLevel`    | float                                | Depth of the nozzle row, in model vertical units |
| `discharge` | scalar / `.bc` filename / `realtime` | Volumetric air-flow rate                         |

An optional `name` field gives a human-readable label.

The **location** can be specified in one of two equivalent ways:

### 1. Inline coordinates

The polyline is embedded directly in the ext file — you give the number of vertices and
two arrays of coordinates.

```ini
[BubbleScreen]
id             = bubbles1
numCoordinates = 4
xCoordinates   = 450 450 550 550
yCoordinates   = 550 650 650 550
zLevel         = -5.0
discharge      = bubble_discharge.bc
```

### 2. External polyline file

The polyline lives in a separate `.pli` file next to the ext file, and the block only
carries a filename reference.

```ini
[BubbleScreen]
id             = bubbles1
locationFile   = simple_bubbles.pli
zLevel         = -5.0
discharge      = bubble_discharge.bc
```

Both forms produce the same simulation. HYDROLIB-core preserves whichever form was read,
so round-tripping an existing model does not silently rewrite it.

> Exactly **one** of the two location styles must be present. A block with neither — or
> with mismatched `numCoordinates` vs. the actual coordinate list length — raises a
> validation error at load time.

## Working with `BubbleScreen` in Python

### Building a new block

```python
from hydrolib.core.dflowfm.ext import BubbleScreen, ExtModel

screen = BubbleScreen(
    id="bubbles1",
    numcoordinates=4,
    xcoordinates=[450.0, 450.0, 550.0, 550.0],
    ycoordinates=[550.0, 650.0, 650.0, 550.0],
    zlevel=-5.0,
    discharge=1.0,  # m3/s as a scalar; or a ForcingModel, or "realtime"
)

ext = ExtModel(bubblescreen=[screen])
ext.filepath = "forcings.ext"
ext.save()
```

Field names in Python are lowercased (`xcoordinates`, `zlevel`, …) but the Pydantic
aliases accept the CamelCase names from the INI file (`xCoordinates`, `zLevel`, …), so
both work when constructing a block from a dict.

### Reading an existing ext file

```python
from hydrolib.core.dflowfm.ext import ExtModel

# read the saved forcings.ext file saved above
ext = ExtModel("forcings.ext")
for screen in ext.bubblescreen:
    print(screen.id, screen.zlevel, screen.discharge)
```

`ExtModel.bubblescreen` is a list; an ext file with no `[BubbleScreen]` blocks gives an
empty list, not `None`.

### Using a `.bc` file for a time-varying discharge

`discharge` accepts three forms:

- a scalar `float` (e.g. `1.5` m³/s, constant),
- the literal string `"realtime"` (the kernel supplies the value at run time),
- a filename string or `ForcingModel` pointing at a `<name>.bc` file — HYDROLIB-core
  resolves it automatically.

The companion `.bc` file uses the quantity name `bubblescreen_discharge`, analogous to
`sourcesink_discharge` for source/sink blocks.

## `BubbleScreen` vs. `SourceSink`

The two look similar — both are INI blocks with an `id`, a polyline/locationFile, and a
`discharge` — but they model different physics and have different field shapes:

|                           | `BubbleScreen`                         | `SourceSink`                                            |
|---------------------------|----------------------------------------|---------------------------------------------------------|
| Models                    | Air-bubble curtain                     | Water / solute injection or extraction                  |
| Vertical placement        | Single `zLevel: float`                 | `zSource` and `zSink`, each scalar **or** 2-value range |
| Paired injector/extractor | No — nozzles are always sources of air | Yes — multi-point polyline pairs a source with a sink   |
| Polyline carries z        | No (plain `.pli` only)                 | Yes — 3- or 5-column `.pliz` encodes vertical placement |
| Legacy `QUANTITY=` form   | No — new format only                   | Yes: `discharge_salinity_temperature_sorsin`            |

If your model previously used a `SourceSink` block to *approximate* a bubble screen, the
migration is straightforward: replace `zSource` with `zLevel`, drop any `zSink`, and
change the header to `[BubbleScreen]`.

## Validation behaviour

HYDROLIB-core's validator rules for a `BubbleScreen` block:

1. **Location specification is required.** Either `locationFile` **or** the triplet
   `numCoordinates` + `xCoordinates` + `yCoordinates` must be present, otherwise the
   block raises `ValueError`.
2. **Coordinate count consistency.** When inline coordinates are used, both arrays must
   have exactly `numCoordinates` entries.
3. **`zLevel` is required.** Unlike `SourceSink.zSource`, `BubbleScreen.zLevel` has no
   default; omitting it raises a `ValidationError`.
4. **`discharge` is required.** Same rule.

## Known limitations

- `zLevel` is currently a single `float`. If a future kernel revision accepts a vertical
  range the way `SourceSink.zSource` does, this field will need widening.

## See also

- [`BubbleScreen`][hydrolib.core.dflowfm.ext.models.BubbleScreen] — API reference
- [`SourceSink`][hydrolib.core.dflowfm.ext.models.SourceSink] — sister block for water / solute sources
- [`ExtModel`][hydrolib.core.dflowfm.ext.models.ExtModel] — the new-format ext file model
- [External forcings file reference](../reference/dflowfm/external-forcing/ext.md)
