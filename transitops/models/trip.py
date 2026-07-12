# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TransitTrip(models.Model):
    """A trip record in TransitOps."""
    _name = 'transit.trip'
    _description = 'Transit Trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Trip Reference', required=True, default='New', copy=False)
    vehicle_id = fields.Many2one('transit.vehicle', string='Vehicle', required=True, tracking=True)
    driver_id = fields.Many2one('transit.driver', string='Driver', required=True, tracking=True)
    origin = fields.Char('Origin', required=True)
    destination = fields.Char('Destination', required=True)
    scheduled_date = fields.Datetime('Scheduled Date', required=True)
    start_date = fields.Datetime('Actual Start')
    end_date = fields.Datetime('Actual End')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    distance_km = fields.Float('Distance (km)')
    odometer_start = fields.Float('Odometer Start (km)')
    odometer_end = fields.Float('Odometer End (km)')
    passengers = fields.Integer('Passengers')
    cargo_weight = fields.Float('Cargo Weight (kg)')
    notes = fields.Text('Notes')
    fuel_ids = fields.One2many('transit.fuel', 'trip_id', string='Fuel Records')

    actual_distance = fields.Float('Actual Distance', compute='_compute_actual_distance', store=True)

    @api.depends('odometer_start', 'odometer_end')
    def _compute_actual_distance(self):
        for rec in self:
            if rec.odometer_end and rec.odometer_start:
                rec.actual_distance = max(0, rec.odometer_end - rec.odometer_start)
            else:
                rec.actual_distance = rec.distance_km or 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('transit.trip') or 'New'
        return super().create(vals_list)
