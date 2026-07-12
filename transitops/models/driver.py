# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date


class TransitDriver(models.Model):
    """Driver employed by TransitOps."""
    _name = 'transit.driver'
    _description = 'Transit Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Full Name', required=True, tracking=True)
    employee_id = fields.Char('Employee ID')
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    license_number = fields.Char('License Number', tracking=True)
    license_expiry = fields.Date('License Expiry', tracking=True)
    license_class = fields.Selection([
        ('a', 'Class A'),
        ('b', 'Class B'),
        ('c', 'Class C'),
        ('d', 'Class D'),
    ], string='License Class')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('suspended', 'Suspended'),
    ], string='Status', default='active', tracking=True)
    date_hired = fields.Date('Date Hired')
    address = fields.Text('Address')
    vehicle_id = fields.Many2one('transit.vehicle', string='Assigned Vehicle')
    trip_ids = fields.One2many('transit.trip', 'driver_id', string='Trips')
    notes = fields.Text('Notes')

    trip_count = fields.Integer('Trip Count', compute='_compute_trip_count')
    license_days_left = fields.Integer('License Days Left', compute='_compute_license_days')

    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for rec in self:
            rec.trip_count = len(rec.trip_ids)

    @api.depends('license_expiry')
    def _compute_license_days(self):
        today = date.today()
        for rec in self:
            if rec.license_expiry:
                rec.license_days_left = (rec.license_expiry - today).days
            else:
                rec.license_days_left = 0
