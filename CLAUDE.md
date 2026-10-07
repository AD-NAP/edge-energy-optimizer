# edge-energy-optimizer

Building energy optimization in 5 phases. Phases 1 (load forecasting) and 2 (control against BOPTEST) are done, phase 3 (BACnet and Modbus) is next. Phases 1 and 2 are due Sunday 11 October 2026.

## Where things are
- Vision and phases: `docs/architecture.md`. Choices made so far: `docs/decisions/`.
- Commands for every pipeline step, and the phase 1 results and known limits: `README.md`.
- Other phases get a forecast through `forecast()` in `src/edge_energy_optimizer/forecasting/forecast.py`.
- Controllers implement `setpoint_c(observation, forecast)` from `src/edge_energy_optimizer/control/base.py`. Phase 2 results: `docs/results/phase2.md`.
- BOPTEST lives in `external/boptest` (gitignored) and must be started with `docker/boptest.override.yml`. Commands are in the README.
- `data/` and `models/` are gitignored. Recreate them with `scripts/download_data.py` (195 MB) and the `forecasting.model` module.

## Conventions
- Use uv for everything: `uv sync`, `uv add <pkg>`, `uv run <cmd>`. Never `pip install`.
- Each step is a module with a `main()`, run as `uv run python -m edge_energy_optimizer.<phase>.<step>`.
- Tests: `uv run pytest`. They use synthetic data and must not need the download.
- Report every result next to a baseline. Charts go in `docs/img/`.
- Record hard-to-reverse choices as a new numbered file in `docs/decisions/`.
- All external systems (building, devices, battery) are simulated. Do not assume real hardware.
- One branch per phase. Commit only when asked.

## Working mode
Claude builds in small steps. Before moving on, explain the one new concept with an analogy and ask a few quick check questions. Learning notes go in the vault (`../../vault/learning/<topic>/`), not in this repo.

## Watch-outs
- The forecaster is trained on a real building, not the BOPTEST one, and phase 2 does not use it. Retrain the same pipeline on BOPTEST data when a later phase needs a load forecast.
- The predictive controller's settings were tuned on the scenarios it is reported on. Rerun the experiment and say so when changing them.
- Still open: whether to add an MPC controller.
