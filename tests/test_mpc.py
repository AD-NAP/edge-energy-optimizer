import pytest

from edge_energy_optimizer.control.base import Controller, Forecast, Observation
from edge_energy_optimizer.control.mpc import MPCController
from edge_energy_optimizer.control.thermal_model import ThermalModel

HOUR = 3600
# Roughly the fitted house, without sun or drift so the numbers are easy to reason about.
MODEL = ThermalModel(loss_per_h=0.02, heat_k_per_kwh=0.17, solar_k_per_wh_m2=0.0, drift_k_per_h=0.0)
FLAT = [0.25] * 25
HOME, AWAY = [True] * 25, [False] * 25


def fake_forecast(prices: list[float], occupied: list[bool], outdoor_c: float = 5.0) -> Forecast:
    """25 hourly points (now plus 24 hours), with the test case's comfort bands."""
    return Forecast(
        time_s=[i * HOUR for i in range(len(prices))],
        lower_c=[21.0 if occ else 15.0 for occ in occupied],
        upper_c=[24.0 if occ else 30.0 for occ in occupied],
        price=prices,
        outdoor_c=[outdoor_c] * len(prices),
        solar_w_m2=[0.0] * len(prices),
    )


def mpc() -> MPCController:
    return MPCController(model=MODEL)


def at(temp_c: float) -> Observation:
    return Observation(time_s=0, zone_temp_c=temp_c)


def test_mpc_is_a_controller():
    assert isinstance(mpc(), Controller)


def test_mpc_lets_an_empty_house_cool_when_nobody_is_coming_home():
    assert mpc().setpoint_c(at(21.5), fake_forecast(FLAT, AWAY)) < 21.5


def test_mpc_keeps_an_occupied_house_at_the_lower_bound_on_a_flat_price():
    assert mpc().setpoint_c(at(21.2), fake_forecast(FLAT, HOME)) == pytest.approx(21.2, abs=0.05)


def test_mpc_preheats_a_cold_house_before_people_come_home():
    back_in_3_hours = [False] * 4 + [True] * 21

    assert mpc().setpoint_c(at(18.0), fake_forecast(FLAT, back_in_3_hours)) > 18.3


def test_mpc_does_not_preheat_when_arrival_is_far_off():
    back_in_20_hours = [False] * 21 + [True] * 4

    assert mpc().setpoint_c(at(18.0), fake_forecast(FLAT, back_in_20_hours)) < 18.0


def test_mpc_stores_heat_when_it_is_cheap_now_and_dear_later():
    cheap_now = [0.10] * 3 + [0.40] * 22

    stored = mpc().setpoint_c(at(21.2), fake_forecast(cheap_now, HOME))

    assert stored > 21.4


def test_mpc_never_plans_above_the_upper_bound():
    cheap_now = [0.01] + [5.0] * 24

    assert mpc().setpoint_c(at(23.9), fake_forecast(cheap_now, HOME)) <= 23.8


def test_mpc_never_plans_below_the_empty_house_floor():
    assert mpc().setpoint_c(at(15.1), fake_forecast(FLAT, AWAY)) >= 15.2


def test_mpc_still_answers_when_comfort_cannot_be_reached():
    """A freezing room with people home cannot reach 21 C in an hour. The plan must
    still come back (via the slack), heating as hard as it can."""
    setpoint = mpc().setpoint_c(at(12.0), fake_forecast(FLAT, HOME, outdoor_c=-10.0))

    assert setpoint >= 21.2


def test_mpc_asks_for_the_floor_when_the_plan_says_off():
    """Asking for the expected temperature would make the thermostat chase the room upward
    whenever it runs warmer than the model thinks, such as on a sunny afternoon."""
    assert mpc().setpoint_c(at(25.0), fake_forecast(FLAT, AWAY)) == 15.2


def test_mpc_asks_for_the_planned_temperature_when_the_plan_heats():
    back_in_6_hours = [False] * 7 + [True] * 18

    controller = mpc()
    power, temps = controller.plan(at(18.0), fake_forecast(FLAT, back_in_6_hours))

    assert power[0] > 0
    assert controller.setpoint_c(at(18.0), fake_forecast(FLAT, back_in_6_hours)) == round(temps[0], 2)
