# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class TransportDashboard(models.Model):
    _name = 'transport.dashboard'
    _description = 'TransitOps Dashboard'

    total_trips = fields.Integer(string='Total Trips', compute='_compute_stats')
    active_trips = fields.Integer(string='Active Trips', compute='_compute_stats')
    completed_trips = fields.Integer(string='Completed Trips', compute='_compute_stats')
    cancelled_trips = fields.Integer(string='Cancelled Trips', compute='_compute_stats')
    
    vehicles_on_route = fields.Integer(string='Vehicles on Route', compute='_compute_stats')
    drivers_available = fields.Integer(string='Drivers Available', compute='_compute_stats')
    
    total_distance_covered = fields.Float(string='Distance Covered (km)', compute='_compute_stats', digits=(16, 2))
    average_eta = fields.Float(string='Average ETA (hours)', compute='_compute_stats', digits=(16, 2))

    # Utilization ratios
    driver_utilization_ratio = fields.Float(string='Driver Utilization Rate (%)', compute='_compute_stats', digits=(16, 2))
    vehicle_utilization_ratio = fields.Float(string='Vehicle Utilization Rate (%)', compute='_compute_stats', digits=(16, 2))
    cancelled_trip_ratio = fields.Float(string='Cancelled Trips Rate (%)', compute='_compute_stats', digits=(16, 2))

    active_trip_ids = fields.Many2many('transport.trip', string='Active Trips Monitoring', compute='_compute_active_trips')

    def _compute_stats(self):
        """Compute live system statistics for dashboard KPI cards."""
        for rec in self:
            trips = self.env['transport.trip'].search([])
            active = trips.filtered(lambda t: t.status == 'in_progress')
            completed = trips.filtered(lambda t: t.status == 'completed')
            cancelled = trips.filtered(lambda t: t.status == 'cancelled')

            rec.total_trips = len(trips)
            rec.active_trips = len(active)
            rec.completed_trips = len(completed)
            rec.cancelled_trips = len(cancelled)
            
            active_vehicles = active.mapped('vehicle_id')
            rec.vehicles_on_route = len(active_vehicles)
            
            all_drivers = trips.mapped('driver_id')
            active_drivers = active.mapped('driver_id')
            available_drivers = all_drivers - active_drivers
            rec.drivers_available = len(available_drivers)
            
            rec.total_distance_covered = sum(completed.mapped('distance'))

            # Average ETA hours from now
            now = fields.Datetime.now()
            eta_diffs = []
            for trip in active:
                if trip.eta and trip.eta > now:
                    eta_diffs.append((trip.eta - now).total_seconds() / 3600.0)
            rec.average_eta = sum(eta_diffs) / len(eta_diffs) if eta_diffs else 0.0

            # Compute utilization percentages
            total_drivers_count = len(self.env['res.partner'].search([('trip_ids', '!=', False)]))
            total_vehicles_count = len(self.env['fleet.vehicle'].search([]))
            
            rec.driver_utilization_ratio = (len(active_drivers) / total_drivers_count * 100.0) if total_drivers_count > 0 else 0.0
            rec.vehicle_utilization_ratio = (len(active_vehicles) / total_vehicles_count * 100.0) if total_vehicles_count > 0 else 0.0
            rec.cancelled_trip_ratio = (len(cancelled) / len(trips) * 100.0) if len(trips) > 0 else 0.0

    def _compute_active_trips(self):
        """Fetch all active (in-progress) trips."""
        for rec in self:
            rec.active_trip_ids = self.env['transport.trip'].search([('status', '=', 'in_progress')])

    @api.model
    def action_open_dashboard(self):
        """Action method to retrieve or create the single dashboard record and display its form."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})
        return {
            'name': 'TransitOps Live Operations Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'transport.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'current',
            'context': {'create': False, 'edit': False, 'delete': False},
        }
