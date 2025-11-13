# FMModel attributes: consolidated diagram

This page provides a single, consolidated Mermaid diagram that shows all top‑level attributes of `FMModel` and how they connect to their section types. Optional sections are visually highlighted.

Looking for complete per‑section property lists? See: [FMModel attributes: detailed class diagrams](fm-model-attributes-detailed.md).

```mermaid
classDiagram
    direction LR

    class FMModel {
      +general: General
      +geometry: Geometry
      +volumetables: VolumeTables
      +numerics: Numerics
      +physics: Physics
      +sediment: Sediment
      +wind: Wind
      +waves: Waves (optional)
      +time: Time
      +restart: Restart
      +external_forcing: ExternalForcing
      +hydrology: Hydrology
      +trachytopes: Trachytopes
      +output: Output
      +calibration: Calibration (optional)
      +grw: GroundWater (optional)
      +processes: Processes (optional)
      +particles: Particles (optional)
      +veg: Vegetation (optional)
    }

    class General
    class Geometry
    class VolumeTables
    class Numerics
    class Physics
    class Sediment
    class Wind
    class Waves
    class Time
    class Restart
    class ExternalForcing
    class Hydrology
    class Trachytopes
    class Output
    class Calibration
    class GroundWater
    class Processes
    class Particles
    class Vegetation

    %% Associations with role labels matching FMModel attribute names
    FMModel *-- General : general
    FMModel *-- Geometry : geometry
    FMModel *-- VolumeTables : volumetables
    FMModel *-- Numerics : numerics
    FMModel *-- Physics : physics
    FMModel *-- Sediment : sediment
    FMModel *-- Wind : wind
    FMModel -- Waves : waves (optional)
    FMModel *-- Time : time
    FMModel *-- Restart : restart
    FMModel *-- ExternalForcing : external_forcing
    FMModel *-- Hydrology : hydrology
    FMModel *-- Trachytopes : trachytopes
    FMModel *-- Output : output
    FMModel -- Calibration : calibration (optional)
    FMModel -- GroundWater : grw (optional)
    FMModel -- Processes : processes (optional)
    FMModel -- Particles : particles (optional)
    FMModel -- Vegetation : veg (optional)
```

Notes

- Required sections use composition links (`*--`).
- Optional sections use a plain association (`--`) and are labeled “(optional)”.
- Field‑level details for each section are documented on their respective reference pages and in the broader `FMModel` diagrams page.

## How to include in navigation

If you maintain the MkDocs navigation manually, add this page under “D-Flow FM → MDU” in `mkdocs.yml`:

```yaml
- reference/dflowfm/mdu/fmmodel-attributes-overview.md
```

Mermaid is already enabled via `pymdownx.superfences` with the `mermaid` fence in this project.
