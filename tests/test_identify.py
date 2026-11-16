import numpy as np

from edge_energy_optimizer.control.identify import excitation, run_identification

HOUR = 3600
DAY = 24 * HOUR


class FakeBoptest:
    """A zone at 21 C. Records every call so tests can check what was sent."""

    def __init__(self) -> None:
        self.time_s = 0
        self.sent: list[dict] = []
        self.initialized: dict | None = None
        self.stopped = False

    def select(self, testcase: str) -> None:
        pass

    def initialize(self, start_s: float, warmup_s: float) -> dict:
        self.initialized = {"start_s": start_s, "warmup_s": warmup_s}
        self.time_s = start_s
        return {"time": self.time_s, "reaTZon_y": 294.15}

    def advance(self, inputs: dict) -> dict:
        self.sent.append(inputs)
        self.time_s += HOUR
        return {"time": self.time_s, "reaTZon_y": 294.15}

    def results(self, point_names: list[str], start_s: float, final_s: float) -> dict:
        times = list(range(int(start_s), int(final_s) + 1, 900))
        values = {"reaTZon_y": 294.15, "weaSta_reaWeaTDryBul_y": 278.15, "weaSta_reaWeaHGloHor_y": 100.0}
        return {"time": times, **{name: [values.get(name, 1000.0)] * len(times) for name in point_names}}

    def stop(self) -> None:
        self.stopped = True


def test_excitation_stays_within_the_modulation_range():
    signal = excitation(hours=500, seed=1)

    assert len(signal) == 500
    assert min(signal) >= 0.0 and max(signal) <= 1.0


def test_excitation_holds_each_level_for_at_least_one_hour_and_varies():
    signal = excitation(hours=500, seed=1, max_hold_hours=6)

    changes = np.flatnonzero(np.diff(signal)) + 1
    holds = np.diff(np.r_[0, changes, len(signal)])
    assert holds.max() <= 6
    assert len(set(signal)) > 3


def test_excitation_is_reproducible():
    assert excitation(hours=50, seed=7) == excitation(hours=50, seed=7)


def test_run_identification_drives_the_heat_pump_directly_then_stops():
    client = FakeBoptest()

    data = run_identification(client, start_day=45, signal=[0.0, 0.5, 1.0])

    assert client.initialized["start_s"] == 45 * DAY
    assert client.sent == [
        {"oveHeaPumY_u": u, "oveHeaPumY_activate": 1} for u in (0.0, 0.5, 1.0)
    ]
    assert client.stopped
    assert list(data.columns) == ["zone_temp_c", "power_kw", "outdoor_c", "solar_w_m2"]
    assert len(data) == 3
    # Three power points of 1000 W each, summed and turned into kW.
    assert data["power_kw"].tolist() == [3.0, 3.0, 3.0]
    assert data["zone_temp_c"].iloc[0] == 21.0
