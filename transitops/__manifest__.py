# -*- coding: utf-8 -*-
{
    'name': 'TransitOps',
    'version': '17.0.1.0.0',
    'summary': 'Smart Transport Operations Platform',
    'description': 'Fleet management, trip scheduling, driver allocation, fuel monitoring, and analytics.',
    'category': 'Transportation',
    'author': 'TransitOps Team',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/vehicle_views.xml',
        'views/driver_views.xml',
        'views/trip_views.xml',
        'views/fuel_views.xml',
        'views/maintenance_views.xml',
        'views/notification_views.xml',
        'views/dashboard_views.xml',
        'views/reports_views.xml',
        'reports/report.xml',
        'reports/report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'transitops/static/src/css/dashboard.css',
            'transitops/static/src/xml/dashboard_templates.xml',
            'transitops/static/src/js/dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
