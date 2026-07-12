# -*- coding: utf-8 -*-
"""Extend Transit Vehicle model in Transit Driver module to resolve dependency order."""

from odoo import fields, models


class TransitVehicle(models.Model):
    """Extends the transit.vehicle model to add driver assignments."""

    _inherit = 'transit.vehicle'

    driver_ids = fields.One2many(
        'transit.driver',
        'vehicle_id',
        string='Assigned Drivers',
    )
