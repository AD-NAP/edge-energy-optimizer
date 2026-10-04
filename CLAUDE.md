# edge-energy-optimizer

Building energy optimization in 5 phases. Phase 1 (load forecasting) is done, phase 2 (control against BOPTEST) is next. Phases 1 and 2 are due Sunday 11 October 2026.

## Where things are
- Vision and phases: `docs/architecture.md`. Choices made so far: `docs/decisions/`.
- Commands for every pipeline step, and the phase 1 results and known limits: `README.md`.
- Other phases get a forecast through `forecast()` in `src/edge_energy_optimizer/forecasting/forecast.py`.
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
Claude builds in small steps. Before moving on, explain the one new concept with an analogy and ask a few quick check questions. Learning notes go in the vault (`../../vault/learning/`), not in this repo.

## Phase 2 watch-outs
- The forecaster is trained on a real building, not the BOPTEST one. Retrain the same pipeline on BOPTEST data if the controller needs a load forecast.
- Still open: which BOPTEST test case, and rule-based control or MPC.
