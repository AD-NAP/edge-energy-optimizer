"""Score the model against the naive baselines on the test year.

Run with: uv run python -m edge_energy_optimizer.forecasting.evaluate
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from edge_energy_optimizer.forecasting.dataset import ROOT, build_dataset
from edge_energy_optimizer.forecasting.explore import BLUE, INK, ORANGE, SURFACE, style
from edge_energy_optimizer.forecasting.features import FEATURES, TARGET, build_features
from edge_energy_optimizer.forecasting.model import train_model
from edge_energy_optimizer.forecasting.split import split

FIGURE_PATH = ROOT / "docs" / "img" / "forecast_week.png"


def mae(actual: pd.Series, predicted) -> float:
    """Mean absolute error: the average size of the miss, in kWh."""
    return float((actual - predicted).abs().mean())


def main() -> None:
    train, test = split(build_features(build_dataset()))
    model = train_model(train)

    scores = {
        "same hour yesterday": mae(test[TARGET], test["load_lag_24h"]),
        "same hour last week": mae(test[TARGET], test["load_lag_168h"]),
        "model": mae(test[TARGET], model.predict(test[FEATURES])),
    }
    best_baseline = min(scores["same hour yesterday"], scores["same hour last week"])

    print(f"Test year, average load {test[TARGET].mean():.1f} kWh per hour")
    for name, score in scores.items():
        print(f"{name:<20} MAE {score:5.1f} kWh  ({score / test[TARGET].mean():.1%} of average load)")
    print(f"Model improves on the best baseline by {1 - scores['model'] / best_baseline:.1%}")

    # A large gap between these two would mean the model memorised the training year.
    train_mae = mae(train[TARGET], model.predict(train[FEATURES]))
    print(f"Model MAE on its own training year: {train_mae:.1f} kWh")

    plot_week(test, model)


def plot_week(test: pd.DataFrame, model) -> None:
    """Plot one test week, holiday included, as actual, model, and baseline."""
    week = test.loc["2017-07-03":"2017-07-09"]
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot(week.index, week["load_lag_168h"], color=ORANGE, linewidth=1.5, label="Same hour last week")
    ax.plot(week.index, model.predict(week[FEATURES]), color=BLUE, linewidth=2, label="Model")
    ax.plot(week.index, week[TARGET], color=INK, linewidth=1.5, label="Actual")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, ncols=3, loc="upper right")
    ax.set_ylim(top=week[TARGET].max() * 1.2)
    style(ax, "Day-ahead forecast for a test week with a holiday (Tue 4 Jul 2017)", "", "kWh per hour")
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=130, facecolor=SURFACE)
    print(f"Wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
