# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import random

class TransportTrip(models.Model):
    _name = 'transport.trip'
    _description = 'Transport Trip'
    _order = 'departure_time desc, id desc'

    trip_id = fields.Char(
        string='Trip ID',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: '/'
    )
    name = fields.Char(string='Trip Name', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('res.partner', string='Driver', required=True)
    route_id = fields.Many2one('transport.route', string='Route', required=True)
    start_location = fields.Char(string='Start Location')
    end_location = fields.Char(string='End Location')
    departure_time = fields.Datetime(string='Departure Time')
    expected_arrival_time = fields.Datetime(string='Expected Arrival Time')
    actual_arrival_time = fields.Datetime(string='Actual Arrival Time', readonly=True)
    distance = fields.Float(string='Distance (km)', digits=(16, 2))
    current_location = fields.Char(string='Current Location')
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True, copy=False)

    # Advanced coordinates tracking
    current_latitude = fields.Float(string='Current Latitude', digits=(10, 7), default=0.0)
    current_longitude = fields.Float(string='Current Longitude', digits=(10, 7), default=0.0)
    last_updated_time = fields.Datetime(string='Last Updated Time')
    speed = fields.Float(string='Speed (km/h)', default=0.0, help="Current vehicle speed")
    eta = fields.Datetime(string='ETA', compute='_compute_eta', store=True, help="Estimated Arrival Time")
    tracking_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('simulated', 'Simulated')
    ], string='Tracking Status', default='inactive')

    # Distance completed and stop tracking
    distance_completed = fields.Float(string='Distance Completed (km)', digits=(16, 2), default=0.0)
    current_stop_id = fields.Many2one('transport.route.stop', string='Current Stop', domain="[('route_id', '=', route_id)]")
    
    remaining_stops = fields.Integer(string='Remaining Stops', compute='_compute_trip_stops')
    distance_covered = fields.Float(string='Distance Covered (km)', compute='_compute_trip_stops', digits=(16, 2))
    remaining_distance = fields.Float(string='Remaining Distance (km)', compute='_compute_trip_stops', digits=(16, 2))

    # Computed progress bar
    progress = fields.Float(string='Progress Percentage', compute='_compute_progress', store=True, group_operator="avg")

    # Color for Kanban cards (Green=10, Blue=4, Orange=3, Red=1)
    color = fields.Integer(string='Color Index', compute='_compute_color_index')

    # --- Onchanges ---
    @api.onchange('route_id')
    def _onchange_route_id(self):
        """Automatically set start, end locations, and distance when route is selected."""
        if self.route_id:
            self.start_location = self.route_id.source
            self.end_location = self.route_id.destination
            self.distance = self.route_id.total_distance
            if not self.name or self.name == 'New Trip':
                self.name = f"Trip - {self.route_id.name}"

    # --- Computes ---
    @api.depends('status', 'distance', 'distance_completed')
    def _compute_progress(self):
        """Compute progress percentage based on trip status and completed distance."""
        for record in self:
            if record.status == 'scheduled' or record.status == 'cancelled':
                record.progress = 0.0
            elif record.status == 'completed':
                record.progress = 100.0
            else:
                if record.distance > 0.0:
                    pct = (record.distance_completed / record.distance) * 100.0
                    record.progress = min(max(pct, 0.0), 100.0)
                else:
                    record.progress = 0.0

    @api.depends('status')
    def _compute_color_index(self):
        """Assign color coding for views: Green -> 10, Blue -> 4, Orange -> 3, Red -> 1."""
        for record in self:
            if record.status == 'completed':
                record.color = 10
            elif record.status == 'in_progress':
                record.color = 4
            elif record.status == 'scheduled':
                record.color = 3
            elif record.status == 'cancelled':
                record.color = 1
            else:
                record.color = 0

    @api.depends('departure_time', 'speed', 'progress', 'distance', 'status', 'actual_arrival_time')
    def _compute_eta(self):
        """Dynamically compute ETA based on current coordinates, speed, and departure time."""
        for record in self:
            if record.status == 'completed':
                record.eta = record.actual_arrival_time
            elif record.status == 'in_progress' and record.departure_time:
                remaining_dist = record.distance * (1.0 - (record.progress / 100.0))
                if record.speed > 0.0:
                    hours_remaining = remaining_dist / record.speed
                    record.eta = record.departure_time + timedelta(hours=hours_remaining)
                else:
                    # Fallback to route travel time adjusted for progress
                    route_time = record.route_id.estimated_travel_time or 2.0
                    hours_remaining = route_time * (1.0 - (record.progress / 100.0))
                    record.eta = record.departure_time + timedelta(hours=hours_remaining)
            else:
                record.eta = False

    @api.depends('route_id', 'current_stop_id', 'distance_completed', 'distance')
    def _compute_trip_stops(self):
        """Compute total stops completed, remaining stops, and distance measurements."""
        for record in self:
            if record.route_id:
                stops = record.route_id.stop_ids.sorted(key=lambda s: s.sequence)
                if record.current_stop_id:
                    record.remaining_stops = len(stops.filtered(lambda s: s.sequence > record.current_stop_id.sequence))
                else:
                    record.remaining_stops = len(stops)
            else:
                record.remaining_stops = 0
            
            record.distance_covered = record.distance_completed
            record.remaining_distance = max(record.distance - record.distance_completed, 0.0)

    # --- Validations (Constraints) ---
    @api.constrains('departure_time', 'expected_arrival_time')
    def _check_expected_arrival_time(self):
        """Constraint: Expected Arrival must be after Departure Time."""
        for record in self:
            if record.departure_time and record.expected_arrival_time:
                if record.expected_arrival_time <= record.departure_time:
                    raise ValidationError("Expected Arrival Time must be after Departure Time.")

    @api.constrains('progress')
    def _check_progress_range(self):
        """Constraint: Progress must remain between 0 and 100."""
        for record in self:
            if record.progress < 0.0 or record.progress > 100.0:
                raise ValidationError("Progress Percentage must be between 0 and 100.")

    @api.constrains('status', 'actual_arrival_time')
    def _check_completed_trip_arrival(self):
        """Constraint: Completed trips must have Actual Arrival."""
        for record in self:
            if record.status == 'completed' and not record.actual_arrival_time:
                raise ValidationError("A completed trip must have an Actual Arrival Time recorded.")

    # --- Action Buttons / Workflow ---
    def action_start(self):
        """Start Trip: Move status to 'in_progress' and set departure time."""
        for record in self:
            if record.status != 'scheduled':
                raise UserError("You can only start a scheduled trip.")
            vals = {
                'status': 'in_progress',
                'tracking_status': 'active',
                'last_updated_time': fields.Datetime.now()
            }
            if not record.departure_time:
                vals['departure_time'] = fields.Datetime.now()
            record.write(vals)

    def action_complete(self):
        """Complete Trip: Move status to 'completed', record arrival, set progress to 100%."""
        for record in self:
            if record.status != 'in_progress':
                raise UserError("You cannot complete a trip unless it has started and is In Progress.")
            
            # Map current stop to last stop on route if any
            last_stop = False
            if record.route_id and record.route_id.stop_ids:
                last_stop = record.route_id.stop_ids.sorted(key=lambda s: s.sequence)[-1]
            
            vals = {
                'status': 'completed',
                'actual_arrival_time': fields.Datetime.now(),
                'distance_completed': record.distance,
                'tracking_status': 'inactive',
                'speed': 0.0,
            }
            if last_stop:
                vals['current_stop_id'] = last_stop.id
            record.write(vals)

    def action_cancel(self):
        """Cancel Trip."""
        for record in self:
            record.write({
                'status': 'cancelled',
                'tracking_status': 'inactive',
                'speed': 0.0,
            })

    def action_reset(self):
        """Reset Trip to Scheduled."""
        for record in self:
            record.write({
                'status': 'scheduled',
                'actual_arrival_time': False,
                'distance_completed': 0.0,
                'tracking_status': 'inactive',
                'current_stop_id': False,
                'speed': 0.0,
            })

    def action_simulate_movement(self):
        """
        Simulate real-time GPS movement and coordinates updating for Hackathon demo.
        Advances coordinates towards destination, updates speed, distance completed, and logs ETA.
        """
        for record in self:
            if record.status != 'in_progress':
                raise UserError("Movement simulation is only available for trips that are currently In Progress.")
            
            record.tracking_status = 'simulated'
            record.last_updated_time = fields.Datetime.now()

            # Assign default coordinates if empty (centered on New York coordinates for simulation)
            if not record.current_latitude or record.current_latitude == 0.0:
                record.current_latitude = 40.7128
                record.current_longitude = -74.0060

            # Advance coordinates slightly
            record.current_latitude += random.uniform(0.005, 0.02)
            record.current_longitude += random.uniform(0.005, 0.02)

            # Pick next stop in route sequence if applicable
            if record.route_id and record.route_id.stop_ids:
                stops = record.route_id.stop_ids.sorted(key=lambda s: s.sequence)
                if not record.current_stop_id:
                    record.current_stop_id = stops[0].id
                else:
                    current_idx = stops.ids.index(record.current_stop_id.id)
                    if current_idx < len(stops) - 1:
                        record.current_stop_id = stops[current_idx + 1].id

            # Increment distance completed
            step_distance = random.uniform(2.0, 5.0)
            record.distance_completed = min(record.distance_completed + step_distance, record.distance)
            record.speed = random.uniform(45.0, 75.0)

            # Auto-complete trip if target distance is reached
            if record.distance_completed >= record.distance:
                record.action_complete()

    # --- Create Overrides (Sequence Allocation) ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('trip_id', '/') == '/':
                vals['trip_id'] = self.env['ir.sequence'].next_by_code('transport.trip') or '/'
        return super(TransportTrip, self).create(vals_list)

    # --- Dashboard Statistics ---
    @api.model
    def get_dashboard_stats(self):
        """
        Calculates computed dashboard stats.
        Returns total trips, active trips, active vehicles on route, available drivers, average ETA, and total distance today.
        """
        trips = self.search([])
        active_trips = trips.filtered(lambda t: t.status == 'in_progress')
        completed_trips = trips.filtered(lambda t: t.status == 'completed')
        
        # Vehicles currently running on the route
        active_vehicles = active_trips.mapped('vehicle_id')
        
        # Available Drivers: drivers who are NOT in an active/in_progress trip
        all_drivers = trips.mapped('driver_id')
        active_drivers = active_trips.mapped('driver_id')
        available_drivers = all_drivers - active_drivers

        # Average ETA in hours (time difference from now to ETA)
        now = fields.Datetime.now()
        eta_diffs = []
        for trip in active_trips:
            if trip.eta and trip.eta > now:
                eta_diffs.append((trip.eta - now).total_seconds() / 3600.0)
        avg_eta = sum(eta_diffs) / len(eta_diffs) if eta_diffs else 0.0

        # Total distance covered today
        today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_trips = completed_trips.filtered(lambda t: t.actual_arrival_time >= today_start and t.actual_arrival_time < today_end)
        total_dist_today = sum(today_trips.mapped('distance'))

        return {
            'total_trips': len(trips),
            'active_trips': len(active_trips),
            'vehicles_on_route': len(active_vehicles),
            'drivers_available': len(available_drivers),
            'average_eta': avg_eta,
            'total_distance_today': total_dist_today,
        }
