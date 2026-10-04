"""Download the Building Data Genome Project 2 files used for load forecasting.

Run with: uv run python scripts/download_data.py
"""

import hashlib
import urllib.request
from pathlib import Path

BASE_URL = "https://media.githubusercontent.com/media/buds-lab/building-data-genome-project-2/master/data"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# Repo path -> expected SHA-256, taken from the repo's Git LFS pointers.
FILES = {
    "meters/cleaned/electricity_cleaned.csv": "b6ffc9b4dfcefe5c753594730a08ae822b0d50fec6815abb8f185591e6c630a3",
    "weather/weather.csv": "a8189f1c6acdf3b9933a9e6354b8e7c1278cd56a7075929623a17565d44f04bd",
    "metadata/metadata.csv": "992d0b29f24f96ad4332bc4dbb534b7bdd7dd2689aad093f94e93068ecddca02",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for repo_path, expected in FILES.items():
        target = RAW_DIR / Path(repo_path).name
        if target.exists() and sha256(target) == expected:
            print(f"ok       {target.name}")
            continue
        print(f"fetching {target.name}")
        urllib.request.urlretrieve(f"{BASE_URL}/{repo_path}", target)
        if sha256(target) != expected:
            target.unlink()
            raise RuntimeError(f"Checksum mismatch for {target.name}")
    print(f"Done. Files are in {RAW_DIR}")


if __name__ == "__main__":
    main()
