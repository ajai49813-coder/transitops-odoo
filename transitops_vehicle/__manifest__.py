# -*- coding: utf-8 -*-
{
    'name': 'TransitOps - Vehicle Management',
    'version': '18.0.1.0.0',
    'category': 'Transportation',
    'summary': 'Manage fleet vehicles, specifications, and availability for TransitOps.',
    'author': 'TransitOps',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/vehicle_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
