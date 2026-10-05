# Architecture

High-level vision only. Details are filled in as each phase is built, and choices that are hard to reverse are recorded in [decisions/](decisions/).

## Goal

Reduce a building's energy cost, mainly its peak demand, without hurting occupant comfort, using a system that runs at the edge next to the equipment it controls.

## The control loop

The whole system is one loop that repeats on a fixed interval:

```
        ┌──────────────────────────────────────────────────────┐
        │                                                      │
        ▼                                                      │
   Measurements ──► Forecaster ──► Controller ──► Setpoints ───┘
   (load, weather,   (phase 1)     (phases 2, 4)  (HVAC, battery)
    zone temps)
        ▲                                             │
        └────────── Building and battery ◄────────────┘
                    (simulated: BOPTEST, battery model)
```

1. **Measure**: read current load, weather, and zone temperatures.
2. **Forecast**: predict load for the coming hours.
3. **Decide**: pick HVAC setpoints and battery charge or discharge power.
4. **Act**: write those setpoints to the equipment.

Each phase adds or hardens one part of this loop.

## Phases

### Phase 1: Energy load forecasting

A machine learning model that predicts building load over a short horizon (hours to a day ahead) from historical load, weather, and calendar features. Output is a forecast the controller can consume, plus an honest evaluation against a naive baseline.

Status: done. Gradient boosted trees forecast each hour of the next day, exposed through `forecast()` in `src/edge_energy_optimizer/forecasting/forecast.py`. Choices are recorded in [decisions/0002](decisions/0002-forecasting-data-and-model.md) and results are in the README.

### Phase 2: Control logic against a simulated building

A controller that chooses HVAC setpoints. It is tested against [BOPTEST](https://ibpsa.github.io/project1-boptest/), which runs a physics-based building model in Docker behind a REST API and scores each run on energy, cost, and comfort KPIs.

Status: done. A look-ahead heuristic cuts heating cost by 10% to 16% against a fixed-setpoint thermostat, with comfort no worse. Choices are recorded in [decisions/0003](decisions/0003-control-strategy.md) and results are in [results/phase2.md](results/phase2.md).

The code in `src/edge_energy_optimizer/control/` has three parts:

```
experiment.py (runner) ──► Controller.setpoint_c(observation, forecast) ──► °C
      │                         ├── FixedSetpointController   (baseline.py)
      │                         └── PredictiveController      (predictive.py)
      ▼
boptest.py (REST client) ──► BOPTEST in Docker
```

- **Controllers** see an observation and a forecast and return a setpoint in °C. They know nothing about BOPTEST, so phase 3 can put BACnet underneath them unchanged.
- **The runner** owns the loop: get a forecast, ask the controller, advance the building one hour, repeat. It also translates between BOPTEST's point names and units and the controller's.
- **The forecast comes from BOPTEST** (weather, price, comfort bounds). The phase 1 load forecaster is not wired in yet, because this controller does not need a load forecast. Phase 4 is where it joins the loop.

### Phase 3: BACnet and Modbus integration

A protocol layer so the controller talks to equipment the way it would on a real site: BACnet for building automation devices, Modbus for meters and power equipment. Simulated devices stand in for hardware. The controller should not know or care which protocol sits underneath.

### Phase 4: Peak demand shaving with a simulated battery

A battery model (capacity, power limits, efficiency, state of charge) and a dispatch strategy that charges when demand is low and discharges into forecast peaks. Success is measured as peak reduction and cost saved versus no battery.

### Phase 5: Edge deployment on k3s with MQTT and a dashboard

The components are packaged as containers and deployed to a k3s cluster. MQTT carries telemetry and commands between them. A dashboard shows live load, forecast, battery state, and savings.

## Target component view (after phase 5)

```
┌──────────────────────── k3s edge cluster ────────────────────────┐
│                                                                  │
│  Protocol gateway ──┐                        ┌── Forecaster      │
│  (BACnet, Modbus)   ├──►  MQTT broker  ◄─────┼── Controller      │
│                     │                        └── Dashboard       │
└─────────┬───────────┴────────────────────────────────────────────┘
          │
          ▼
  Simulated building (BOPTEST), meters, and battery
```

## Design principles

- **Simulation first.** Every external system (building, devices, battery) is simulated, so the project runs on a laptop.
- **Stable seams.** Forecaster, controller, and protocol layer talk through narrow interfaces so each can be replaced or tested alone.
- **Measure against a baseline.** Every phase reports its result next to a simple baseline. A number with nothing to compare against proves nothing.
- **Each phase is demonstrable.** A phase is done when it can be run and shown end to end, not when the code exists.

## Open questions

- Whether to add an MPC controller next to the heuristic (phase 2 follow-up).
- Which Python libraries for BACnet and Modbus (phase 3).
- Dashboard technology (phase 5).
