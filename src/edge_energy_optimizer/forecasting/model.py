"""Train the load forecasting model.

Run with: uv run python -m edge_energy_optimizer.forecasting.model
"""

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from edge_energy_optimizer.forecasting.dataset import ROOT, build_dataset
from edge_energy_optimizer.forecasting.features import FEATURES, TARGET, build_features
from edge_energy_optimizer.forecasting.split import split

MODEL_PATH = ROOT / "models" / "load_forecaster.joblib"


def train_model(train: pd.DataFrame) -> HistGradientBoostingRegressor:
    """Fit gradient boosted trees on the training period."""
    model = HistGradientBoostingRegressor(random_state=0)
    model.fit(train[FEATURES], train[TARGET])
    return model


def load_model() -> HistGradientBoostingRegressor:
    """Load the model saved by running this module."""
    return joblib.load(MODEL_PATH)


def main() -> None:
    train, test = split(build_features(build_dataset()))
    model = train_model(train)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Trained {model.n_iter_} trees on {len(train)} rows, saved to {MODEL_PATH}")

    # A few noon hours the model has never seen, including the 4 July holiday.
    sample = test.loc[["2017-06-27 12:00", "2017-07-04 12:00", "2017-07-05 12:00"]]
    result = pd.DataFrame({
        "actual": sample[TARGET],
        "model": model.predict(sample[FEATURES]),
        "last_week_baseline": sample["load_lag_168h"],
    })
    print(result.round(1))


if __name__ == "__main__":
    main()
