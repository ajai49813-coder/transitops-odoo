# -*- coding: utf-8 -*-
{
    'name': 'TransitOps',
    'version': '1.0',
    'summary': 'Smart Transport Operations Platform - Trip & Route Management',
    'description': """
TransitOps: Trip & Route Management Module
=========================================
This module enables fleet managers to:
* Create and manage transport routes with detailed stops and total distances.
* Schedule and track transport trips with vehicle and driver allocations.
* Monitor real-time status and trip progression.
* View business intelligence and metrics (Total distance, active/completed trips).
* Advanced Live Tracking features (Latitude, Longitude, Speed, dynamic ETA, and GPS simulation).
* Driver performance statistics and Vehicle utilization metrics.
* PDF report printouts for Trips, Routes, Vehicles distance summary, and Drivers trip history.
    """,
    'author': 'TransitOps Team',
    'category': 'Operations/Transportation',
    'depends': [
        'base',
        'fleet',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/route_views.xml',
        'views/trip_views.xml',
        'views/partner_views.xml',
        'views/vehicle_views.xml',
        'views/report_templates.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
