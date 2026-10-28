"""Coverage routes and comparable sediment-removal experiment metrics."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import numpy as np

from .field import SedimentField, SedimentMapper


@dataclass(frozen=True)
class RouteMetrics:
    name: str
    distance_m: float
    removed_m3: float
    mapped_fraction: float
    samples: int
    energy_index: float


def lawnmower_route(width: float, height: float, *, lane_spacing: float = 2.0) -> np.ndarray:
    """Alternating full-width reservoir transects."""
    if lane_spacing <= 0:
        raise ValueError("lane spacing must be positive")
    lanes = np.arange(0.0, height + lane_spacing / 2, lane_spacing)
    points: list[tuple[float, float]] = []
    for index, y in enumerate(np.clip(lanes, 0.0, height)):
        points.extend(((0.0, y), (width, y)) if index % 2 == 0 else ((width, y), (0.0, y)))
    return np.asarray(points, dtype=float)


def hotspot_route(field: SedimentField, *, threshold: float = 0.7, spacing: float = 2.0) -> np.ndarray:
    """Nearest-neighbour route through cells above a relative-depth threshold."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between zero and one")
    cutoff = float(field.thickness.min() + threshold * np.ptp(field.thickness))
    rows, cols = np.nonzero(field.thickness >= cutoff)
    if len(rows) == 0:
        return np.array([[0.0, 0.0]])
    candidates = np.column_stack(
        (cols / (field.thickness.shape[1] - 1) * field.width,
         rows / (field.thickness.shape[0] - 1) * field.height)
    )
    # Thin dense hotspot pixels to approximately the requested spacing.
    quantized = np.round(candidates / max(spacing, 1e-6)).astype(int)
    _, unique = np.unique(quantized, axis=0, return_index=True)
    remaining = list(candidates[np.sort(unique)])
    route = [np.array([0.0, 0.0])]
    while remaining:
        current = route[-1]
        index = int(np.argmin([np.linalg.norm(point - current) for point in remaining]))
        route.append(remaining.pop(index))
    return np.asarray(route)


def _resample(route: np.ndarray, step: float) -> np.ndarray:
    points = [np.asarray(route[0], dtype=float)]
    for start, end in pairwise(route):
        length = float(np.linalg.norm(end - start))
        segments = max(1, int(np.ceil(length / step)))
        points.extend(start + (end - start) * fraction for fraction in np.linspace(0, 1, segments + 1)[1:])
    return np.asarray(points)


def evaluate_route(
    name: str,
    source: SedimentField,
    route: np.ndarray,
    *,
    sample_step: float = 1.0,
    remove: bool = True,
) -> RouteMetrics:
    field = SedimentField(source.thickness, width=source.width, height=source.height, seed=19)
    mapper = SedimentMapper(*source.thickness.shape, width=source.width, height=source.height)
    points = _resample(np.asarray(route, dtype=float), sample_step)
    distance = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
    removed = 0.0
    for x, y in points:
        reading = field.sense(float(x), float(y), noise_std=0.05, dropout=0.03)
        mapper.update(reading)
        if remove and reading.valid:
            removed += field.remove(float(x), float(y))
    # Simple comparative proxy: travel plus removal work, not electrical joules.
    energy = distance + 2.5 * removed
    return RouteMetrics(name, distance, removed, mapper.coverage, len(points), energy)


def compare_routes(field: SedimentField) -> list[RouteMetrics]:
    return [
        evaluate_route("full-coverage", field, lawnmower_route(field.width, field.height)),
        evaluate_route("hotspot-first", field, hotspot_route(field)),
    ]