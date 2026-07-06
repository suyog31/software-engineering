#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
system.py

SmartStreetLightingSystem is the central controller/facade that owns every
street light, report, task, schedule, and log, and implements the
requirements that don't belong to any single actor class:

    R2  Monitor_Street_Lights
    R3  Control_Street_Lights
    R4  Configure_Brightness_level
    R5  Generate_reports
    R6  Send_Maintenance_Alerts
    R7  Schedule_Lighting_Operations
    R9  Real_Time_Status_Update
    R10 Energy_Consumption_Tracking
    R15 Assign_Maintenance_Task

It composes the other classes rather than re-implementing their behaviour:
StreetLight, Report, MaintenanceTask, LightingSchedule, EnergyTracker,
NotificationService, Admin, MaintenanceStaff.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Dict, List, Optional

from street_light import StreetLight, LightStatus, Location
from report import Report, ReportStatus
from maintenance_task import MaintenanceTask, TaskStatus
from schedule import LightingSchedule
from energy_log import EnergyTracker
from notification import NotificationService, NotificationType
from user import MaintenanceStaff


class SmartStreetLightingSystem:
    def __init__(self):
        self.lights: Dict[str, StreetLight] = {}
        self.reports: Dict[str, Report] = {}
        self.tasks: Dict[str, MaintenanceTask] = {}
        self.schedules: Dict[str, LightingSchedule] = {}
        self.energy = EnergyTracker()
        self.notifications = NotificationService()

    # ---------- setup ----------
    def add_light(self, zone: str, brightness: int = 70, latitude: float = 0.0,
                   longitude: float = 0.0) -> StreetLight:
        light = StreetLight(Location(zone, latitude, longitude), brightness)
        self.lights[light.light_id] = light
        self.schedules.setdefault(zone, LightingSchedule(zone, time(18, 0), time(6, 0)))
        return light

    # ---------- R2 / R9 ----------
    def get_network_status(self) -> List[StreetLight]:
        """Real-time snapshot of every light — feeds the monitoring dashboard."""
        return list(self.lights.values())

    def get_light_location(self, light_id: str) -> Optional[str]:
        light = self.lights.get(light_id)
        return str(light.location) if light else None

    # ---------- R3 / R4 ----------
    def set_light_power(self, light_id: str, turn_on: bool, manual: bool = True) -> StreetLight:
        light = self._require_light(light_id)
        light.turn_on(manual=manual) if turn_on else light.turn_off(manual=manual)
        return light

    def set_light_brightness(self, light_id: str, percentage: int) -> StreetLight:
        light = self._require_light(light_id)
        light.dim_light(percentage)
        return light

    # ---------- R7 ----------
    def set_zone_schedule(self, zone: str, on_time: time, off_time: time) -> LightingSchedule:
        sched = self.schedules.setdefault(zone, LightingSchedule(zone, on_time, off_time))
        sched.update(on_time, off_time)
        return sched

    def apply_schedules(self, now: time) -> None:
        """Call periodically (e.g. every tick/minute) to let schedules drive lights
        that are not under manual override and are not faulty."""
        for light in self.lights.values():
            if light.manual_override or light.status == LightStatus.FAULT:
                continue
            sched = self.schedules.get(light.location.zone)
            if not sched:
                continue
            light.turn_on() if sched.is_light_period(now) else light.turn_off()

    # ---------- R8: motion ----------
    def register_motion(self, light_id: str) -> None:
        light = self._require_light(light_id)
        light.register_motion()
        self.notifications.send(
            f"Motion detected near {light.light_id} ({light.location.zone}).",
            NotificationType.MOTION_DETECTED,
        )

    # ---------- fault handling / R6 ----------
    def report_fault(self, light_id: str, user_id: Optional[int] = None,
                      description: str = "") -> MaintenanceTask:
        """Raise a Report, flag the light, and open a MaintenanceTask + alert. This is
        the pipeline behind Non-functional R4 (accurate fault detection) and R6
        (send maintenance alerts)."""
        light = self._require_light(light_id)
        light.report_fault()

        report = Report.submit_report(item_id=light_id, user_id=user_id, description=description)
        self.reports[report.report_id] = report

        task = MaintenanceTask(light_id=light_id, report_id=report.report_id)
        self.tasks[task.task_id] = task

        self.notifications.send(
            f"Fault detected on {light_id} ({light.location.zone}). Task {task.task_id} created.",
            NotificationType.FAULT_DETECTED,
        )
        return task

    # ---------- R15 ----------
    def assign_task(self, task_id: str, staff: MaintenanceStaff) -> MaintenanceTask:
        task = self._require_task(task_id)
        task.assign_to(staff.user_id)
        self.notifications.send(
            f"{task_id} ({task.light_id}) assigned to {staff.full_name}.",
            NotificationType.TASK_ASSIGNED,
            recipient_id=staff.user_id,
        )
        return task

    # ---------- R11 / R12 / R14 ----------
    def get_tasks_for_staff(self, staff: MaintenanceStaff) -> List[MaintenanceTask]:
        return [t for t in self.tasks.values() if t.assigned_to == staff.user_id]

    def update_task_status(self, task_id: str, status: str, remarks: str = "") -> MaintenanceTask:
        task = self._require_task(task_id)
        task.update_status(TaskStatus(status), remarks)
        if task.status == TaskStatus.COMPLETED:
            light = self._require_light(task.light_id)
            light.mark_repaired()
            if task.report_id and task.report_id in self.reports:
                self.reports[task.report_id].update_status(ReportStatus.RESOLVED)
            self.notifications.send(
                f"{task_id} ({task.light_id}) marked completed.",
                NotificationType.TASK_COMPLETED,
            )
        return task

    def get_task_history(self, staff: Optional[MaintenanceStaff] = None) -> List[MaintenanceTask]:
        completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        if staff:
            completed = [t for t in completed if t.assigned_to == staff.user_id]
        return sorted(completed, key=lambda t: t.resolved_at or datetime.min)

    # ---------- R10 ----------
    def sample_energy(self) -> float:
        total = sum(light.instantaneous_kwh() for light in self.lights.values())
        self.energy.record(total)
        return total

    # ---------- R5 ----------
    def generate_report(self) -> dict:
        lights = list(self.lights.values())
        return {
            "generated_at": datetime.now(),
            "lights_on": sum(1 for l in lights if l.status == LightStatus.ON),
            "lights_off": sum(1 for l in lights if l.status == LightStatus.OFF),
            "faults_open": sum(1 for l in lights if l.status == LightStatus.FAULT),
            "average_kwh": self.energy.average_kwh(),
            "total_kwh": self.energy.total_kwh(),
            "tasks_completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "tasks_pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
        }

    # ---------- internal ----------
    def _require_light(self, light_id: str) -> StreetLight:
        light = self.lights.get(light_id)
        if not light:
            raise KeyError(f"No such street light: {light_id}")
        return light

    def _require_task(self, task_id: str) -> MaintenanceTask:
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError(f"No such maintenance task: {task_id}")
        return task
