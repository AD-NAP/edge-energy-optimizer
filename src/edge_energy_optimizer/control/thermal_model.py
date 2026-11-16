"""A one-room thermal model of the test case house, fitted from the identification runs.

Each hour the room temperature changes by:

    loss * (outdoor - room)      heat leaks out, faster when it is colder outside
  + heat * power                 the heat pump's electric power warms it
  + solar * sunshine             sun through the windows warms it
  + drift                        everything else, such as heat lost to the ground

Four numbers, all fitted with ordinary least squares.
Run with: uv run python -m edge_energy_optimizer.control.thermal_model
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_PATH = Path("models/thermal_model.json")
HORIZON_H = 24


@dataclass(frozen=True)
class ThermalModel:
    loss_per_h: float
    heat_k_per_kwh: float
    solar_k_per_wh_m2: float
    drift_k_per_h: float

    def simulate(self, start_c: float, power_kw, outdoor_c, solar_w_m2) -> list[float]:
        """Room temperature at the end of each hour, starting from `start_c`."""
        temps, temp = [], start_c
        for power, outdoor, solar in zip(power_kw, outdoor_c, solar_w_m2):
            temp += (self.loss_per_h * (outdoor - temp) + self.heat_k_per_kwh * power
                     + self.solar_k_per_wh_m2 * solar + self.drift_k_per_h)
            temps.append(temp)
        return temps

    def response(self, start_c: float, outdoor_c, solar_w_m2) -> tuple[np.ndarray, np.ndarray]:
        """The model as `temps = free + gain @ power`, which is what a linear optimizer needs.

        `free` is the temperature path with the heat pump off. `gain[k, j]` is how much one kW
        in hour j raises the temperature at the end of hour k: it starts at `heat_k_per_kwh`
        and fades by `1 - loss_per_h` every hour after, as that heat leaks away.
        """
        hours = len(outdoor_c)
        free = np.array(self.simulate(start_c, np.zeros(hours), outdoor_c, solar_w_m2))
        k, j = np.indices((hours, hours))
        gain = np.where(k >= j, self.heat_k_per_kwh * (1 - self.loss_per_h) ** (k - j), 0.0)
        return free, gain


def fit(runs: list[pd.DataFrame]) -> ThermalModel:
    """Least squares on hourly rows. Each run is kept apart, so no row spans two runs."""
    features, changes = [], []
    for run in runs:
        temp = run["zone_temp_c"].to_numpy()
        before, after = temp[:-1], temp[1:]
        rest = run.iloc[1:]
        features.append(np.column_stack([
            rest["outdoor_c"] - before, rest["power_kw"], rest["solar_w_m2"], np.ones(len(rest)),
        ]))
        changes.append(after - before)
    params, *_ = np.linalg.lstsq(np.vstack(features), np.concatenate(changes), rcond=None)
    return ThermalModel(*(float(p) for p in params))


def multi_step_error(model: ThermalModel, run: pd.DataFrame, hours: int = HORIZON_H) -> tuple[float, float]:
    """Mean absolute error of 24-hour simulations started every hour, for the model and for
    the naive guess "the temperature stays where it is"."""
    temp = run["zone_temp_c"].to_numpy()
    model_errors, naive_errors = [], []
    for start in range(len(run) - hours):
        window = run.iloc[start + 1:start + 1 + hours]
        actual = window["zone_temp_c"].to_numpy()
        predicted = model.simulate(temp[start], window["power_kw"], window["outdoor_c"], window["solar_w_m2"])
        model_errors.append(np.abs(np.array(predicted) - actual).mean())
        naive_errors.append(np.abs(temp[start] - actual).mean())
    return float(np.mean(model_errors)), float(np.mean(naive_errors))


def save(model: ThermalModel, path: Path = MODEL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(model), indent=2))


def load(path: Path = MODEL_PATH) -> ThermalModel:
    return ThermalModel(**json.loads(path.read_text()))


def main() -> None:
    # Imported here because the runner imports the MPC, which imports this module.
    from edge_energy_optimizer.control.experiment import SERIES_DIR

    train = pd.read_csv(SERIES_DIR / "identification_train.csv")
    validate = pd.read_csv(SERIES_DIR / "identification_validate.csv")
    model = fit([train])
    save(model)
    print(model)
    print(f"Time constant: {1 / model.loss_per_h:.0f} hours")
    for name, run in (("train", train), ("validate", validate)):
        model_mae, naive_mae = multi_step_error(model, run)
        print(f"24-hour MAE on {name}: model {model_mae:.2f} K, temperature stays put {naive_mae:.2f} K")


if __name__ == "__main__":
    main()
