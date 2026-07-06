#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
maintenance_task.py

Defines MaintenanceTask: the unit of work a maintenance staff member acts on.
A task is created from a Report (see report.py) once a fault is confirmed,
and is assigned to a MaintenanceStaff member by an Admin.

Covers SRS requirements:
    R11 View_Maintenance_Status
    R12 Update_Repair_Status
    R14 Maintenance_History_Tracking
    R15 Assign_Maintenance_Task
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
import itertools


class TaskStatus(Enum):
    PENDING = "pending"       # created, not yet assigned
    ONGOING = "ongoing"       # assigned and being worked on
    COMPLETED = "completed"   # repaired


class MaintenanceTask:
    """A repair job tracked from creation through to completion."""

    _id_counter = itertools.count(1)

    def __init__(self, light_id: str, report_id: Optional[str] = None):
        self.task_id: str = f"MT-{next(MaintenanceTask._id_counter):04d}"
        self.light_id: str = light_id
        self.report_id: Optional[str] = report_id
        self.assigned_to: Optional[int] = None   # MaintenanceStaff.user_id
        self.status: TaskStatus = TaskStatus.PENDING
        self.remarks: str = ""
        self.created_at: datetime = datetime.now()
        self.resolved_at: Optional[datetime] = None

    # ---------- R15 ----------
    def assign_to(self, staff_user_id: int) -> None:
        self.assigned_to = staff_user_id
        self.status = TaskStatus.ONGOING

    # ---------- R12 ----------
    def update_status(self, status: TaskStatus, remarks: str = "") -> None:
        self.status = status
        if remarks:
            self.remarks = remarks
        if status == TaskStatus.COMPLETED:
            self.resolved_at = datetime.now()

    def __repr__(self) -> str:
        return f"<MaintenanceTask {self.task_id} light={self.light_id} status={self.status.value}>"
