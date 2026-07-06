#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
demo.py

A runnable walkthrough of the Smart Street Lighting System class model.
Run with:  python demo.py
"""

from datetime import time

from user import Admin, MaintenanceStaff
from system import SmartStreetLightingSystem


def main():
    system = SmartStreetLightingSystem()

    # --- setup: add street lights to two zones ---
    l1 = system.add_light(zone="Main Street", latitude=27.7172, longitude=85.3240)
    l2 = system.add_light(zone="Park Avenue", latitude=27.7180, longitude=85.3250)
    system.add_light(zone="Main Street")

    # --- users ---
    admin = Admin("City Admin", "admin@lumen-city.gov", "9800000000", "admin123")
    staff = MaintenanceStaff("R. Karki", "rkarki@lumen-city.gov", "9811111111", "staff123")

    assert admin.login("admin@lumen-city.gov", "admin123")
    assert staff.login("rkarki@lumen-city.gov", "staff123")

    # --- R7: schedule Main Street to run 18:00-06:00 ---
    admin.schedule_lighting_operations(system, zone="Main Street", on_time=time(18, 0), off_time=time(6, 0))

    # --- R3 / R4: admin manually turns a light on and dims it ---
    admin.control_street_light(system, l2.light_id, turn_on=True)
    admin.configure_brightness(system, l2.light_id, 85)

    # --- R8: a motion sensor pings the system ---
    system.register_motion(l2.light_id)

    # --- fault pipeline: l1 develops a fault -> report + task + alert ---
    task = system.report_fault(l1.light_id, description="Light flickering then went dark.")

    # --- R15: admin assigns the task to maintenance staff ---
    admin.assign_maintenance_task(system, task.task_id, staff)

    # --- R11: staff checks their queue ---
    print("Staff task queue:", staff.view_maintenance_status(system))

    # --- R13: staff looks up where the fault is ---
    print("Fault location:", staff.view_fault_location(system, l1.light_id))

    # --- R12: staff completes the repair ---
    staff.update_repair_status(system, task.task_id, status="completed",
                                remarks="Replaced LED driver module.")

    # --- R14: history now shows the completed job ---
    print("Maintenance history:", staff.view_maintenance_history(system))

    # --- R10: sample energy draw a few times ---
    for _ in range(3):
        system.sample_energy()

    # --- R2 / R9: live status snapshot ---
    print("\nNetwork status:")
    for light in admin.monitor_street_lights(system):
        print(" ", light)

    # --- R5: generate the admin report ---
    print("\nGenerated report:")
    for key, value in admin.generate_report(system).items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
