"""Bathymetric sediment field, noisy soundings, mapping, and removal.

Depth values are sediment thickness in metres above a fixed reference bed. The
model is intentionally 2.5D: IR-SIM handles horizontal robot navigation while
this grid supplies the environmental quantity a dredging robot measures and
changes. It is an engineering experiment model, not a hydrodynamic solver.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SensorReading:
    x: float
    y: float
    thickness: float | None
    true_thickness: float
    noise_std: float

    @property
    def valid(self) -> bool:
        return self.thickness is not None


class SedimentField:
    """Mutable reservoir-bed thickness grid with reproducible sensor noise."""

    def __init__(
        self,
        thickness: np.ndarray,
        *,
        width: float,
        height: float,
        seed: int = 0,
    ) -> None:
        values = np.asarray(thickness, dtype=float)
        if values.ndim != 2 or min(values.shape) < 2:
            raise ValueError("thickness must be a two-dimensional grid")
        if width <= 0 or height <= 0:
            raise ValueError("field dimensions must be positive")
        if np.any(values < 0):
            raise ValueError("sediment thickness cannot be negative")
        self.thickness = values.copy()
        self.width = float(width)
        self.height = float(height)
        self.rng = np.random.default_rng(seed)

    @classmethod
    def reservoir(
        cls,
        *,
        width: float = 60.0,
        height: float = 30.0,
        resolution: float = 1.0,
        seed: int = 7,
    ) -> SedimentField:
        """Create a plausible synthetic delta with several accumulation lobes."""
        if resolution <= 0:
            raise ValueError("resolution must be positive")
        cols = max(2, round(width / resolution) + 1)
        rows = max(2, round(height / resolution) + 1)
        x = np.linspace(0.0, width, cols)
        y = np.linspace(0.0, height, rows)
        xx, yy = np.meshgrid(x, y)

        # Broad inflow delta, a channel-bank deposit, and a dam-adjacent mound.
        base = 0.10 + 0.10 * (1.0 - xx / width)
        lobes = (
            2.2 * np.exp(-(((xx - 12.0) / 10.0) ** 2 + ((yy - 16.0) / 7.0) ** 2))
            + 1.4 * np.exp(-(((xx - 31.0) / 8.0) ** 2 + ((yy - 8.0) / 5.0) ** 2))
            + 0.9 * np.exp(-(((xx - 50.0) / 5.0) ** 2 + ((yy - 23.0) / 4.0) ** 2))
        )
        texture = cls._smooth_noise((rows, cols), seed) * 0.12
        return cls(np.maximum(0.0, base + lobes + texture), width=width, height=height, seed=seed)

    @staticmethod
    def _smooth_noise(shape: tuple[int, int], seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed)
        noise = rng.normal(0.0, 1.0, shape)
        for _ in range(4):
            noise = (
                noise
                + np.roll(noise, 1, 0)
                + np.roll(noise, -1, 0)
                + np.roll(noise, 1, 1)
                + np.roll(noise, -1, 1)
            ) / 5.0
        return noise

    @property
    def cell_area(self) -> float:
        return (self.width / (self.thickness.shape[1] - 1)) * (
            self.height / (self.thickness.shape[0] - 1)
        )

    @property
    def total_volume(self) -> float:
        """Approximate deposited volume in cubic metres."""
        return float(self.thickness.sum() * self.cell_area)

    def _index(self, x: float, y: float) -> tuple[int, int]:
        if not (0.0 <= x <= self.width and 0.0 <= y <= self.height):
            raise ValueError("position is outside the reservoir")
        col = round(x / self.width * (self.thickness.shape[1] - 1))
        row = round(y / self.height * (self.thickness.shape[0] - 1))
        return row, col

    def depth_at(self, x: float, y: float) -> float:
        row, col = self._index(x, y)
        return float(self.thickness[row, col])

    def sense(
        self,
        x: float,
        y: float,
        *,
        noise_std: float = 0.04,
        dropout: float = 0.02,
    ) -> SensorReading:
        if noise_std < 0 or not 0.0 <= dropout <= 1.0:
            raise ValueError("invalid sensor noise or dropout")
        true = self.depth_at(x, y)
        measured = None
        if self.rng.random() >= dropout:
            measured = max(0.0, true + float(self.rng.normal(0.0, noise_std)))
        return SensorReading(x, y, measured, true, noise_std)

    def remove(self, x: float, y: float, *, radius: float = 1.4, efficiency: float = 0.45) -> float:
        """Remove a fraction inside a circular cutter footprint; return m³ removed."""
        if radius <= 0 or not 0.0 <= efficiency <= 1.0:
            raise ValueError("invalid removal radius or efficiency")
        xs = np.linspace(0.0, self.width, self.thickness.shape[1])
        ys = np.linspace(0.0, self.height, self.thickness.shape[0])
        xx, yy = np.meshgrid(xs, ys)
        mask = (xx - x) ** 2 + (yy - y) ** 2 <= radius**2
        before = float(self.thickness[mask].sum())
        self.thickness[mask] *= 1.0 - efficiency
        return (before - float(self.thickness[mask].sum())) * self.cell_area


class SedimentMapper:
    """Online local-average map that preserves unknown cells as NaN."""

    def __init__(self, rows: int, cols: int, *, width: float, height: float) -> None:
        if min(rows, cols) < 2:
            raise ValueError("map needs at least two rows and columns")
        self.width = float(width)
        self.height = float(height)
        self.sums = np.zeros((rows, cols), dtype=float)
        self.counts = np.zeros((rows, cols), dtype=int)

    def update(self, reading: SensorReading) -> None:
        if not reading.valid:
            return
        col = round(reading.x / self.width * (self.sums.shape[1] - 1))
        row = round(reading.y / self.height * (self.sums.shape[0] - 1))
        self.sums[row, col] += float(reading.thickness)
        self.counts[row, col] += 1

    @property
    def estimate(self) -> np.ndarray:
        result = np.full_like(self.sums, np.nan)
        np.divide(self.sums, self.counts, out=result, where=self.counts > 0)
        return result

    @property
    def coverage(self) -> float:
        return float(np.count_nonzero(self.counts) / self.counts.size)