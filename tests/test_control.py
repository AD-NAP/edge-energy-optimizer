from edge_energy_optimizer.control.base import Controller, Forecast, Observation
from edge_energy_optimizer.control.baseline import FixedSetpointController
from edge_energy_optimizer.control.predictive import PredictiveController

HOUR = 3600
NOW = Observation(time_s=0, zone_temp_c=21.5)
FLAT = [0.25] * 24
HOME, AWAY = [True] * 24, [False] * 24


def fake_forecast(
    prices: list[float], occupied: list[bool], start_s: int = 0, outdoor_c: float = 5.0
) -> Forecast:
    """An hourly forecast with the test case's comfort bands: 21 to 24 occupied, 15 to 30 empty."""
    return Forecast(
        time_s=[start_s + i * HOUR for i in range(len(prices))],
        lower_c=[21.0 if occ else 15.0 for occ in occupied],
        upper_c=[24.0 if occ else 30.0 for occ in occupied],
        price=prices,
        outdoor_c=[outdoor_c] * len(prices),
    )


def test_fixed_controller_is_a_controller():
    assert isinstance(FixedSetpointController(), Controller)


def test_fixed_controller_ignores_price_occupancy_and_temperature():
    controller = FixedSetpointController(setpoint_c=21.2)
    cheap_occupied = fake_forecast([0.10] * 4, [True] * 4)
    pricey_empty = fake_forecast([0.90] * 4, [False] * 4)

    cold = controller.setpoint_c(Observation(time_s=0, zone_temp_c=18.0), cheap_occupied)
    warm = controller.setpoint_c(Observation(time_s=0, zone_temp_c=25.0), pricey_empty)

    assert cold == warm == 21.2


def predictive(**overrides) -> PredictiveController:
    settings = {"margin_c": 0.2, "preheat_hours": 4, "boost_c": 1.0, "cheap_quantile": 0.25,
                "mild_outdoor_c": 10.0}
    return PredictiveController(**(settings | overrides))


def test_predictive_controller_is_a_controller():
    assert isinstance(predictive(), Controller)


def test_predictive_holds_the_lower_bound_when_home_at_a_normal_price():
    assert predictive().setpoint_c(NOW, fake_forecast(FLAT, HOME)) == 21.2


def test_predictive_sets_back_when_the_house_stays_empty():
    assert predictive().setpoint_c(NOW, fake_forecast(FLAT, AWAY)) == 15.2


def test_predictive_preheats_before_people_come_home():
    back_in_3_hours = [False] * 3 + [True] * 21

    assert predictive().setpoint_c(NOW, fake_forecast(FLAT, back_in_3_hours)) == 21.2


def test_predictive_does_not_preheat_too_early():
    back_in_6_hours = [False] * 6 + [True] * 18

    assert predictive().setpoint_c(NOW, fake_forecast(FLAT, back_in_6_hours)) == 15.2


def test_predictive_stores_heat_when_the_price_is_cheap_now():
    cheap_now = [0.10] + [0.30] * 23

    assert predictive().setpoint_c(NOW, fake_forecast(cheap_now, HOME)) == 22.2


def test_predictive_does_not_store_heat_when_the_price_is_expensive_now():
    pricey_now = [0.50] + [0.10] * 23

    assert predictive().setpoint_c(NOW, fake_forecast(pricey_now, HOME)) == 21.2


def test_predictive_never_goes_above_the_upper_bound():
    cheap_now = [0.10] + [0.30] * 23

    setpoint = predictive(boost_c=10.0).setpoint_c(NOW, fake_forecast(cheap_now, HOME))

    assert setpoint == 23.8


def test_predictive_handles_a_forecast_shorter_than_the_preheat_window():
    assert predictive().setpoint_c(NOW, fake_forecast([0.25, 0.25], [False, True])) == 21.2


def test_predictive_does_not_store_heat_on_a_mild_day():
    cheap_now = [0.10] + [0.30] * 23

    assert predictive().setpoint_c(NOW, fake_forecast(cheap_now, HOME, outdoor_c=15.0)) == 21.2


def test_predictive_still_preheats_on_a_mild_day():
    back_in_3_hours = [False] * 3 + [True] * 21

    assert predictive().setpoint_c(NOW, fake_forecast(FLAT, back_in_3_hours, outdoor_c=15.0)) == 21.2
