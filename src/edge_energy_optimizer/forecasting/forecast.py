"""Forecast the next day of load. This is the entry point other phases call.

Run with: uv run python -m edge_energy_optimizer.forecasting.forecast
"""

import pandas as pd

from edge_energy_optimizer.forecasting.dataset import build_dataset
from edge_energy_optimizer.forecasting.features import (
    FEATURES,
    TARGET,
    WEATHER_FEATURES,
    add_features,
)
from edge_energy_optimizer.forecasting.model import load_model

HORIZON_HOURS = 24


def forecast(history: pd.DataFrame, weather_forecast: pd.DataFrame, model=None) -> pd.Series:
    """Predict hourly load for the hours covered by `weather_forecast`.

    `history` holds the observed load and weather, hourly, ending at the
    current hour. It must reach back at least one week. `weather_forecast`
    holds the expected weather for up to the next 24 hours.
    """
    if len(weather_forecast) > HORIZON_HOURS:
        raise ValueError(f"Can forecast at most {HORIZON_HOURS} hours ahead")
    model = model or load_model()

    # Future hours have weather but no load yet, so their load stays NaN.
    frame = pd.concat([history[[TARGET] + WEATHER_FEATURES], weather_forecast[WEATHER_FEATURES]])
    features = add_features(frame).loc[weather_forecast.index, FEATURES]
    if features.isna().any().any():
        raise ValueError("History must cover the week before the forecast hours with no gaps")

    return pd.Series(model.predict(features), index=features.index, name="forecast_kwh")


def main() -> None:
    df = build_dataset()
    now = pd.Timestamp("2017-07-11 23:00")
    history = df.loc[:now]
    next_day = df.loc[now + pd.Timedelta(hours=1) : now + pd.Timedelta(hours=HORIZON_HOURS)]

    result = pd.DataFrame({
        "forecast": forecast(history, next_day[WEATHER_FEATURES]),
        "actual": next_day[TARGET],
    })
    print(result.round(1))
    print(f"MAE for this day: {(result['forecast'] - result['actual']).abs().mean():.1f} kWh")


if __name__ == "__main__":
    main()
