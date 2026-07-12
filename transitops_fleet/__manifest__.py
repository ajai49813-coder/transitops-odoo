# -*- coding: utf-8 -*-
{
    'name': 'TransitOps – Fleet Management',
    'version': '18.0.1.0.0',
    'category': 'Transport/Fleet',
    'summary': 'Smart Transport Operations – Fleet, Maintenance & Fuel Management',
    'description': """
        TransitOps Fleet Management Module
        ====================================
        - Vehicle Management (CRUD + Status Tracking)
        - Maintenance Management (Scheduling & History)
        - Fuel Management (Consumption & Cost Tracking)
        - Fleet Dashboard (KPIs, Charts, Alerts)
    """,
    'author': 'TransitOps Team',
    'website': 'https://transitops.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security – always load first
        'security/security.xml',
        'security/ir.model.access.csv',
        # Actions & Menus
        'views/actions.xml',
        'views/menus.xml',
        # Views
        'views/vehicle_views.xml',
        'views/maintenance_views.xml',
        'views/fuel_views.xml',
        'views/dashboard_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
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
