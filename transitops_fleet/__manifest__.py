# -*- coding: utf-8 -*-
{
    'name': 'TransitOps – Fleet Management',
    'version': '18.0.2.0.0',
    'category': 'Transport/Fleet',
    'summary': 'Enterprise Fleet Management – Vehicles, Maintenance, Fuel, Documents & Reports',
    'description': """
        TransitOps Fleet Management Module v2
        =======================================
        - Vehicle Management (full CRUD + compliance tracking)
        - Maintenance Management (scheduling, workflow, notifications)
        - Fuel Management (consumption, mileage, cost analytics)
        - Vehicle Document Management (insurance, RC, PUC, bills)
        - Fleet Dashboard (KPIs, charts, alerts)
        - QWeb PDF Reports (fleet, vehicle, fuel, maintenance)
    """,
    'author': 'TransitOps Team',
    'website': 'https://transitops.example.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web'],
    'data': [
        # ── Security (always first) ──────────────────────────────
        'security/security.xml',
        'security/ir.model.access.csv',
        # ── Views (must load before actions/menus) ───────────────
        'views/vehicle_views.xml',
        'views/maintenance_views.xml',
        'views/fuel_views.xml',
        'views/vehicle_document_views.xml',
        'views/dashboard_views.xml',
        # ── Actions (Window & Report) ────────────────────────────
        'views/actions.xml',
        'reports/report_actions.xml',
        # ── Menus ────────────────────────────────────────────────
        'views/menus.xml',
        # ── QWeb Report Templates ────────────────────────────────
        'reports/fleet_report.xml',
        'reports/vehicle_report.xml',
        'reports/fuel_report.xml',
        'reports/maintenance_report.xml',
    ],
    'demo': ['demo/demo.xml'],
    'assets': {
        'web.assets_backend': [
            'transitops_fleet/static/src/css/dashboard.css',
            'transitops_fleet/static/src/js/dashboard.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
