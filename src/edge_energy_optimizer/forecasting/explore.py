"""Plot the patterns in the building's load that the forecaster will rely on.

Run with: uv run python -m edge_energy_optimizer.forecasting.explore
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from edge_energy_optimizer.forecasting.dataset import BUILDING_ID, ROOT, build_dataset

FIGURE_PATH = ROOT / "docs" / "img" / "load_overview.png"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e6e5e1"
BLUE = "#2a78d6"
ORANGE = "#eb6834"


def style(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main() -> None:
    df = build_dataset()
    fig, axes = plt.subplots(3, 1, figsize=(9, 10), facecolor=SURFACE)
    for ax in axes:
        ax.set_facecolor(SURFACE)

    # 1. Two weeks of raw hourly load: the daily and weekly cycles.
    window = df.loc["2017-05-01":"2017-05-14", "load_kwh"]
    axes[0].plot(window.index, window, color=BLUE, linewidth=1.5)
    axes[0].xaxis.set_major_locator(mdates.DayLocator(interval=2))
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    style(axes[0], "Two weeks of hourly load (1 to 14 May 2017)", "", "kWh per hour")

    # 2. Average day shape, weekdays against weekends.
    is_weekend = df.index.dayofweek >= 5
    for mask, label, color in [(~is_weekend, "Weekday", BLUE), (is_weekend, "Weekend", ORANGE)]:
        profile = df.loc[mask, "load_kwh"].groupby(df.index[mask].hour).mean()
        axes[1].plot(profile.index, profile, color=color, linewidth=2, label=label)
    axes[1].set_xticks(range(0, 24, 3))
    axes[1].legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper left")
    style(axes[1], "Average load by hour of day", "Hour of day (local time)", "kWh per hour")

    # 3. Daily load against daily temperature: the weather driver.
    daily = df.resample("D").mean()
    axes[2].scatter(daily["air_temp_c"], daily["load_kwh"], s=14, color=BLUE,
                    alpha=0.6, edgecolors=SURFACE, linewidths=0.5)
    style(axes[2], "Daily average load against outdoor temperature",
          "Daily average air temperature (°C)", "kWh per hour")

    fig.suptitle(f"{BUILDING_ID}: load patterns, 2016 to 2017", x=0.07, ha="left",
                 fontsize=13, color=INK)
    fig.tight_layout(rect=(0, 0, 0.97, 0.98))
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=130, facecolor=SURFACE)
    print(f"Wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
