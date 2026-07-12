# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TransportRoute(models.Model):
    _name = 'transport.route'
    _description = 'Transport Route'
    _order = 'name'

    route_id = fields.Char(string='Route ID', required=True, copy=False, index=True)
    name = fields.Char(string='Route Name', required=True)
    source = fields.Char(string='Source', required=True)
    destination = fields.Char(string='Destination', required=True)
    stops = fields.Text(string='Stops Description')
    total_distance = fields.Float(string='Total Distance (km)', digits=(16, 2), help="Distance in kilometers")
    estimated_travel_time = fields.Float(string='Estimated Travel Time (Hours)', digits=(16, 2), help="Travel time in hours")
    active = fields.Boolean(string='Active', default=True)

    # Advanced route stop and visualization fields
    stop_ids = fields.One2many('transport.route.stop', 'route_id', string='Route Stops')
    
    total_stops = fields.Integer(string='Total Stops', compute='_compute_route_viz')
    remaining_stops = fields.Integer(string='Remaining Stops', compute='_compute_route_viz')
    distance_covered = fields.Float(string='Distance Covered (km)', compute='_compute_route_viz', digits=(16, 2))
    remaining_distance = fields.Float(string='Remaining Distance (km)', compute='_compute_route_viz', digits=(16, 2))

    # Smart button counter fields
    trip_count = fields.Integer(string='Total Trips Count', compute='_compute_trip_counts')
    completed_trip_count = fields.Integer(string='Completed Trips Count', compute='_compute_trip_counts')
    cancelled_trip_count = fields.Integer(string='Cancelled Trips Count', compute='_compute_trip_counts')

    _sql_constraints = [
        ('route_id_uniq', 'unique(route_id)', 'The Route ID must be unique!'),
    ]

    @api.depends('stop_ids', 'total_distance')
    def _compute_route_viz(self):
        """Calculate stops and distance metrics based on the active trip running on this route."""
        for route in self:
            route.total_stops = len(route.stop_ids)
            # Find the first active trip on this route
            active_trip = self.env['transport.trip'].search([
                ('route_id', '=', route.id),
                ('status', '=', 'in_progress')
            ], limit=1)
            
            if active_trip:
                route.distance_covered = active_trip.distance_completed
                route.remaining_distance = max(route.total_distance - active_trip.distance_completed, 0.0)
                if active_trip.current_stop_id:
                    route.remaining_stops = len(route.stop_ids.filtered(lambda s: s.sequence > active_trip.current_stop_id.sequence))
                else:
                    route.remaining_stops = len(route.stop_ids)
            else:
                route.distance_covered = 0.0
                route.remaining_distance = route.total_distance
                route.remaining_stops = len(route.stop_ids)

    def _compute_trip_counts(self):
        """Calculate counts of all, completed, and cancelled trips for smart buttons."""
        for route in self:
            trips = self.env['transport.trip'].search([('route_id', '=', route.id)])
            route.trip_count = len(trips)
            route.completed_trip_count = len(trips.filtered(lambda t: t.status == 'completed'))
            route.cancelled_trip_count = len(trips.filtered(lambda t: t.status == 'cancelled'))

    # Smart button action methods
    def action_view_trips(self):
        self.ensure_one()
        return {
            'name': f"Trips for Route {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'transport.trip',
            'view_mode': 'tree,kanban,form',
            'domain': [('route_id', '=', self.id)],
            'context': {'default_route_id': self.id},
        }

    def action_view_completed_trips(self):
        self.ensure_one()
        return {
            'name': f"Completed Trips for Route {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'transport.trip',
            'view_mode': 'tree,kanban,form',
            'domain': [('route_id', '=', self.id), ('status', '=', 'completed')],
            'context': {'default_route_id': self.id, 'default_status': 'completed'},
        }

    def action_view_cancelled_trips(self):
        self.ensure_one()
        return {
            'name': f"Cancelled Trips for Route {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'transport.trip',
            'view_mode': 'tree,kanban,form',
            'domain': [('route_id', '=', self.id), ('status', '=', 'cancelled')],
            'context': {'default_route_id': self.id, 'default_status': 'cancelled'},
        }
