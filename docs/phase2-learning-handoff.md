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
| 4 | Tuning on your own exam (over-tuning) | Retaking the same marked paper | Explained, questions not answered yet |

Smaller ideas covered without their own questions: "occupied" means people at home (the building is a house, so it is empty on weekday daytimes), setback, thermal discomfort in kelvin-hours, and why a flat price must never trigger the boost.

## Start here: open questions for concept 4

1. Why is the improvement from the mild-day rule less trustworthy than the phase 1 forecast score?
2. Which is the bigger warning sign of over-tuning: one rule with a round threshold, or ten rules with thresholds like 9.73?
3. The controller could be run from a custom start date through `PUT /initialize`, outside the two official periods. How would that help?

Background for checking the answers: the 10 °C mild-day threshold was picked after seeing which days overheated in the first run, and the results are reported on those same scenarios. Phase 1 trained on 2016 and scored on 2017.

## Concepts still to teach, in this order

1. **Test-driven development.** It was done three times (tests failed, then passed) but never taught. Use `tests/test_control.py` and `src/edge_energy_optimizer/control/predictive.py`.
2. **Fakes.** `FakeBoptest` in `tests/test_experiment.py` stands in for the emulator. Explain why that makes the tests fast and independent of Docker.
3. **Reading the KPIs and charts.** Check that the learner can read `docs/img/phase2_temperature_peak_heat_day.png` and `docs/img/phase2_power_peak_heat_day.png` unaided: where setback, preheating, and price shifting show up.
4. **Attribution by ablation.** The price boost was switched off (`boost_c=0`) to split the saving into setback and price. Numbers are in the "How it saves money" table of `docs/results/phase2.md`.
5. **MPC in more depth** (thermal model, optimizer). Only needed if the MPC controller gets built.

## Work left

| Item | Where | Notes |
| --- | --- | --- |
| Learning notes for each concept | The vault repo, `learning/`, one file per concept, from `templates/learning.md` | Write each one after its questions are answered, so it reflects what was actually understood |
| MPC controller | `src/edge_energy_optimizer/control/` | Optional. Needs BOPTEST, so home PC only. Phases 1 and 2 are due 11 October 2026 |
| Merge `phase-2` into `main` | GitHub | When the learner asks |
