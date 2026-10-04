# 0001: Python with uv

- Status: accepted
- Date: 2026-10-04

## Context

The project needs ML libraries, building simulation clients, and industrial protocol libraries. It also needs a setup that new contributors can reproduce in one command.

## Decision

Use Python, with [uv](https://docs.astral.sh/uv/) for Python version and dependency management. Dependencies live in `pyproject.toml` and are locked in `uv.lock`.

## Consequences

- One tool replaces pip, venv, and pyenv. Setup is `uv sync`.
- Contributors must install uv first.
- `pip install` is not used in this repo, since it would bypass the lockfile.
