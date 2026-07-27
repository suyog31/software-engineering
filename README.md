# Lumen — Smart Street Lighting System

Lumen is a municipal smart street lighting platform built around a Python OOP domain model, paired with a browser-based control console (HTML/CSS/JS) that simulates the network in real time.

The project has two parts:

- **Backend domain model (Python)** — a class-based simulation of street lights, users, faults, maintenance tasks, schedules, energy tracking, and notifications, mapped directly to a set of SRS requirements.
- **Frontend console (HTML/CSS/JS)** — a self-contained web dashboard that visualizes the network on a live map, lets an Admin monitor and control lights, and lets Maintenance Staff manage repair tasks.

## Features

- 🗺️ **Live network map** — real-time visual status of every street light (on / off / fault), grouped by zone
- 💡 **Remote control** — turn lights on/off and adjust brightness, with manual override vs. automatic daylight scheduling
- ⏰ **Scheduling** — configure daily on/off windows per zone, with overnight-wrap support
- 🚶 **Motion detection** — simulated motion events boost brightness near active lights
- ⚠️ **Fault detection & alerts** — automatic (simulated) and manual fault reporting, which opens a maintenance task and pushes a notification
- 🛠️ **Maintenance workflow** — assign open faults to staff, track task status (pending → ongoing → completed), and log repair remarks
- 📍 **Fault location lookup** — maintenance staff can see exactly where a faulty light is
- 📜 **Maintenance history** — full record of completed repairs
- ⚡ **Energy consumption tracking** — sampled grid draw over time, charted and summarized
- 📊 **Report generation** — on-demand snapshot of network and maintenance statistics
- 👤 **Role-based access** — separate Admin and Maintenance Staff views, with login and profile self-service

## Project structure

```
.
├── index.html            # Dashboard markup (login screen + app shell)
├── styles.css            # Dark-themed UI styling
├── script.js             # Frontend simulation, rendering, and event logic
│
├── street_light.py        # StreetLight, Location, LightStatus (R3, R4, R8, R9)
├── user.py                 # User, Admin, MaintenanceStaff (R1, login, profile)
├── system.py                # SmartStreetLightingSystem — central facade/controller
├── schedule.py              # LightingSchedule (R7)
├── report.py                 # Report — fault reports (feeds R6)
├── maintenance_task.py        # MaintenanceTask (R11, R12, R14, R15)
├── notification.py             # Notification, NotificationService (R6)
├── energy_log.py                # EnergyLog, EnergyTracker (R10)
└── demo.py                       # Runnable end-to-end walkthrough of the Python model
```

## Requirements coverage

| ID | Requirement | Where it's implemented |
|----|-------------|--------------------------|
| R1 | Login (Admin / Staff) | `user.py` |
| R2 | Monitor street lights | `system.py::get_network_status` |
| R3 | Control street lights | `street_light.py`, `system.py::set_light_power` |
| R4 | Configure brightness level | `street_light.py::dim_light` |
| R5 | Generate reports | `system.py::generate_report` |
| R6 | Send maintenance alerts | `notification.py`, `system.py::report_fault` |
| R7 | Schedule lighting operations | `schedule.py` |
| R8 | Motion detection | `street_light.py::register_motion` |
| R9 | Real-time status update | `system.py::get_network_status` |
| R10 | Energy consumption tracking | `energy_log.py` |
| R11 | View maintenance status | `system.py::get_tasks_for_staff` |
| R12 | Update repair status | `maintenance_task.py::update_status` |
| R13 | View fault location | `system.py::get_light_location` |
| R14 | Maintenance history tracking | `system.py::get_task_history` |
| R15 | Assign maintenance task | `system.py::assign_task` |

## Getting started

### 1. Run the Python domain model

Requires Python 3.9+. No external dependencies.

```bash
python demo.py
```

This walks through the full lifecycle: adding lights, logging in as Admin and Maintenance Staff, scheduling a zone, controlling and dimming a light, registering motion, reporting a fault, assigning and completing the resulting task, sampling energy, and generating a report.

### 2. Run the web dashboard

The dashboard is a static site (`index.html`, `styles.css`, `script.js`) — it needs a local server rather than being opened directly as a `file://` path.

**Using VS Code:**
1. Install the **Live Server** extension.
2. Right-click `index.html` → **Open with Live Server**.

**Using Python:**
```bash
python -m http.server 5500
```
then open `http://localhost:5500`.

**Using Node:**
```bash
npx live-server
```

Once running:
- Log in as **Admin** to monitor the network, control lights, set schedules, assign maintenance tasks, and generate reports.
- Log in as **Maintenance Staff** to view assigned tasks, update repair status, look up fault locations, and review history.
- Use **Report fault** in a light's control panel to manually trigger a fault and test the assignment workflow, or use the **Simulate day cycle** button to let faults, motion, and scheduling happen automatically.

## Tech stack

- **Backend model:** Python (standard library only — `dataclasses`, `enum`, `itertools`, `datetime`)
- **Frontend:** vanilla HTML, CSS, and JavaScript, with [Chart.js](https://www.chartjs.org/) for the energy consumption chart

## Notes

- The web dashboard's login screen accepts any credentials — it's a demo build for exercising the UI, not tied to the Python backend.
- The Python model and the JS dashboard are two independent implementations of the same domain (currently not wired together over an API); see `demo.py` for the Python-only walkthrough.

## License

Add your license of choice here (e.g. MIT).
