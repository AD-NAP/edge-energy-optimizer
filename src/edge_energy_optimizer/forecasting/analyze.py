"""Find where the model is still wrong and which features it relies on.

Run with: uv run python -m edge_energy_optimizer.forecasting.analyze
"""

import pandas as pd
from sklearn.inspection import permutation_importance

from edge_energy_optimizer.forecasting.dataset import build_dataset
from edge_energy_optimizer.forecasting.features import FEATURES, TARGET, build_features
from edge_energy_optimizer.forecasting.model import train_model
from edge_energy_optimizer.forecasting.split import split


def error_table(error: pd.Series, groups) -> pd.DataFrame:
    """Bias (mean error) and MAE of the model for each group of hours."""
    grouped = error.groupby(groups)
    return pd.DataFrame({
        "hours": grouped.size(),
        "bias": grouped.mean(),
        "mae": grouped.apply(lambda e: e.abs().mean()),
    }).round(1)


def main() -> None:
    train, test = split(build_features(build_dataset()))
    model = train_model(train)

    # Positive error means the model guessed too high.
    error = pd.Series(model.predict(test[FEATURES]), index=test.index) - test[TARGET]
    print(f"Overall bias {error.mean():+.1f} kWh, MAE {error.abs().mean():.1f} kWh")
    print(f"Average load: train {train[TARGET].mean():.1f}, test {test[TARGET].mean():.1f}")

    print("\nBy month")
    print(error_table(error, test.index.month))
    print("\nBy day type")
    day_type = pd.Series("weekday", index=test.index)
    day_type[test.index.dayofweek >= 5] = "weekend"
    day_type[test["is_holiday"] == 1] = "holiday"
    print(error_table(error, day_type))

    print("\nFeature importance (rise in MAE when the feature is scrambled)")
    result = permutation_importance(
        model, test[FEATURES], test[TARGET],
        scoring="neg_mean_absolute_error", n_repeats=5, random_state=0,
    )
    importance = pd.Series(result.importances_mean, index=FEATURES)
    print(importance.sort_values(ascending=False).round(1))


if __name__ == "__main__":
    main()
