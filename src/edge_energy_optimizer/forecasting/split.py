"""Split the feature table into a training period and a test period.

Run with: uv run python -m edge_energy_optimizer.forecasting.split
"""

import pandas as pd

from edge_energy_optimizer.forecasting.dataset import build_dataset
from edge_energy_optimizer.forecasting.features import TARGET, build_features

# Train on 2016, test on 2017. A full test year covers every season and holiday.
TEST_START = "2017-01-01"


def split(table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (train, test), split by time and never shuffled."""
    return table.loc[table.index < TEST_START], table.loc[table.index >= TEST_START]


def main() -> None:
    train, test = split(build_features(build_dataset()))
    for name, part in [("train", train), ("test", test)]:
        print(f"{name:<5} {part.index.min()} to {part.index.max()}  {len(part)} rows")

    # The baselines are already columns in the table, so score them on the test year.
    for lag in ["load_lag_24h", "load_lag_168h"]:
        miss = (test[TARGET] - test[lag]).abs().mean()
        print(f"{lag:<14} average miss on test: {miss:.1f} kWh")


if __name__ == "__main__":
    main()
