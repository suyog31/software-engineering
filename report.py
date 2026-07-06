#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
report.py

Defines Report: a fault report raised against a street light, either by the
automated sensor layer or by a user. A Report is the trigger that leads the
system to create a MaintenanceTask (see maintenance_task.py).

Covers SRS requirements:
    Non-functional R4  Accurate_Fault_Detection
    R6  Send_Maintenance_Alerts (indirectly — a Report is what gets alerted on)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
import itertools


class ReportStatus(Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"


class Report:
    """A fault report tied to one street light and, optionally, the user who filed it."""

    _id_counter = itertools.count(1)

    def __init__(self, item_id: str, user_id: Optional[int] = None, description: str = ""):
        self.report_id: str = f"RPT-{next(Report._id_counter):04d}"
        self.item_id: str = item_id          # the StreetLight.light_id this report is about
        self.user_id: Optional[int] = user_id  # who filed it; None if raised automatically by a sensor
        self.description: str = description
        self.status: ReportStatus = ReportStatus.OPEN
        self.submitted_at: datetime = datetime.now()
        self.updated_at: datetime = self.submitted_at

    # ---------- submit_report ----------
    @classmethod
    def submit_report(cls, item_id: str, user_id: Optional[int] = None, description: str = "") -> "Report":
        """Factory used by users or the sensor layer to file a new report."""
        return cls(item_id=item_id, user_id=user_id, description=description)

    # ---------- update_status ----------
    def update_status(self, status: ReportStatus) -> None:
        self.status = status
        self.updated_at = datetime.now()

    def __repr__(self) -> str:
        return f"<Report {self.report_id} item={self.item_id} status={self.status.value}>"
