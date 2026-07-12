# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TransitFuel(models.Model):
    """Fuel consumption record for a vehicle/trip."""
    _name = 'transit.fuel'
    _description = 'Transit Fuel Record'
    _rec_name = 'name'

    name = fields.Char('Reference', required=True, default='New', copy=False)
    vehicle_id = fields.Many2one('transit.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('transit.driver', string='Driver')
    trip_id = fields.Many2one('transit.trip', string='Trip')
    date = fields.Date('Date', required=True, default=fields.Date.today)
    quantity_liters = fields.Float('Quantity (L)', required=True)
    cost_per_liter = fields.Float('Cost per Liter')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    odometer_reading = fields.Float('Odometer Reading (km)')
    fuel_station = fields.Char('Fuel Station')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric (kWh)'),
        ('cng', 'CNG'),
    ], string='Fuel Type', default='diesel')
    notes = fields.Text('Notes')

    @api.depends('quantity_liters', 'cost_per_liter')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (rec.quantity_liters or 0.0) * (rec.cost_per_liter or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('transit.fuel') or 'New'
        return super().create(vals_list)
