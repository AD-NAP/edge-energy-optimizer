# 0002: Forecasting data and model

- Status: accepted
- Date: 2026-10-04

## Context

Phase 1 needs a dataset to learn from and a model family. The forecast feeds later phases that plan a day ahead (battery charging, pre-cooling).

## Decision

- **Data:** one real office building, `Hog_office_Shawnna`, from the Building Data Genome Project 2, with its site's weather. It has no missing or zero hours, clear daily and weekly cycles, and a strong link to temperature.
- **Task:** hourly load, forecast 24 hours ahead. Every feature must be known 24 hours before the hour being predicted.
- **Model:** gradient boosted trees (`HistGradientBoostingRegressor` from scikit-learn) with default settings.
- **Evaluation:** train on 2016, test on 2017, split by time. Report MAE next to the naive "same hour last week" baseline.

## Consequences

- Real data is messier and more credible than simulated data, but the model does not describe the BOPTEST building used in phase 2. The pipeline must be retrained on that building's data if phase 2 needs a load forecast.
- Trees handle the non-linear temperature effect without extra work and train in seconds.
- Measured weather stands in for weather forecasts, so reported errors are optimistic.
- One training year gives few holiday examples and no protection against drift. See the known limits in the README.
