# -*- coding: utf-8 -*-
{
    'name': 'TransitOps – Fleet Management',
    'version': '18.0.2.0.0',
    'category': 'Transport/Fleet',
    'summary': 'Enterprise Fleet Management – Vehicles, Maintenance, Fuel, Documents & Reports',
    'author': 'TransitOps Team',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web'],
    'data': [
        # 1. Security first
        'security/security.xml',
        'security/ir.model.access.csv',
        # 2. Views before actions (actions reference view IDs)
        'views/vehicle_views.xml',
        'views/maintenance_views.xml',
        'views/fuel_views.xml',
        'views/vehicle_document_views.xml',
        'views/dashboard_views.xml',
        # 3. Actions after views
        'views/actions.xml',
        # 4. Menus last (menus reference action IDs)
        'views/menus.xml',
        # 5. Reports
        'reports/report_actions.xml',
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
    'installable': True,
    'application': True,
    'auto_install': False,
}
