# What went wrong, and what it taught

Every mistake, wrong turn, and surprise in this project so far, with how it was found, how it was fixed, and the lesson. Newest phase last. Concept notes that explain the ideas in more depth live outside the repo.

## Phase 1: load forecasting

### Features that peeked into the future

- **What went wrong:** Getting the lag features legal took three tries. A "load 1 hour before" feature looks harmless, but when forecasting a whole day ahead, one hour before the target hour has not happened yet.
- **How it was found:** Walking through one forecast by clock time. Forecasting Tuesday 15:00 on Monday 15:00, "1 hour before" is Tuesday 14:00.
- **Fix:** Every lag counts back from the target hour and is at least 24 hours. Future weather is allowed, because a weather forecast for it exists.
- **Lesson:** Historical data hides leakage. Every row is in the past, so an illegal column can still be built and will score well. It is only empty in live use. Check each feature by asking whether its value exists at the moment the forecast is made.

### The model guesses high

- **What went wrong:** Average error on 2017 is +13.8 kWh. The model overshoots.
- **How it was found:** Splitting errors by month and day type instead of reading one MAE number.
- **Cause:** The building used about 8% less energy in 2017 than in 2016, the training year. The model learned the old level.
- **Tried:** Adding the previous week's average load as a feature. It did not help, so it was left out.
- **Status:** Not fixed. Documented as a known limit. Live use would need regular retraining.
- **Lesson:** One overall score hides where a model is wrong. Error analysis by group points at the cause.

### Holidays are the weak spot

- **What went wrong:** MAE on holidays is 61.9 kWh, against 32.6 on normal weekdays.
- **Cause:** One training year has too few holidays to learn from.
- **Status:** Not fixed. Documented as a known limit.
- **Lesson:** A model can only be as good as the examples it has seen of each situation.

### Reported errors are optimistic

- **What went wrong:** The model was scored with measured weather, but a live system only has weather forecasts, which are less accurate.
- **Status:** Documented in the README and decision 0002.
- **Lesson:** Say which inputs a score assumed, not just the score.

## Phase 2: control against BOPTEST

### BOPTEST would not start

- **What went wrong:** BOPTEST 0.9.0 pins MinIO images that were removed from Docker Hub in September 2026, so `docker compose up` failed.
- **Fix:** `docker/boptest.override.yml` swaps in Chainguard's builds of MinIO. The upstream checkout stays untouched.
- **Lesson:** Pinned versions of third-party images can still vanish. Keep local fixes in an override file, so they are easy to drop when upstream fixes it.

### Storing heat on sunny days overheated the home

- **What went wrong:** The first predictive controller added 1 °C whenever the price was cheap. On sunny spring days the sun was already warming the house, so it overheated: 8.32 Kh of discomfort against the baseline's 7.08 Kh.
- **How it was found:** The temperature charts, not the cost table. Cost had gone down.
- **Fix:** Skip the boost when the outdoor forecast reaches 10 °C.
- **Lesson:** Look at the time series, not only the totals. A better headline number can hide a worse behaviour.

### A price rule that only moved the cost around

- **What went wrong:** The price rule does nothing under the day/night tariff. It looks for the cheapest quarter of the day, and the night rate covers more than a quarter, so no hour stands out.
- **Tried:** Boosting on any below-average price instead. Cost fell under the day/night tariff and rose under spot prices, for the same total (461.10 EUR against 461.45 EUR). Not adopted.
- **Lesson:** Check a change across every scenario. A gain in one place can be a loss somewhere else.

### Tuning on its own exam

- **What went wrong:** The 10 °C mild-day threshold was chosen after seeing which days overheated, then reported on those same days. The predictive controller's savings were therefore optimistic.
- **How it was found:** Reviewing the order of events: tune first, then score on the same data.
- **Fix (16 November):** Two unseen two-week periods were added. On them the predictive controller saved 14% to 18% in March but only 8% in October, against 10% to 16% on the scenarios it was tuned on.
- **Lesson:** A score is only honest if the data behind it played no part in choosing the settings. Keep a test that nothing is tuned on.

### The baseline flatters the result

- **What went wrong:** "Smart control saves 14%" overstates it. Most of the saving is from not heating an empty home, which a cheap timer thermostat would also do. Price awareness adds 2 to 5 points.
- **How it was found:** Turning off one rule at a time and measuring what each contributes.
- **Status:** Stated in the results. A timer thermostat would be the tougher baseline.
- **Lesson:** A result is only as strong as the baseline it beats. Pick the baseline a sceptic would pick.

### The MPC slipped from Friday 9 October to 16 November

- **What went wrong:** Phases 1 and 2 were due on 11 October. The optional MPC was planned for 9 October, then moved several times and parked behind other work.
- **Lesson:** Optional work with no deadline drifts. A handoff note with a concrete plan made it quick to restart.

## Phase 2: the MPC controller (16 November)

### A model fitted on thermostat data was worse than doing nothing

- **What went wrong:** The first house model was fitted on the saved phase 2 runs. Predicting 24 hours ahead, it was off by 1.05 °C, worse than assuming the temperature stays put (0.85 °C).
- **Cause:** A thermostat was in charge in those runs. It raised power exactly when the room cooled, so the data said "more heating goes with colder rooms" and the model could not tell cause from effect.
- **Fix:** `control/identify.py` drives the heat pump directly with a random signal for two weeks (from day 45), and checks the model on two more weeks (from day 330). The new model is off by 0.50 °C, against 1.08 °C for "stays put".
- **Lesson:** To learn what an input does, the input must move independently of the output. More data recorded under a controller does not help.

### The random signal ran the house hot

- **What went wrong:** The excitation signal used modulation levels from 0 to 1 evenly, and any level above 0 already draws about 2 kW. The house ran at 21 to 33 °C, mostly above the comfort band.
- **Status:** Not fixed. The model is linear and checked well on unseen weeks, but it is least tested near 21 °C, where the controller works.
- **Lesson:** Excite the system around where it will be used.

### Excitation holds merged

- **What went wrong:** The random signal could pick the same level twice in a row, which merged two holds into one longer than the 6-hour maximum.
- **How it was found:** A test written before the code failed with a 12-hour hold.
- **Fix:** Each new level must differ from the last.
- **Lesson:** Watching a test fail catches real bugs, not just missing code.

### Weather points had a different name

- **What went wrong:** The results request asked for `reaWeaTDryBul_y` and BOPTEST answered 400.
- **Fix:** Weather measurements carry a `weaSta_` prefix: `weaSta_reaWeaTDryBul_y`. Found by asking BOPTEST one point at a time.
- **Lesson:** When an API rejects a batch, split it to find the bad item. The docs' names and the API's names can differ.

### A wrong test

- **What went wrong:** The test for "do not join two runs" added 5 °C to the second run. That broke the physics, so no fit could match it, and the test failed against correct code.
- **Fix:** Simulate the second run from a warmer start instead.
- **Lesson:** A failing test can be the wrong one. Synthetic data must obey the model it tests.

### Circular import

- **What went wrong:** The runner imports the MPC, which imports the house model, which imported the runner for its data folder. Every test failed to load.
- **Fix:** Import the data folder inside the model's `main()`.
- **Lesson:** Shared constants should sit low in the import tree, or be imported where they are used.

### The first MPC heated an empty room to 30 °C

- **What went wrong:** The first MPC cost more than both other controllers in the mild period, with 48 Kh of discomfort. The house was too warm, not too cold.
- **How it was found:** Splitting discomfort into too warm and too cold, then reading one bad day hour by hour. The heat pump ran at 3 kW while the room was at 28 °C.
- **Cause:** The plan is in kW, but the runner sends a setpoint, and the MPC sent "the temperature I expect after this hour", even when the plan said off. On sunny days the room ran warmer than the model expected, the setpoint followed it up, and the thermostat kept heating.
- **Fix:** When the plan says off, ask for the comfort floor.
- **Lesson:** How a plan is turned into a command matters as much as the plan. Sending a prediction as a target turns every model error into an action.

### Fixing it meant tuning on the exam again

- **What went wrong:** The fix above was made after seeing the reported scenarios, the same trap as the 10 °C threshold.
- **Fix:** All three controllers were also run on two unseen periods (from days 64 and 300), and the results say which numbers are which. MPC was cheapest on all four unseen runs: 3% to 8% below the predictive controller.
- **Lesson:** When a fix is driven by the test set, get a fresh test set before claiming the gain.

### Reheating starts late in the cold

- **What went wrong:** In the coldest period, MPC is less comfortable than the heuristic (3.11 Kh against 1.53 Kh under the day/night tariff).
- **Cause:** The model treats heat as arriving within the hour, but here it goes through a heavy floor first.
- **Status:** Not fixed. Driving the heat pump directly, or a model with the floor as a second state, would help.
- **Lesson:** A simple model is good enough on average but shows its gaps where timing matters most.

### Long runs ran out of network ports

- **What went wrong:** The 24-run experiment crashed after 13 runs with `WinError 10048`.
- **Cause:** Every BOPTEST call opened a new connection. Thousands of closed connections were waiting to time out, and Windows ran out of ports.
- **Fix:** One `requests.Session` reused for every call.
- **Lesson:** Reuse HTTP connections for chatty clients. The bug only appears at scale, so short test runs never show it.

### A scripted edit missed silently

- **What went wrong:** A Python string replace on `report.py` did not match because of the `°` character, so the MPC label was never added. The chart crashed later.
- **Fix:** Edit the file directly and check that every replacement matched.
- **Lesson:** Bulk find-and-replace should fail loudly when nothing matches.
