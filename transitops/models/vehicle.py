# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    trip_ids = fields.One2many('transport.trip', 'vehicle_id', string='Trips')

    total_trips = fields.Integer(string='Total Trips', compute='_compute_vehicle_stats')
    total_distance = fields.Float(string='Total Distance Covered (km)', compute='_compute_vehicle_stats', digits=(16, 2))
    running_hours = fields.Float(string='Running Hours (Hours)', compute='_compute_vehicle_stats', digits=(16, 2))
    average_daily_usage = fields.Float(string='Average Daily Distance (km/day)', compute='_compute_vehicle_stats', digits=(16, 2))

    def _compute_vehicle_stats(self):
        """Calculate trip metrics and utilization stats for the vehicle."""
        for vehicle in self:
            trips = vehicle.trip_ids
            vehicle.total_trips = len(trips)
            
            completed = trips.filtered(lambda t: t.status == 'completed')
            vehicle.total_distance = sum(completed.mapped('distance'))
            
            # Running hours
            total_duration_hours = 0.0
            for trip in completed:
                if trip.departure_time and trip.actual_arrival_time:
                    duration = trip.actual_arrival_time - trip.departure_time
                    total_duration_hours += duration.total_seconds() / 3600.0
            vehicle.running_hours = total_duration_hours
            
            # Average Daily Usage (km/day) based on active days range
            if completed:
                departure_dates = completed.mapped('departure_time')
                min_date = min(departure_dates).date()
                max_date = max(departure_dates).date()
                days = (max_date - min_date).days + 1
                vehicle.average_daily_usage = vehicle.total_distance / days if days > 0 else vehicle.total_distance
            else:
                vehicle.average_daily_usage = 0.0

    def action_view_trips(self):
        """Action for smart button to view all trips related to this vehicle."""
        self.ensure_one()
        return {
            'name': f"Trips - Vehicle {self.license_plate or self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'transport.trip',
            'view_mode': 'tree,kanban,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
