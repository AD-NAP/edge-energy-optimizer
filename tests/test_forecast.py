import numpy as np
import pandas as pd
import pytest

from edge_energy_optimizer.forecasting.features import FEATURES, TARGET, build_features
from edge_energy_optimizer.forecasting.forecast import forecast
from edge_energy_optimizer.forecasting.model import train_model


@pytest.fixture(scope="module")
def data() -> pd.DataFrame:
    """Six weeks of synthetic hourly load with a daily cycle."""
    index = pd.date_range("2017-01-02", periods=24 * 42, freq="h")
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        TARGET: 300 + 100 * np.sin(index.hour / 24 * 2 * np.pi) + rng.normal(0, 5, len(index)),
        "air_temp_c": 10 + rng.normal(0, 3, len(index)),
        "dew_temp_c": 5 + rng.normal(0, 3, len(index)),
    }, index=index)


@pytest.fixture(scope="module")
def model(data):
    return train_model(build_features(data))


def test_forecast_covers_the_next_day(data, model):
    history, next_day = data.iloc[:-24], data.iloc[-24:]

    result = forecast(history, next_day[["air_temp_c", "dew_temp_c"]], model)

    assert result.index.equals(next_day.index)
    assert result.notna().all()


def test_forecast_matches_the_features_used_in_training(data, model):
    history, next_day = data.iloc[:-24], data.iloc[-24:]

    result = forecast(history, next_day[["air_temp_c", "dew_temp_c"]], model)

    expected = model.predict(build_features(data).loc[next_day.index, FEATURES])
    np.testing.assert_allclose(result.to_numpy(), expected)


def test_forecast_rejects_short_history(data, model):
    history, next_day = data.iloc[-72:-24], data.iloc[-24:]

    with pytest.raises(ValueError, match="History"):
        forecast(history, next_day[["air_temp_c", "dew_temp_c"]], model)


def test_forecast_rejects_horizons_beyond_a_day(data, model):
    history, future = data.iloc[:-48], data.iloc[-48:]

    with pytest.raises(ValueError, match="at most"):
        forecast(history, future[["air_temp_c", "dew_temp_c"]], model)
