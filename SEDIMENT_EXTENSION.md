# Sediment-removal robotics extension

## Purpose

This extension turns an IR-SIM navigation experiment into a simplified dam
sedimentation survey and removal study. A mobile robot follows autonomous
routes over a two-dimensional reservoir footprint while a separate grid stores
sediment thickness above a reference bed.

## What is modeled

- Synthetic sediment deposits with reproducible spatial texture.
- Noisy sediment-thickness readings and configurable dropouts.
- An online map that preserves unobserved cells as unknown.
- Circular removal-tool footprint and fractional removal efficiency.
- Full-coverage and hotspot-first autonomous routes.
- Travel distance, sampled coverage, removed volume and a comparative energy
  index.

## What is not modeled

- Water flow and sediment transport.
- Resuspension and turbidity plumes.
- Dredge-pump curves, hose losses or disposal logistics.
- Bathymetric sonar beam geometry.
- Dam structural interaction.
- Ecological effects, regulation or permitting.

The simulator is suitable for comparing navigation and sampling strategies. It
is not sufficient for selecting physical dredging equipment or predicting the
sediment volume in a real reservoir without calibrated survey data.

See [`DESIGN_REQUIREMENTS.md`](DESIGN_REQUIREMENTS.md) for a requirement-by-
requirement record of what the current model can and cannot evaluate.

## Architecture

```text
IR-SIM navigation and collision
              │
              ▼
       robot XY position
              │
       ┌──────┴────────┐
       ▼               ▼
noisy sounding    removal footprint
       │               │
       ▼               ▼
estimated map     mutable true field
       └──────┬────────┘
              ▼
      route-comparison metrics
```

`irsim/sediment/field.py` owns the environmental model and measurements.
`irsim/sediment/routes.py` owns route generation and comparable experiments.
The example in `usage/27sediment_dam` produces a visual comparison and printed
metrics.