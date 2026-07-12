# -*- coding: utf-8 -*-
from odoo import models, fields

class TransportRoute(models.Model):
    _name = 'transport.route'
    _description = 'Transport Route'
    _order = 'name'

    route_id = fields.Char(string='Route ID', required=True, copy=False, index=True)
    name = fields.Char(string='Route Name', required=True)
    source = fields.Char(string='Source', required=True)
    destination = fields.Char(string='Destination', required=True)
    stops = fields.Text(string='Stops')
    total_distance = fields.Float(string='Total Distance (km)', digits=(16, 2), help="Distance in kilometers")
    estimated_travel_time = fields.Float(string='Estimated Travel Time (Hours)', digits=(16, 2), help="Travel time in hours")
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('route_id_uniq', 'unique(route_id)', 'The Route ID must be unique!'),
    ]
