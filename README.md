# TransitOps — Smart Transport Operations Platform

TransitOps is a complete fleet and transport management module built on **Odoo 17**.  
It covers fleet management, trip scheduling, driver allocation, fuel monitoring, maintenance tracking, real-time analytics, and automated alerts.

---

## Docker Setup (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- No other service using port `8069` or `5432`

### Project layout after Docker files are added

```
transitops-odoo/          ← project root (this folder)
├── transitops/           ← Odoo module (mounted into container)
├── docker-compose.yml
├── odoo.conf
├── .gitignore
└── README.md
```

### 1. Start the environment

Open a terminal in the project root (`transitops-odoo/`) and run:

```bash
docker compose up -d
```

This will:
- Pull `postgres:15` and `odoo:17` images if not already present
- Start a PostgreSQL container (`transitops_db`)
- Start an Odoo 17 container (`transitops_odoo`) on port **8069**
- Mount `./transitops` into the container at `/mnt/extra-addons/transitops`
- Persist database data in the `transitops_db_data` Docker volume
- Persist Odoo filestore in the `transitops_odoo_data` Docker volume

### 2. Open Odoo

Navigate to: **http://localhost:8069**

On first run, Odoo will show the database creation screen.

Fill in:
| Field | Value |
|---|---|
| Master Password | `admin` (default) |
| Database Name | `transitops` |
| Email | `admin@example.com` |
| Password | `admin` |
| Language | English |
| Demo data | ❌ Leave unchecked |

Click **Create database**.

### 3. Install the TransitOps module

After the database is created:

1. Go to **Settings → Activate Developer Mode**  
   (URL shortcut: add `?debug=1` to any page URL)
2. Go to **Apps → Update Apps List** → click **Update**
3. Search for **TransitOps**
4. Click **Install**

### 4. Access the Dashboard

Navigate to **TransitOps → Dashboard** in the top menu.

---

## Docker Commands Reference

### Start containers
```bash
docker compose up -d
```

### Stop containers
```bash
docker compose down
```

### Stop and remove volumes (full reset — deletes all data)
```bash
docker compose down -v
```

### View Odoo logs (live)
```bash
docker logs -f transitops_odoo
```

### View PostgreSQL logs
```bash
docker logs -f transitops_db
```

### Restart only Odoo (after code changes)
```bash
docker compose restart odoo
```

### Upgrade the transitops module
```bash
docker exec transitops_odoo odoo -u transitops -d transitops --stop-after-init
```

Then restart Odoo:
```bash
docker compose restart odoo
```

### Open a shell inside the Odoo container
```bash
docker exec -it transitops_odoo bash
```

### Open a psql shell
```bash
docker exec -it transitops_db psql -U odoo -d transitops
```

---

## Configuration

The `odoo.conf` file is mounted read-only into the container at `/etc/odoo/odoo.conf`.

Key settings:

| Setting | Value |
|---|---|
| `addons_path` | `/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons` |
| `db_host` | `db` (Docker service name) |
| `db_user` | `odoo` |
| `db_password` | `odoo` |
| `http_port` | `8069` |

To override settings locally without affecting git, create `odoo.local.conf` (already in `.gitignore`) and pass it as an additional config.

---

## Module Structure

```
transitops/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── vehicle.py          # transit.vehicle
│   ├── driver.py           # transit.driver
│   ├── trip.py             # transit.trip
│   ├── fuel.py             # transit.fuel
│   ├── maintenance.py      # transit.maintenance
│   ├── notification.py     # transit.notification
│   ├── fuel_analytics.py   # transit.fuel.analytics (AbstractModel)
│   └── dashboard.py        # transit.dashboard (AbstractModel)
├── views/
│   ├── vehicle_views.xml
│   ├── driver_views.xml
│   ├── trip_views.xml
│   ├── fuel_views.xml
│   ├── maintenance_views.xml
│   ├── notification_views.xml
│   ├── dashboard_views.xml  # menus + client action
│   └── reports_views.xml    # pivot/graph/list report views
├── reports/
│   ├── report.xml           # ir.actions.report registrations
│   └── report_templates.xml # QWeb PDF templates
├── security/
│   └── ir.model.access.csv
├── data/
│   └── cron.xml             # sequences + daily alert cron
└── static/src/
    ├── js/dashboard.js      # OWL 2 dashboard component
    ├── css/dashboard.css
    └── xml/dashboard_templates.xml
```

---

## Features

### 1. Dashboard
- OWL 2 client-action component (`transitops_dashboard`)
- 10 KPI cards — each clickable to navigate to the relevant model list
- All data fetched dynamically from `transit.dashboard.get_kpis()`

**KPI Cards:**
| Card | Model |
|---|---|
| Total Vehicles | transit.vehicle |
| Active Vehicles | transit.vehicle |
| Total Drivers | transit.driver |
| Total Trips | transit.trip |
| Completed Trips | transit.trip |
| Ongoing Trips | transit.trip |
| Total Fuel Consumed (L) | transit.fuel |
| Total Fuel Cost | transit.fuel |
| Pending Maintenance | transit.maintenance |
| Active Alerts | transit.notification |

### 2. Charts (Chart.js)
All charts load real backend data via `transit.dashboard.get_chart_data()`:

| Chart | Type |
|---|---|
| Fuel Consumption by Month | Bar |
| Fuel Cost by Month | Line |
| Trips by Status | Doughnut |
| Vehicle Usage (Top 10) | Horizontal Bar |
| Fuel Efficiency (km/L) | Bar |
| Monthly Trip Trend | Line |

### 3. Reports
Pivot + Graph + List views for:
- Vehicle Report
- Trip Report
- Fuel Report
- Driver Report
- Maintenance Report

Accessible under **TransitOps → Reports** menu.

### 4. Notifications & Alerts
Model: `transit.notification`

Fields: title, alert_type, severity (info/warning/critical), vehicle, driver, alert_date, status, description.

Alert types auto-generated by cron:
- Insurance expiry (≤30 days → warning, ≤7 days → critical)
- Registration expiry
- Driver license expiry
- Maintenance overdue

### 5. Fuel Analytics
`transit.fuel.analytics` (AbstractModel) computes:
- Total fuel consumed / cost / avg cost per liter
- Per-vehicle fuel breakdown
- Most fuel-efficient vehicle (km/L)
- Monthly fuel usage & expenses

### 6. PDF Reports (QWeb)
Print actions bound to models:
- Vehicle Summary Report
- Trip Summary Report
- Fuel Consumption Report
- Driver Summary Report
- Maintenance Summary Report

Access via the **Print** button on any record.

---

## Manual Installation (without Docker)

1. Copy the `transitops/` folder into your Odoo addons path.
2. Restart the Odoo server.
3. Enable developer mode.
4. Go to **Apps → Update Apps List**.
5. Search for **TransitOps** and click **Install**.

### Module Upgrade (manual)
```bash
./odoo-bin -u transitops -d <your_database>
```

---

## Required Dependencies

- `base`, `mail`, `web` (all standard Odoo modules)
- Chart.js — loaded via Odoo's web assets bundle

---

## How Scheduled Alerts Work

A daily cron job (`cron_transit_generate_alerts`) calls `transit.dashboard.generate_alerts()`.  
It scans:
- Vehicles with `insurance_expiry` or `registration_expiry` within 30 days
- Drivers with `license_expiry` within 30 days
- Maintenance records with `status = pending` and `scheduled_date < today`

Duplicate alerts are suppressed — an alert is only created if no active alert of the same type exists for that vehicle/driver.

Alerts can be resolved via the **Mark Resolved** button or dismissed.

---

## Team

| Member | Module |
|---|---|
| Member 1 | Fleet / Vehicle Management |
| Member 2 | Trip Scheduling |
| Member 3 | Driver & Maintenance |
| Member 4 | Dashboard, Reports & Analytics *(this module)* |
