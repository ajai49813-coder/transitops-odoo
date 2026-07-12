# 🚌 TransitOps - Smart Transport Operations Platform

[![Odoo Version](https://img.shields.io/badge/Odoo-18.0%20Community%20%2F%20Enterprise-7c5b9e.svg?style=for-the-badge&logo=odoo)](https://www.odoo.com/)
[![License](https://img.shields.io/badge/License-LGPL--3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/lgpl-3.0.html)
[![Hackathon Build](https://img.shields.io/badge/Build-Hackathon%20Premium-orange.svg?style=for-the-badge)](https://github.com/)

**TransitOps** is a modern, premium, and feature-rich Smart Transport Operations Platform built on top of **Odoo 18**. It is designed to optimize route planning, coordinate live vehicle tracking, allocate drivers, monitor vehicle utilizations, and provide business analytics in a sleek SaaS-like experience.

---

## 📖 Table of Contents
- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [The Solution](#-the-solution)
- [Core Features](#-core-features)
- [Screenshots & UI Design](#-screenshots--ui-design)
- [Technology Stack](#-technology-stack)
- [Folder Structure](#-folder-structure)
- [Installation Guide](#-installation-guide)
- [Team Members & Roster](#-team-members--roster)
- [Future Scope](#-future-scope)
- [License](#-license)

---

## 🔍 Project Overview
TransitOps streamlines transit management by connecting vehicles, routes, drivers, and schedules into a unified telemetry ecosystem. Using reactive Odoo APIs, custom stylesheet injections, and automation triggers, the module provides dispatcher and manager control rooms with real-time transit visibility.

## ⚠️ Problem Statement
Modern logistics and passenger transit companies suffer from:
1. **Disconnected Systems**: Siloed route schedules, driver calendars, and vehicle telemetry.
2. **Lack of Live Visibility**: Dispatchers cannot see intermediate trip progression or compute live, speed-based ETAs.
3. **Underutilized Assets**: Inability to calculate daily vehicle mileage, driving hours, and driver performance statistics easily.
4. **Poor User Experience**: Traditional ERP interfaces are complex, lack visual visual aids (colors, progress indicators), and slow down dispatch speed.

## 💡 The Solution
TransitOps solves these issues by presenting a unified transport console:
* **Live GPS Telemetry Simulation**: Allows dispatchers to simulate vehicle transit, tracking speed changes, coordinates, and stops.
* **Asset Analytics & Stats**: Auto-computes driver scores and vehicle utilization metrics.
* **Premium SaaS Dashboard View**: Consolidates telemetry metrics into high-impact color-coded KPI cards and live monitoring grids.
* **Modern Interface**: Custom CSS theme injections provide smooth transitions, border color-codes, badges, and progress bars.

---

## 🚀 Core Features

### 🔀 Route Optimization & Stops
* Manage customizable Routes with Source, Destination, and total distance.
* Add sequential waypoint stops with drag-and-drop sequencing handles (`transport.route.stop`).
* Live Route visualization showing Total Stops, Remaining Stops, Distance Covered, and Remaining Distance.

### 📍 Trip Dispatcher Control & Live GPS Tracking
* Auto-generating custom sequence numbers (`TRIP/YYYY/MM/XXXXX`).
* Set drivers (`res.partner`) and vehicles (`fleet.vehicle`).
* **Live Tracking Console**: Logs Latitude, Longitude, last update timestamp, current speed (km/h), and dynamic remaining-distance ETAs.
* **Movement Simulator**: Simulates vehicle transit, advancing through waypoints and updating speed/ETA dynamically.

### 📊 SaaS Dashboard & Reports
* **Live Operations Dashboard**: Features KPI cards for Active/Completed trips, Distance covered, Available Drivers, and System Utilizations.
* **Analytical Views**: Built-in Odoo Graph, Pivot table, and Calendar views to aggregate mileage and status counts.
* **Printable QWeb PDFs**: Clean templates for Trip Sheets, Route Waypoints, Vehicle Distance Summaries, and Driver History.

---

## 📸 Screenshots & UI Design
*This module features a customized Odoo 18 style scheme:*

| View Mode | Highlight Details |
| :--- | :--- |
| **SaaS Dashboard** | KPI grid blocks, active trip monitoring row, and vertical utilization progress bars. |
| **Trip Kanban** | Drag-and-drop status columns styled with responsive color-coded border cards. |
| **Spaced Form** | Live GPS group block with inline markers (`fa-map-marker`), speed dials, and ribbons. |
| **Interactive List** | Row colored decorations: Completed (Green), In Progress (Blue), Scheduled (Orange), Cancelled (Red). |

---

## 🛠️ Technology Stack
* **Framework**: Odoo 18.0 Community & Enterprise (Python 3.10+ / PostgreSQL 14+)
* **Frontend**: XML Views, QWeb Templates, Bootstrap 5.1/5.2, Font Awesome 4.7 Icons
* **Styling**: Vanilla CSS (Asset bundle overrides in `web.assets_backend`)
* **Testing**: Python Odoo TestCase (`TransactionCase`)

---

## 📂 Folder Structure
```
transitops/
├── __init__.py                # Imports models and tests
├── __manifest__.py            # Registers metadata, assets, data and demo views
├── data/
│   └── sequence.xml           # Trip ID sequence configuration (TRIP/YYYY/MM/NNNNN)
├── demo/
│   └── transitops_demo.xml    # Bulk demo data (20 vehicles, 15 drivers, 12 routes, 50 trips)
├── models/
│   ├── __init__.py            # Model registration imports
│   ├── dashboard.py           # Dashboard KPIs and singleton controller
│   ├── partner.py             # Driver res.partner performance extension
│   ├── route.py               # Route schema, metrics, and smart buttons
│   ├── route_stop.py          # Route stops waypoint model
│   ├── trip.py                # Trip dispatch log, GPS simulation, and progress
│   └── vehicle.py             # Vehicle fleet.vehicle utilization extension
├── security/
│   ├── security.xml           # Groups (TransitOps User, TransitOps Manager)
│   └── ir.model.access.csv    # ACL permissions mapping
├── static/
│   └── src/
│       └── css/
│           └── transitops.css # Custom CSS overrides (Kanban cards hover, progress bars)
├── tests/
│   ├── __init__.py            # Tests importer
│   └── test_trip.py           # Unit tests suite (Simulations, validations, stats)
└── views/
    ├── dashboard_views.xml    # SaaS dashboard view and server action
    ├── menu.xml               # Menuitem nodes hierarchy
    ├── partner_views.xml      # Partner form inheritance (Smart button + stats page)
    ├── report_templates.xml   # QWeb PDF print template designs
    ├── route_views.xml        # Route list, form views and actions
    ├── trip_views.xml         # Trip list, form, Kanban, Calendar, Graph, Pivot views
    └── vehicle_views.xml      # Vehicle form inheritance (Smart button + stats page)
```

---

## ⚙️ Installation Guide

### 1. Prerequisite
Ensure you have Odoo 18 installed with the standard `fleet` module enabled.

### 2. Clone the Repository
Clone the codebase into your custom Odoo addons directory:
```bash
cd /your/odoo/custom/addons/
git clone https://github.com/your-username/transitops-odoo.git
```

### 3. Add to Odoo Addons Path
Add the cloned directory path to your Odoo configuration file (`odoo.conf`):
```ini
addons_path = /path/to/odoo/server/addons,/your/odoo/custom/addons/transitops-odoo
```

### 4. Install Module
1. Start your Odoo Server.
2. Log in to the Database with Developer Mode active.
3. Navigate to **Apps** -> Click **Update Apps List**.
4. Search for `transitops` and click **Activate**.

### 5. Load Demo Data (Optional)
To load the rich demo dataset (50 trips, 20 vehicles, 12 routes), make sure to initialize your Odoo database with **Load demo data** enabled.

---

## 👥 Team Members & Roster
* **Member 1 (Fleet Management)**: Focuses on vehicle logs, servicing, and telemetry hooks.
* **Member 2 (Driver Management)**: Focuses on driver profile parameters, scheduling, and shifts.
* **Member 3 (Trip & Route Management)**: Focuses on route stop allocations, trip dispatching, simulations, SaaS dashboards, and PDF reporting.

---

## 🔮 Future Scope
* **Google Maps/OpenStreetMap Integration**: Embed dynamic mapping view widgets directly in Odoo forms.
* **Mobile Driver App Integration**: Connect native mobile driver applications to push GPS location coordinate updates via IoT REST APIs.
* **AI Route Optimization**: Integrate route pathfinding APIs to re-arrange waypoints sequence automatically depending on traffic telemetry.

---

## 📄 License
TransitOps is distributed under the **LGPL-3** license. Feel free to copy, modify, and distribute the platform.
