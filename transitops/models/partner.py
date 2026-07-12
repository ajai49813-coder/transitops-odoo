# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    trip_ids = fields.One2many('transport.trip', 'driver_id', string='Trips')

    total_trips = fields.Integer(string='Total Trips', compute='_compute_driver_stats')
    completed_trips = fields.Integer(string='Completed Trips', compute='_compute_driver_stats')
    cancelled_trips = fields.Integer(string='Cancelled Trips', compute='_compute_driver_stats')
    average_trip_time = fields.Float(string='Average Trip Time (Hours)', compute='_compute_driver_stats', digits=(16, 2))
    average_distance = fields.Float(string='Average Distance (km)', compute='_compute_driver_stats', digits=(16, 2))

    def _compute_driver_stats(self):
        """Calculate trip statistics and metrics for the driver."""
        for partner in self:
            trips = partner.trip_ids
            partner.total_trips = len(trips)
            
            completed = trips.filtered(lambda t: t.status == 'completed')
            partner.completed_trips = len(completed)
            partner.cancelled_trips = len(trips.filtered(lambda t: t.status == 'cancelled'))
            
            # Average trip distance
            partner.average_distance = sum(completed.mapped('distance')) / len(completed) if completed else 0.0
            
            # Average trip duration in hours
            total_duration_hours = 0.0
            for trip in completed:
                if trip.departure_time and trip.actual_arrival_time:
                    duration = trip.actual_arrival_time - trip.departure_time
                    total_duration_hours += duration.total_seconds() / 3600.0
            partner.average_trip_time = total_duration_hours / len(completed) if completed else 0.0

    def action_view_trips(self):
        """Action for smart button to view all trips related to this driver."""
        self.ensure_one()
        return {
            'name': f"Trips - Driver {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'transport.trip',
            'view_mode': 'tree,kanban,form',
            'domain': [('driver_id', '=', self.id)],
            'context': {'default_driver_id': self.id},
        }
