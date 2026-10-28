import numpy as np
import pytest

from irsim.sediment import (
    SedimentField,
    SedimentMapper,
    compare_routes,
    lawnmower_route,
)


def test_reservoir_is_reproducible_and_nonnegative():
    first = SedimentField.reservoir(seed=4)
    second = SedimentField.reservoir(seed=4)
    np.testing.assert_allclose(first.thickness, second.thickness)
    assert np.all(first.thickness >= 0)
    assert first.total_volume > 0


def test_sensor_noise_is_seeded_and_dropout_stays_unknown():
    field = SedimentField.reservoir(seed=8)
    same = SedimentField.reservoir(seed=8)
    assert field.sense(5, 5).thickness == pytest.approx(same.sense(5, 5).thickness)
    missing = field.sense(5, 5, dropout=1.0)
    assert not missing.valid
    assert missing.thickness is None


def test_removal_reduces_volume_and_never_goes_negative():
    field = SedimentField.reservoir()
    before = field.total_volume
    removed = field.remove(12, 16, efficiency=0.7)
    assert removed > 0
    assert field.total_volume == pytest.approx(before - removed)
    assert np.all(field.thickness >= 0)


def test_mapper_does_not_turn_unknown_cells_into_zero():
    field = SedimentField.reservoir()
    mapper = SedimentMapper(*field.thickness.shape, width=field.width, height=field.height)
    mapper.update(field.sense(2, 3, noise_std=0, dropout=0))
    assert np.count_nonzero(np.isfinite(mapper.estimate)) == 1
    assert np.isnan(mapper.estimate).sum() == mapper.estimate.size - 1


def test_routes_are_valid_and_comparable():
    field = SedimentField.reservoir(width=20, height=10, resolution=1)
    route = lawnmower_route(field.width, field.height, lane_spacing=2)
    assert route.shape[1] == 2
    results = compare_routes(field)
    assert {result.name for result in results} == {"full-coverage", "hotspot-first"}
    assert all(result.distance_m >= 0 and result.removed_m3 >= 0 for result in results)