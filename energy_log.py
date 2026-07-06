#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
energy_log.py

Defines EnergyLog (a single reading) and EnergyTracker (an in-memory series
of readings used to compute totals/averages for reports).

Covers SRS requirement:
    R10 Energy_Consumption_Tracking
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class EnergyLog:
    """One point-in-time sample of network-wide power draw."""
    timestamp: datetime
    kwh: float


class EnergyTracker:
    """Keeps a rolling history of EnergyLog samples and derives statistics from them."""

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self._logs: List[EnergyLog] = []

    def record(self, kwh: float, timestamp: datetime = None) -> EnergyLog:
        log = EnergyLog(timestamp=timestamp or datetime.now(), kwh=kwh)
        self._logs.append(log)
        if len(self._logs) > self.max_history:
            self._logs.pop(0)
        return log

    @property
    def logs(self) -> List[EnergyLog]:
        return list(self._logs)

    def total_kwh(self) -> float:
        return round(sum(log.kwh for log in self._logs), 3)

    def average_kwh(self) -> float:
        if not self._logs:
            return 0.0
        return round(self.total_kwh() / len(self._logs), 3)

    def latest(self) -> EnergyLog | None:
        return self._logs[-1] if self._logs else None
