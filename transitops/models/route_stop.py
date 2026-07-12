# -*- coding: utf-8 -*-
from odoo import models, fields

class TransportRouteStop(models.Model):
    _name = 'transport.route.stop'
    _description = 'Route Stop'
    _order = 'sequence, id'

    route_id = fields.Many2one(
        'transport.route',
        string='Route',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Stop Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    distance_from_start = fields.Float(
        string='Distance from Start (km)',
        digits=(16, 2),
        help="Distance from the route starting location"
    )
