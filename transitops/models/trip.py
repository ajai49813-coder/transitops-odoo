# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

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
    progress = fields.Float(string='Progress Percentage', default=0.0, group_operator="avg")
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True, copy=False)

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
            }
            if not record.departure_time:
                vals['departure_time'] = fields.Datetime.now()
            record.write(vals)

    def action_complete(self):
        """Complete Trip: Move status to 'completed', record arrival, set progress to 100%."""
        for record in self:
            # Prevent completing a trip unless it has started (is in_progress)
            if record.status != 'in_progress':
                raise UserError("You cannot complete a trip unless it has started and is In Progress.")
            record.write({
                'status': 'completed',
                'actual_arrival_time': fields.Datetime.now(),
                'progress': 100.0,
            })

    def action_cancel(self):
        """Cancel Trip."""
        for record in self:
            record.write({'status': 'cancelled'})

    def action_reset(self):
        """Reset Trip to Scheduled."""
        for record in self:
            record.write({
                'status': 'scheduled',
                'actual_arrival_time': False,
                'progress': 0.0,
            })

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
        Prepare computed stats suitable for display on a custom dashboard.
        Returns a dictionary of total, active, completed, cancelled trips, and total distance covered.
        """
        trips = self.search([])
        completed_trips = trips.filtered(lambda t: t.status == 'completed')
        return {
            'total_trips': len(trips),
            'active_trips': len(trips.filtered(lambda t: t.status == 'in_progress')),
            'completed_trips': len(completed_trips),
            'cancelled_trips': len(trips.filtered(lambda t: t.status == 'cancelled')),
            'total_distance_covered': sum(completed_trips.mapped('distance')),
        }
