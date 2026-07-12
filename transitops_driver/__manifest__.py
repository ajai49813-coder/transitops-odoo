# -*- coding: utf-8 -*-
{
    'name': 'TransitOps - Driver Management',
    'version': '18.0.1.0.0',
    'category': 'Transportation',
    'summary': 'Manage drivers, licenses, and vehicle assignments for TransitOps.',
    'author': 'TransitOps',
    'depends': ['base', 'mail', 'transitops_vehicle'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/driver_views.xml',
        'views/vehicle_extension_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
