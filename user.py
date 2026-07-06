#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
user.py

Defines the User base class and its two specialised roles, Admin and
MaintenanceStaff, for the Smart Street Lighting System.

Covers SRS requirements:
    R1  Login_Admin / secure login for any user
    R5 (Security) Secure_User_Access
    updateProfile() — account self-service for every role
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib
import itertools


class UserRole(Enum):
    ADMIN = "admin"
    MAINTENANCE_STAFF = "maintenance_staff"


class User:
    """Base class for anyone who can log into the system."""

    _id_counter = itertools.count(1)

    def __init__(self, full_name: str, email: str, phone_number: str, password: str):
        self.user_id: int = next(User._id_counter)
        self.full_name: str = full_name
        self.email: str = email
        self.phone_number: str = phone_number
        self.created_at: datetime = datetime.now()
        self._password_hash: str = self._hash_password(password)
        self.is_logged_in: bool = False

    # ---------- internal helpers ----------
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # ---------- R1 / R5: authentication ----------
    def login(self, email: str, password: str) -> bool:
        """Validate credentials and open a session. Returns True on success."""
        if email == self.email and self._hash_password(password) == self._password_hash:
            self.is_logged_in = True
            return True
        return False

    def logout(self) -> None:
        self.is_logged_in = False

    def change_password(self, old_password: str, new_password: str) -> bool:
        if self._hash_password(old_password) != self._password_hash:
            return False
        self._password_hash = self._hash_password(new_password)
        return True

    # ---------- profile self-service ----------
    def update_profile(self, full_name: Optional[str] = None, email: Optional[str] = None,
                        phone_number: Optional[str] = None) -> None:
        if full_name:
            self.full_name = full_name
        if email:
            self.email = email
        if phone_number:
            self.phone_number = phone_number

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} #{self.user_id} {self.full_name}>"


class Admin(User):
    """
    City administrator. Owns the operations described in R2-R10 and R15:
    monitoring, remote control, brightness configuration, scheduling,
    reporting, alerting, and assigning maintenance work.

    The heavy lifting for these requirements lives in SmartStreetLightingSystem
    (system.py); Admin exposes the actions a person in this role can trigger.
    """

    def __init__(self, full_name: str, email: str, phone_number: str, password: str):
        super().__init__(full_name, email, phone_number, password)
        self.role = UserRole.ADMIN

    # R2
    def monitor_street_lights(self, system: "SmartStreetLightingSystem"):
        return system.get_network_status()

    # R3
    def control_street_light(self, system: "SmartStreetLightingSystem", light_id: str, turn_on: bool):
        return system.set_light_power(light_id, turn_on, manual=True)

    # R4
    def configure_brightness(self, system: "SmartStreetLightingSystem", light_id: str, percentage: int):
        return system.set_light_brightness(light_id, percentage)

    # R7
    def schedule_lighting_operations(self, system: "SmartStreetLightingSystem", zone: str,
                                      on_time: str, off_time: str):
        return system.set_zone_schedule(zone, on_time, off_time)

    # R5
    def generate_report(self, system: "SmartStreetLightingSystem"):
        return system.generate_report()

    # R15
    def assign_maintenance_task(self, system: "SmartStreetLightingSystem", task_id: str, staff: "MaintenanceStaff"):
        return system.assign_task(task_id, staff)


class MaintenanceStaff(User):
    """
    Field maintenance personnel. Covers R11-R14: viewing assigned faults,
    updating repair status, locating faults, and reviewing history.
    """

    def __init__(self, full_name: str, email: str, phone_number: str, password: str):
        super().__init__(full_name, email, phone_number, password)
        self.role = UserRole.MAINTENANCE_STAFF

    # R11
    def view_maintenance_status(self, system: "SmartStreetLightingSystem"):
        return system.get_tasks_for_staff(self)

    # R12
    def update_repair_status(self, system: "SmartStreetLightingSystem", task_id: str,
                              status: str, remarks: str = ""):
        return system.update_task_status(task_id, status, remarks)

    # R13
    def view_fault_location(self, system: "SmartStreetLightingSystem", light_id: str):
        return system.get_light_location(light_id)

    # R14
    def view_maintenance_history(self, system: "SmartStreetLightingSystem"):
        return system.get_task_history(self)
