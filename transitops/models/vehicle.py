# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TransitVehicle(models.Model):
    """Fleet vehicle managed by TransitOps."""
    _name = 'transit.vehicle'
    _description = 'Transit Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Vehicle Name', required=True, tracking=True)
    license_plate = fields.Char('License Plate', required=True, tracking=True)
    vehicle_type = fields.Selection([
        ('bus', 'Bus'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
    ], string='Type', default='bus', required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    ], string='Status', default='active', tracking=True)
    make = fields.Char('Make')
    model = fields.Char('Model')
    year = fields.Integer('Year')
    color = fields.Char('Color')
    capacity = fields.Integer('Capacity (seats/tons)')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
    ], string='Fuel Type', default='diesel')
    odometer = fields.Float('Current Odometer (km)', tracking=True)
    insurance_expiry = fields.Date('Insurance Expiry', tracking=True)
    registration_expiry = fields.Date('Registration Expiry', tracking=True)
    driver_id = fields.Many2one('transit.driver', string='Assigned Driver')
    trip_ids = fields.One2many('transit.trip', 'vehicle_id', string='Trips')
    fuel_ids = fields.One2many('transit.fuel', 'vehicle_id', string='Fuel Records')
    maintenance_ids = fields.One2many('transit.maintenance', 'vehicle_id', string='Maintenance Records')
    notes = fields.Text('Notes')

    trip_count = fields.Integer('Trip Count', compute='_compute_trip_count')
    fuel_count = fields.Integer('Fuel Records', compute='_compute_fuel_count')

    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for rec in self:
            rec.trip_count = len(rec.trip_ids)

    @api.depends('fuel_ids')
    def _compute_fuel_count(self):
        for rec in self:
            rec.fuel_count = len(rec.fuel_ids)