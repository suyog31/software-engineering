#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
schedule.py

Defines LightingSchedule: the on/off time window an admin configures for a
zone of street lights.

Covers SRS requirement:
    R7  Schedule_Lighting_Operations
"""

from __future__ import annotations

from datetime import time


class LightingSchedule:
    """A recurring daily on/off window for one zone."""

    def __init__(self, zone: str, on_time: time, off_time: time):
        self.zone: str = zone
        self.on_time: time = on_time
        self.off_time: time = off_time

    def update(self, on_time: time = None, off_time: time = None) -> None:
        if on_time is not None:
            self.on_time = on_time
        if off_time is not None:
            self.off_time = off_time

    def is_light_period(self, now: time) -> bool:
        """True if `now` falls inside the configured on-window. Handles overnight wraps."""
        if self.on_time <= self.off_time:
            return self.on_time <= now < self.off_time
        return now >= self.on_time or now < self.off_time

    def __repr__(self) -> str:
        return f"<LightingSchedule zone={self.zone} on={self.on_time} off={self.off_time}>"
