"""Build the hourly dataset for one building: its load plus the local weather.

Run with: uv run python -m edge_energy_optimizer.forecasting.dataset
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Chosen for clean data (no missing or zero hours), clear daily and weekly
# cycles, and a strong link between load and outdoor temperature.
BUILDING_ID = "Hog_office_Shawnna"

WEATHER_COLUMNS = {
    "airTemperature": "air_temp_c",
    "dewTemperature": "dew_temp_c",
}


def build_dataset(building_id: str = BUILDING_ID) -> pd.DataFrame:
    """Return one row per hour with the building's load and weather.

    Timestamps are in the building's local time.
    """
    load = pd.read_csv(
        RAW_DIR / "electricity_cleaned.csv",
        usecols=["timestamp", building_id],
        parse_dates=["timestamp"],
        index_col="timestamp",
    )[building_id].rename("load_kwh")

    site_id = building_id.split("_")[0]
    weather = pd.read_csv(RAW_DIR / "weather.csv", parse_dates=["timestamp"])
    weather = (
        weather[weather["site_id"] == site_id]
        .set_index("timestamp")[list(WEATHER_COLUMNS)]
        .rename(columns=WEATHER_COLUMNS)
    )
    # The weather station misses a few hours. Fill them from the neighbours.
    weather = weather.reindex(load.index).interpolate(limit_direction="both")

    return pd.concat([load, weather], axis=1)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_dataset()
    target = PROCESSED_DIR / f"{BUILDING_ID}.csv"
    df.to_csv(target)
    print(f"Wrote {len(df)} rows to {target}")
    print(df.describe().round(1))


if __name__ == "__main__":
    main()
