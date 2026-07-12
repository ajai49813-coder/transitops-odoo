# -*- coding: utf-8 -*-
"""Transit Vehicle model for TransitOps – Smart Transport Operations Platform."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TransitVehicle(models.Model):
    """Represents a vehicle in the fleet for TransitOps."""

    _name = 'transit.vehicle'
    _description = 'Transit Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'license_plate asc'

    # -------------------------------------------------------------------------
    # Core Specifications
    # -------------------------------------------------------------------------
    name = fields.Char(string='Vehicle Name', compute='_compute_name', store=True)
    brand = fields.Selection(
        [
            ('toyota', 'Toyota'),
            ('ford', 'Ford'),
            ('mercedes', 'Mercedes-Benz'),
            ('volvo', 'Volvo'),
            ('scania', 'Scania'),
            ('man', 'MAN'),
            ('other', 'Other'),
        ],
        string='Brand / Manufacturer',
        required=True,
        tracking=True,
    )
    model_name = fields.Char(string='Model', required=True, tracking=True)
    license_plate = fields.Char(string='License Plate', required=True, tracking=True)
    year = fields.Integer(string='Model Year', tracking=True)
    fuel_type = fields.Selection(
        [
            ('gasoline', 'Gasoline'),
            ('diesel', 'Diesel'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
        ],
        string='Fuel Type',
        default='diesel',
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # Status & Drivers
    # -------------------------------------------------------------------------
    status = fields.Selection(
        [
            ('active', 'Active'),
            ('out_of_service', 'Out of Service'),
            ('maintenance', 'Under Maintenance'),
        ],
        string='Status',
        default='active',
        tracking=True,
    )
    active = fields.Boolean(string='Active', default=True)


    # -------------------------------------------------------------------------
    # Computed Fields
    # -------------------------------------------------------------------------
    @api.depends('brand', 'model_name', 'license_plate')
    def _compute_name(self):
        for rec in self:
            brand_label = dict(self._fields['brand'].selection).get(rec.brand, '') if rec.brand else ''
            model = rec.model_name or ''
            plate = rec.license_plate or ''
            rec.name = f"[{plate}] {brand_label} {model}".strip()

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains('license_plate')
    def _check_unique_license_plate(self):
        for rec in self:
            if rec.license_plate:
                duplicate = self.search([
                    ('license_plate', '=', rec.license_plate),
                    ('id', '!=', rec.id),
                ])
                if duplicate:
                    raise ValidationError(
                        f"A vehicle with license plate '{rec.license_plate}' already exists."
                    )
