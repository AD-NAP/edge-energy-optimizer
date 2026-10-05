"""A thin client for the BOPTEST REST API (v0.9.0, run locally with Docker)."""

import requests

DEFAULT_URL = "http://127.0.0.1:80"
TIMEOUT_S = 300


class BoptestClient:
    def __init__(self, url: str = DEFAULT_URL) -> None:
        self._url = url
        self._testid: str | None = None

    def select(self, testcase: str) -> None:
        """Start a fresh copy of a test case. Every later call talks to that copy."""
        response = requests.post(f"{self._url}/testcases/{testcase}/select", timeout=TIMEOUT_S)
        response.raise_for_status()
        self._testid = response.json()["testid"]

    def set_scenario(self, time_period: str, electricity_price: str) -> dict:
        """Jump to the start of a time period. Returns the first measurements."""
        payload = self._call("put", "scenario", {
            "time_period": time_period,
            "electricity_price": electricity_price,
        })
        return payload["time_period"]

    def forecast(self, point_names: list[str], horizon_s: float, interval_s: float) -> dict:
        return self._call("put", "forecast", {
            "point_names": point_names,
            "horizon": horizon_s,
            "interval": interval_s,
        })

    def advance(self, inputs: dict) -> dict:
        """Apply `inputs`, simulate one control step, and return the new measurements."""
        return self._call("post", "advance", inputs)

    def results(self, point_names: list[str], start_s: float, final_s: float) -> dict:
        return self._call("put", "results", {
            "point_names": point_names,
            "start_time": start_s,
            "final_time": final_s,
        })

    def kpis(self) -> dict:
        return self._call("get", "kpi")

    def stop(self) -> None:
        requests.put(f"{self._url}/stop/{self._testid}", timeout=TIMEOUT_S).raise_for_status()

    def _call(self, method: str, endpoint: str, body: dict | None = None) -> dict:
        response = requests.request(
            method, f"{self._url}/{endpoint}/{self._testid}", json=body, timeout=TIMEOUT_S
        )
        response.raise_for_status()
        # BOPTEST wraps every answer as {"status", "message", "payload"}.
        answer = response.json()
        if answer["status"] != 200:
            raise RuntimeError(f"BOPTEST {endpoint} failed: {answer['message']}")
        return answer["payload"]
