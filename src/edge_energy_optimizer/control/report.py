"""Chart the saved experiment results: temperature, power against price, and KPIs.

Run the experiment first, then: uv run python -m edge_energy_optimizer.control.report
"""

import matplotlib.pyplot as plt
import pandas as pd

from edge_energy_optimizer.control.experiment import KPI_PATH, SERIES_DIR, TIME_PERIODS
from edge_energy_optimizer.forecasting.dataset import ROOT
from edge_energy_optimizer.forecasting.explore import BLUE, GRID, INK, MUTED, ORANGE, SURFACE, style

IMG_DIR = ROOT / "docs" / "img"
COLORS = {"baseline": ORANGE, "predictive": BLUE}
LABELS = {"baseline": "Baseline (fixed 21.2 °C)", "predictive": "Predictive"}
PERIOD_NAMES = {"peak_heat_day": "peak heating period", "typical_heat_day": "typical heating period"}
# The time charts use the spot price scenario, where the price moves the most.
PRICE = "highly_dynamic"
# Days shown in the time charts, counted from the start of the two weeks.
WINDOW_DAYS = (6, 10)
DAY_S = 86400


def load_window(controller: str, time_period: str) -> pd.DataFrame:
    """A few days from the middle of one run, indexed by day of the year."""
    series = pd.read_csv(SERIES_DIR / f"{controller}_{time_period}_{PRICE}.csv")
    start_s = series["time_s"].iloc[0]
    first, last = (start_s + day * DAY_S for day in WINDOW_DAYS)
    window = series[(series["time_s"] >= first) & (series["time_s"] <= last)]
    return window.set_index(window["time_s"] / DAY_S)


def plot_temperature(time_period: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    runs = {name: load_window(name, time_period) for name in COLORS}
    bounds = runs["baseline"]
    ax.fill_between(bounds.index, bounds["lower_c"], bounds["upper_c"], step="post",
                    color=GRID, linewidth=0, label="Comfort band")
    for name, run in runs.items():
        ax.plot(run.index, run["zone_temp_c"], color=COLORS[name], linewidth=2, label=LABELS[name])
    ax.set_ylim(17, 28)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, ncols=3, loc="upper right")
    style(ax, f"Zone temperature against the comfort band, {PERIOD_NAMES[time_period]}",
          "Day of the year", "°C")
    save(fig, f"phase2_temperature_{time_period}.png")


def plot_power(time_period: str) -> None:
    """Power and price are different units, so they get one panel each on a shared time axis."""
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9, 5.5), facecolor=SURFACE, sharex=True,
                                      height_ratios=[2, 1])
    runs = {name: load_window(name, time_period) for name in COLORS}
    for name, run in runs.items():
        # Hourly averages, because the raw 15-minute power is too spiky to compare by eye.
        hourly = run["power_kw"].groupby((run.index * 24).astype(int) / 24).mean()
        top.step(hourly.index, hourly, where="post", color=COLORS[name], linewidth=2, label=LABELS[name])
    top.legend(frameon=False, fontsize=9, labelcolor=INK, ncols=2, loc="upper right")
    top.set_ylim(top=top.get_ylim()[1] * 1.2)
    style(top, f"Heating power against the electricity price, {PERIOD_NAMES[time_period]}", "", "kW")

    price = runs["baseline"]["price"]
    bottom.step(price.index, price, where="post", color=INK, linewidth=1.5)
    style(bottom, "", "Day of the year", "EUR per kWh")
    for ax in (top, bottom):
        ax.set_facecolor(SURFACE)
    save(fig, f"phase2_power_{time_period}.png")


def plot_kpis() -> None:
    kpis = pd.read_csv(KPI_PATH)
    scenarios = kpis[["time_period", "electricity_price"]].drop_duplicates()
    names = [
        f"{'Peak' if period == 'peak_heat_day' else 'Typical'}\n{price.replace('_', ' ')}"
        for period, price in scenarios.itertuples(index=False)
    ]
    panels = {
        "cost_eur": "Cost (EUR)",
        "energy_kwh": "Energy (kWh)",
        "discomfort_kh": "Thermal discomfort (Kh)",
    }
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), facecolor=SURFACE)
    for ax, (column, title) in zip(axes, panels.items()):
        ax.set_facecolor(SURFACE)
        for offset, name in zip((-0.2, 0.2), COLORS):
            values = kpis.loc[kpis["controller"] == name, column].to_numpy()
            bars = ax.bar([x + offset for x in range(len(values))], values, width=0.36,
                          color=COLORS[name], label=LABELS[name])
            ax.bar_label(bars, fmt="%.0f" if values.max() >= 20 else "%.1f", fontsize=7,
                         color=MUTED, padding=2)
        ax.set_xticks(range(len(names)), names)
        ax.set_ylim(top=ax.get_ylim()[1] * 1.15)
        style(ax, title, "", "")
        ax.grid(axis="x", visible=False)
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper right")
    fig.suptitle("Two weeks per scenario, lower is better", x=0.01, ha="left", fontsize=10, color=MUTED)
    save(fig, "phase2_kpis.png")


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(IMG_DIR / name, dpi=130, facecolor=SURFACE)
    plt.close(fig)
    print(f"Wrote {IMG_DIR / name}")


def main() -> None:
    for time_period in TIME_PERIODS:
        plot_temperature(time_period)
        plot_power(time_period)
    plot_kpis()


if __name__ == "__main__":
    main()
