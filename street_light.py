#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
street_light.py

Defines StreetLight, the physical/logical unit controlled by the system.

Covers SRS requirements:
    R3  Control_Street_Lights (turn_on / turn_off)
    R4  Configure_Brightness_level (dim_light)
    R8  Motion_Detection (register_motion)
    R9  Real_Time_Status_Update (status property)
    Non-functional R4 Accurate_Fault_Detection (report_fault)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import itertools


class LightStatus(Enum):
    ON = "on"
    OFF = "off"
    FAULT = "fault"


@dataclass
class Location:
    """Lightweight location value object (swap for real GPS coords if available)."""
    zone: str
    latitude: float = 0.0
    longitude: float = 0.0

    def __str__(self) -> str:
        return f"{self.zone} ({self.latitude:.5f}, {self.longitude:.5f})"


class StreetLight:
    """A single street light node on the network."""

    _id_counter = itertools.count(1)

    def __init__(self, location: Location, brightness: int = 70):
        self.light_id: str = f"SL-{next(StreetLight._id_counter):03d}"
        self.location: Location = location
        self.status: LightStatus = LightStatus.OFF
        self.brightness_level: int = self._clamp(brightness)
        self.manual_override: bool = False   # True while an admin has taken manual control
        self.last_maintenance_at: Optional[datetime] = None
        self.motion_detected: bool = False

    @staticmethod
    def _clamp(value: int) -> int:
        return max(0, min(100, value))

    # ---------- R3 ----------
    def turn_on(self, manual: bool = False) -> None:
        if self.status == LightStatus.FAULT:
            raise RuntimeError(f"{self.light_id} is faulty and cannot be controlled remotely.")
        self.status = LightStatus.ON
        self.manual_override = manual

    def turn_off(self, manual: bool = False) -> None:
        if self.status == LightStatus.FAULT:
            raise RuntimeError(f"{self.light_id} is faulty and cannot be controlled remotely.")
        self.status = LightStatus.OFF
        self.manual_override = manual

    def reset_to_automatic(self) -> None:
        """Hand control of this light back to the daylight/schedule sensor."""
        self.manual_override = False

    # ---------- R4 ----------
    def dim_light(self, percentage: int) -> None:
        if self.status == LightStatus.FAULT:
            raise RuntimeError(f"{self.light_id} is faulty; brightness cannot be set.")
        self.brightness_level = self._clamp(percentage)

    # ---------- R8 ----------
    def register_motion(self) -> None:
        """Called by the sensor layer when movement is detected nearby."""
        self.motion_detected = True
        if self.status == LightStatus.ON:
            self.brightness_level = 100

    def clear_motion(self) -> None:
        self.motion_detected = False

    # ---------- Fault handling ----------
    def report_fault(self) -> None:
        self.status = LightStatus.FAULT
        self.manual_override = False

    def mark_repaired(self) -> None:
        self.status = LightStatus.OFF
        self.manual_override = False
        self.last_maintenance_at = datetime.now()

    # ---------- energy ----------
    def instantaneous_kwh(self, base_draw_kw: float = 0.4, idle_draw_kw: float = 0.01) -> float:
        """A simple model: full draw scaled by brightness when on, idle draw otherwise."""
        if self.status == LightStatus.ON:
            return round(base_draw_kw * (self.brightness_level / 100), 3)
        return idle_draw_kw

    def __repr__(self) -> str:
        return (f"<StreetLight {self.light_id} status={self.status.value} "
                f"brightness={self.brightness_level}% zone={self.location.zone}>")
