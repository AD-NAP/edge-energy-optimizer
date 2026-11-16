import pytest

from edge_energy_optimizer.control.baseline import FixedSetpointController
from edge_energy_optimizer.control.experiment import run_episode, to_forecast, to_inputs

HOUR = 3600


class FakeBoptest:
    """Stands in for the emulator: a zone that sits at 21 C and draws 1 kW."""

    def __init__(self) -> None:
        self.time_s = 0
        self.sent: list[dict] = []
        self.stopped = False

    def select(self, testcase: str) -> None:
        pass

    def set_scenario(self, time_period: str, electricity_price: str) -> dict:
        return {"time": self.time_s, "reaTZon_y": 294.15}

    def set_price(self, electricity_price: str) -> None:
        self.price = electricity_price

    def initialize(self, start_s: float, warmup_s: float) -> dict:
        self.initialized = start_s
        self.time_s = start_s
        return {"time": self.time_s, "reaTZon_y": 294.15}

    def forecast(self, point_names: list[str], horizon_s: float, interval_s: float) -> dict:
        self.forecast_starts = getattr(self, "forecast_starts", []) + [self.time_s]
        times = [self.time_s + i * HOUR for i in range(int(horizon_s / interval_s) + 1)]
        values = {"TDryBul": 278.15, "LowerSetp[1]": 294.15, "UpperSetp[1]": 297.15}
        payload = {name: [values.get(name, 0.25)] * len(times) for name in point_names}
        return {"time": times, **payload}

    def advance(self, inputs: dict) -> dict:
        self.sent.append(inputs)
        self.time_s += HOUR
        return {"time": self.time_s, "reaTZon_y": 294.15}

    def results(self, point_names: list[str], start_s: float, final_s: float) -> dict:
        times = list(range(int(start_s), int(final_s) + 1, 900))
        values = {"reaTZon_y": 294.15}
        return {"time": times, **{name: [values.get(name, 1000.0)] * len(times) for name in point_names}}

    def kpis(self) -> dict:
        return {"cost_tot": 1.0, "ener_tot": 4.0, "tdis_tot": 0.0}

    def stop(self) -> None:
        self.stopped = True


def test_to_inputs_sends_kelvin_and_activates_the_override():
    assert to_inputs(21.2) == {"oveTSet_u": 294.35, "oveTSet_activate": 1}


def test_to_forecast_converts_to_celsius_and_picks_the_scenario_price():
    payload = {
        "time": [0, 3600],
        "TDryBul": [273.15, 274.15],
        "LowerSetp[1]": [294.15, 288.15],
        "UpperSetp[1]": [297.15, 303.15],
        "PriceElectricPowerHighlyDynamic": [0.21, 0.32],
    }

    forecast = to_forecast(payload, "highly_dynamic")

    assert forecast.lower_c == pytest.approx([21.0, 15.0])
    assert forecast.upper_c == pytest.approx([24.0, 30.0])
    assert forecast.outdoor_c == pytest.approx([0.0, 1.0])
    assert forecast.price == [0.21, 0.32]


def test_to_forecast_passes_the_sunshine_through_when_asked_for():
    payload = {
        "time": [0], "TDryBul": [273.15], "HGloHor": [150.0], "LowerSetp[1]": [294.15],
        "UpperSetp[1]": [297.15], "PriceElectricPowerDynamic": [0.2],
    }

    assert to_forecast(payload, "dynamic").solar_w_m2 == [150.0]


def test_run_episode_sends_the_controller_setpoint_every_step_then_stops():
    client = FakeBoptest()

    kpis, series = run_episode(client, FixedSetpointController(21.2), "peak_heat_day", "dynamic", steps=5)

    assert client.sent == [{"oveTSet_u": 294.35, "oveTSet_activate": 1}] * 5
    assert client.stopped
    assert kpis["cost_tot"] == 1.0
    assert series["zone_temp_c"].iloc[0] == pytest.approx(21.0)
    assert series["setpoint_c"].iloc[-1] == pytest.approx(21.2)
    assert series["power_kw"].iloc[0] == pytest.approx(3.0)


def test_run_episode_can_start_on_any_day_with_the_scenario_price():
    client = FakeBoptest()

    run_episode(client, FixedSetpointController(21.2), "unseen", "dynamic", steps=2, start_day=64)

    assert client.initialized == 64 * 86400
    assert client.price == "dynamic"
    assert client.forecast_starts[0] == 64 * 86400
