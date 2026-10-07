# Phase 2 learning handoff

Written on 5 October 2026 so a new Claude session, on any device, can continue the phase 2 teaching. Delete this file when the learning is finished.

## For the new session

- Work on the `phase-2` branch.
- All required phase 2 code and docs are done. What is left is teaching, the vault notes, and an optional MPC controller.
- Follow the working mode in `CLAUDE.md`: one concept at a time, an analogy first, then 1 to 5 check questions, and wait for the answers before moving on.
- BOPTEST only runs on the home PC (it needs Docker and the gitignored `external/` checkout). Do not try to rerun experiments elsewhere. Teach from the code, `docs/results/phase2.md`, `docs/results/phase2_kpis.csv`, and the charts in `docs/img/`.
- `data/phase2/` (the 15-minute time series) is gitignored and only exists on the home PC.

## Concepts already taught

| # | Concept | Analogy used | What needed correcting |
| --- | --- | --- | --- |
| 1 | The emulator is turn-based: `advance` moves time, `forecast` looks ahead, `kpi` scores | Chess server | Nothing |
| 2 | An interface (`Protocol`) keeps controllers independent of BOPTEST | Wall socket | A new controller goes in its own file, and only the runner's list changes. Controllers return Celsius so BOPTEST names stay in the runner |
| 3 | Look-ahead heuristic versus MPC, and receding horizon | Rules of thumb versus a GPS, then walking with a flashlight | `preheat_hours` is a fixed setting. Preheating starts when the occupied hour slides into the window, not because anything was re-estimated |
| 4 | Tuning on your own exam (over-tuning) | Retaking the same marked paper | Ten precise thresholds are worse because of how many knobs there are and how precise they are. Custom start dates give an unseen test only if nothing is tuned on them |
| 5 | Test-driven development | Skewer test before baking | Watching a test fail also catches a wrong test, not only code that already exists |
| 6 | Fakes and dependency injection | Crash test dummy | `sent` records what was sent, not when. A missing `stop()` is caught by the test's `assert client.stopped`, because tests only ever use the fake |
| 7 | Reading the KPIs and charts | Final score versus match replay | The predictive controller is fixed rules, not a learned model with training data. The price rule shifts when heat is bought, not how much. Peak power: the learner ran out of time, so the answer was given (reheating after 0 kW stretches) |
| 8 | Attribution by ablation | Muting one instrument on a mixing desk | Muting setback keeps the house warm all day, it does not mean heating only when cheap. Did not know what a day/night tariff is, so it was explained. Shares depend on removal order (interaction). A timer thermostat is the tougher baseline |

Smaller ideas covered without their own questions: "occupied" means people at home (the building is a house, so it is empty on weekday daytimes), setback, thermal discomfort in kelvin-hours, and why a flat price must never trigger the boost.

## Start here

Concepts 1 to 8 are taught and their notes are in the vault (`learning/`). The only concept left is MPC in more depth, and only if the learner decides to build the MPC controller. Ask that first.

## Concepts still to teach, in this order

1. **MPC in more depth** (thermal model, optimizer). Only needed if the MPC controller gets built.

## Work left

| Item | Where | Notes |
| --- | --- | --- |
| Learning notes for each concept | The vault repo, `learning/`, one file per concept, from `templates/learning.md` | Write each one after its questions are answered, so it reflects what was actually understood |
| MPC controller | `src/edge_energy_optimizer/control/` | Optional. Needs BOPTEST, so home PC only. Phases 1 and 2 are due 11 October 2026 |
| Merge `phase-2` into `main` | GitHub | When the learner asks |
