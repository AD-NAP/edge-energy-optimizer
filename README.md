# edge-energy-optimizer

Forecast a building's energy load, use the forecast to control the building, and cut its peak demand, all running on a small edge cluster.

## Purpose

Buildings pay for electricity in two ways: the total energy they use (kWh) and the highest power they draw at any moment (peak demand, kW). The peak charge can be a large share of the bill, so flattening peaks saves real money without making anyone uncomfortable.

This project builds the full chain needed to do that:

1. Predict how much power the building will need over the next hours.
2. Decide what the heating, cooling, and battery should do about it.
3. Talk to building equipment using the protocols real equipment speaks.
4. Run the whole thing on edge hardware, close to the building, not in the cloud.

Everything runs against simulators, so you need no physical building, meter, or battery to work on it.

## Status

Scaffold only. No application code yet. Phase 1 is next.

## Setup

You need:

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which manages both the Python version and the dependencies
- [Docker](https://docs.docker.com/get-docker/), needed from phase 2 onward to run the BOPTEST building simulator

Then:

```bash
git clone <repo-url>
cd edge-energy-optimizer
uv sync
```

`uv sync` reads `pyproject.toml`, installs the Python version pinned in `.python-version`, and creates a virtual environment in `.venv/`. You do not need to activate it. Prefix commands with `uv run` instead:

```bash
uv run python --version
```

### Working with dependencies

| Task | Command |
| --- | --- |
| Add a runtime dependency | `uv add <package>` |
| Add a dev-only dependency | `uv add --dev <package>` |
| Remove a dependency | `uv remove <package>` |
| Sync after pulling changes | `uv sync` |

Always commit `pyproject.toml` and `uv.lock` together. Never edit `uv.lock` by hand and never use `pip install` in this repo.

## Phase roadmap

| Phase | What gets built | Target |
| --- | --- | --- |
| 1 | Energy load forecasting (ML) | Sunday 11 October 2026 |
| 2 | Control logic tested against a simulated building (BOPTEST) | Sunday 11 October 2026 |
| 3 | BACnet and Modbus protocol integration | TBD |
| 4 | Peak demand shaving with a simulated battery | TBD |
| 5 | Edge deployment on k3s with MQTT and a dashboard | TBD |

Each phase builds on the one before it and should leave the repo in a working, demonstrable state. See [docs/architecture.md](docs/architecture.md) for how the phases fit together.

## Repository layout

```
edge-energy-optimizer/
├── docs/
│   ├── architecture.md   # the 5-phase vision and how the parts connect
│   └── decisions/        # architecture decision records (ADRs)
├── pyproject.toml        # project metadata and dependencies
├── .python-version       # Python version uv installs
└── README.md
```

Source and test folders are added when phase 1 starts.

## Glossary

- **Load forecasting**: predicting future power demand from history, weather, and calendar features.
- **BOPTEST**: an open source framework that runs a physics-based building model in Docker and exposes it over a REST API, so control strategies can be tested and scored fairly.
- **BACnet**: the standard protocol for building automation equipment such as HVAC controllers.
- **Modbus**: a simple, older protocol common on meters, inverters, and batteries.
- **Peak shaving**: discharging a battery (or reducing load) when demand is high so the grid sees a flatter profile.
- **k3s**: a lightweight Kubernetes distribution made for edge devices.
- **MQTT**: a lightweight publish/subscribe messaging protocol common in IoT.

## Contributing

- Read [docs/architecture.md](docs/architecture.md) before your first change.
- Work on a branch and open a pull request. Keep each one small and focused on a single phase.
- When you make a choice that would be hard to reverse (a library, a protocol, a data format), record it as a new file in [docs/decisions/](docs/decisions/), following the format of the existing ones.
