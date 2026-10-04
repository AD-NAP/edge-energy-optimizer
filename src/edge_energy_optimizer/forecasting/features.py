"""Turn the hourly time series into a table a model can learn from.

The forecast is made one day ahead, so every feature must be known 24 hours
before the hour being predicted.

Run with: uv run python -m edge_energy_optimizer.forecasting.features
"""

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from edge_energy_optimizer.forecasting.dataset import build_dataset

TARGET = "load_kwh"

CALENDAR_FEATURES = ["hour", "day_of_week", "day_of_year", "is_holiday"]
# Measured weather stands in for the weather forecast a live system would use.
WEATHER_FEATURES = ["air_temp_c", "dew_temp_c"]
LAG_FEATURES = ["load_lag_24h", "load_lag_168h"]
FEATURES = CALENDAR_FEATURES + WEATHER_FEATURES + LAG_FEATURES


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return every hour of `df` with the target and every feature.

    Hours whose load or lags are unknown keep NaN in those columns.
    """
    out = df[[TARGET] + WEATHER_FEATURES].copy()

    out["hour"] = out.index.hour
    out["day_of_week"] = out.index.dayofweek
    out["day_of_year"] = out.index.dayofyear
    holidays = USFederalHolidayCalendar().holidays(out.index.min(), out.index.max())
    out["is_holiday"] = out.index.normalize().isin(holidays).astype(int)

    out["load_lag_24h"] = out[TARGET].shift(24)
    out["load_lag_168h"] = out[TARGET].shift(168)

    return out[[TARGET] + FEATURES]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return one complete row per hour, ready for training or scoring."""
    # The first week has no value from a week earlier.
    return add_features(df).dropna()


def main() -> None:
    table = build_features(build_dataset())
    print(f"{len(table)} rows, {len(FEATURES)} features")
    with pd.option_context("display.width", 200):
        print(table.loc["2017-07-03 12:00":"2017-07-05 12:00":12].round(1))


if __name__ == "__main__":
    main()
