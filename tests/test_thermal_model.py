import numpy as np
import pandas as pd
import pytest

from edge_energy_optimizer.control.thermal_model import ThermalModel, fit

TRUE = ThermalModel(loss_per_h=0.02, heat_k_per_kwh=0.17, solar_k_per_wh_m2=0.0015, drift_k_per_h=-0.05)


def synthetic(model: ThermalModel, hours: int = 400, seed: int = 0, start_c: float = 21.0) -> pd.DataFrame:
    """Hourly data from a known model, laid out like the identification runs."""
    rng = np.random.default_rng(seed)
    power = rng.choice([0.0, 2.0, 3.0, 4.0], size=hours)
    outdoor = 5 + 4 * np.sin(np.arange(hours) / 24 * 2 * np.pi)
    solar = np.clip(300 * np.sin(np.arange(hours) / 24 * 2 * np.pi), 0, None)
    temps = model.simulate(start_c, power, outdoor, solar)
    return pd.DataFrame({"zone_temp_c": temps, "power_kw": power, "outdoor_c": outdoor, "solar_w_m2": solar})


def test_simulate_without_heat_or_sun_cools_towards_outdoor():
    model = ThermalModel(loss_per_h=0.1, heat_k_per_kwh=0.2, solar_k_per_wh_m2=0.0, drift_k_per_h=0.0)

    temps = model.simulate(20.0, power_kw=[0, 0], outdoor_c=[10, 10], solar_w_m2=[0, 0])

    assert temps == pytest.approx([19.0, 18.1])


def test_simulate_heating_warms_the_room():
    model = ThermalModel(loss_per_h=0.0, heat_k_per_kwh=0.5, solar_k_per_wh_m2=0.0, drift_k_per_h=0.0)

    assert model.simulate(20.0, [2.0], [10.0], [0.0]) == pytest.approx([21.0])


def test_fit_recovers_a_known_model():
    model = fit([synthetic(TRUE)])

    assert model.loss_per_h == pytest.approx(TRUE.loss_per_h, abs=1e-6)
    assert model.heat_k_per_kwh == pytest.approx(TRUE.heat_k_per_kwh, abs=1e-6)
    assert model.solar_k_per_wh_m2 == pytest.approx(TRUE.solar_k_per_wh_m2, abs=1e-6)
    assert model.drift_k_per_h == pytest.approx(TRUE.drift_k_per_h, abs=1e-6)


def test_fit_does_not_link_the_end_of_one_run_to_the_start_of_the_next():
    # The second run starts much warmer, so a row joining the two runs would be a big outlier.
    first, second = synthetic(TRUE, seed=1), synthetic(TRUE, seed=2, start_c=30.0)

    model = fit([first, second])

    assert model.heat_k_per_kwh == pytest.approx(TRUE.heat_k_per_kwh, abs=1e-6)


def test_response_matrix_matches_simulate():
    """The optimizer uses T = free + G @ power. It must agree with simulate()."""
    rng = np.random.default_rng(3)
    power, outdoor, solar = rng.uniform(0, 4, 24), rng.uniform(-5, 10, 24), rng.uniform(0, 300, 24)

    free, gain = TRUE.response(21.0, outdoor, solar)

    assert free + gain @ power == pytest.approx(TRUE.simulate(21.0, power, outdoor, solar))
