# edge-energy-optimizer

Building energy optimization in 5 phases. See `docs/architecture.md`.

- Use uv for everything: `uv sync`, `uv add <pkg>`, `uv run <cmd>`. Never `pip install`.
- Tests: `uv run pytest`. They use synthetic data and need no download.
- Record hard-to-reverse choices as a new numbered file in `docs/decisions/`.
- All external systems (building, devices, battery) are simulated. Do not assume real hardware.
