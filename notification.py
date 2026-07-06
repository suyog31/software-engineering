#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
notification.py

Defines Notification and NotificationService: the alerting mechanism that
tells maintenance personnel (and the admin dashboard feed) when a fault is
detected or a task changes state.

Covers SRS requirement:
    R6  Send_Maintenance_Alerts
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
import itertools


class NotificationType(Enum):
    FAULT_DETECTED = "fault_detected"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    MOTION_DETECTED = "motion_detected"


class Notification:
    _id_counter = itertools.count(1)

    def __init__(self, message: str, notif_type: NotificationType, recipient_id: Optional[int] = None):
        self.notification_id: str = f"NTF-{next(Notification._id_counter):04d}"
        self.message: str = message
        self.type: NotificationType = notif_type
        self.recipient_id: Optional[int] = recipient_id  # None = broadcast to the admin feed
        self.created_at: datetime = datetime.now()
        self.read: bool = False

    def mark_read(self) -> None:
        self.read = True

    def __repr__(self) -> str:
        return f"<Notification {self.notification_id} {self.type.value}: {self.message}>"


class NotificationService:
    """Fan-out point for creating and retrieving notifications."""

    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self._notifications: List[Notification] = []

    def send(self, message: str, notif_type: NotificationType,
              recipient_id: Optional[int] = None) -> Notification:
        notif = Notification(message, notif_type, recipient_id)
        self._notifications.insert(0, notif)
        if len(self._notifications) > self.max_history:
            self._notifications.pop()
        return notif

    def for_recipient(self, recipient_id: Optional[int] = None) -> List[Notification]:
        """recipient_id=None returns broadcast (admin feed) notifications."""
        return [n for n in self._notifications if n.recipient_id == recipient_id]

    def unread_count(self, recipient_id: Optional[int] = None) -> int:
        return sum(1 for n in self.for_recipient(recipient_id) if not n.read)
