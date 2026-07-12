# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class TransitVehicle(models.Model):
    """
    Core vehicle model for TransitOps Fleet Management.
    Tracks all vehicle details, documents, status, and relationships
    to drivers, trips, maintenance records, and fuel logs.
    """
    _name = 'transit.vehicle'
    _description = 'Fleet Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    _rec_name = 'name'

    # ─── Basic Information ────────────────────────────────────────────────────

    name = fields.Char(
        string='Vehicle Name',
        required=True,
        tracking=True,
        help='Display name for the vehicle (e.g. "City Bus 01")',
    )
    vehicle_number = fields.Char(
        string='Vehicle Number',
        required=True,
        copy=False,
        tracking=True,
        help='Internal fleet number assigned by the company',
    )
    registration_number = fields.Char(
        string='Registration Number',
        required=True,
        copy=False,
        tracking=True,
        help='Government-issued vehicle registration plate number',
    )
    vehicle_type = fields.Selection(
        selection=[
            ('bus', 'Bus'),
            ('minibus', 'Mini Bus'),
            ('van', 'Van'),
            ('truck', 'Truck'),
            ('car', 'Car'),
            ('motorcycle', 'Motorcycle'),
            ('other', 'Other'),
        ],
        string='Vehicle Type',
        required=True,
        tracking=True,
    )
    brand = fields.Char(string='Brand', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    manufacturing_year = fields.Integer(
        string='Manufacturing Year',
        tracking=True,
    )
    capacity = fields.Integer(
        string='Capacity (Seats)',
        help='Maximum passenger or load capacity',
    )
    fuel_type = fields.Selection(
        selection=[
            ('petrol', 'Petrol'),
            ('diesel', 'Diesel'),
            ('cng', 'CNG'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('lpg', 'LPG'),
        ],
        string='Fuel Type',
        required=True,
        tracking=True,
    )
    odometer = fields.Float(
        string='Current Odometer (km)',
        tracking=True,
        help='Latest odometer reading in kilometres',
    )
    vehicle_image = fields.Image(
        string='Vehicle Image',
        max_width=1024,
        max_height=1024,
    )
    notes = fields.Text(string='Notes')

    # ─── Status ───────────────────────────────────────────────────────────────

    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('assigned', 'Assigned'),
            ('on_trip', 'On Trip'),
            ('maintenance', 'Under Maintenance'),
            ('out_of_service', 'Out of Service'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )

    # ─── Insurance & Compliance ───────────────────────────────────────────────

    insurance_number = fields.Char(string='Insurance Number', copy=False)
    insurance_expiry = fields.Date(
        string='Insurance Expiry Date',
        tracking=True,
    )
    pollution_cert_number = fields.Char(
        string='Pollution Certificate Number',
        copy=False,
    )
    pollution_cert_expiry = fields.Date(
        string='Pollution Certificate Expiry',
        tracking=True,
    )

    # ─── Computed: Days Until Expiry ──────────────────────────────────────────

    insurance_days_left = fields.Integer(
        string='Insurance Days Left',
        compute='_compute_expiry_days',
        store=False,
    )
    pollution_days_left = fields.Integer(
        string='Pollution Cert Days Left',
        compute='_compute_expiry_days',
        store=False,
    )
    insurance_alert = fields.Boolean(
        string='Insurance Expiry Alert',
        compute='_compute_expiry_days',
        store=False,
        help='True when insurance expires within 30 days',
    )

    # ─── Relationships ────────────────────────────────────────────────────────

    driver_id = fields.Many2one(
        comodel_name='res.partner',
        string='Assigned Driver',
        domain=[('is_company', '=', False)],
        tracking=True,
        help='Driver currently assigned to this vehicle',
    )
    # current_trip_id is a Many2one back-reference; the trip model
    # (managed by the Trip team) should set this field.
    current_trip_id = fields.Many2one(
        comodel_name='res.partner',   # placeholder – replace with transit.trip when available
        string='Current Trip',
        help='Active trip this vehicle is assigned to (managed by Trip module)',
    )
    maintenance_ids = fields.One2many(
        comodel_name='transit.maintenance',
        inverse_name='vehicle_id',
        string='Maintenance Records',
    )
    fuel_ids = fields.One2many(
        comodel_name='transit.fuel',
        inverse_name='vehicle_id',
        string='Fuel Records',
    )

    # ─── Computed Aggregates ──────────────────────────────────────────────────

    maintenance_count = fields.Integer(
        string='Maintenance Count',
        compute='_compute_counts',
    )
    fuel_count = fields.Integer(
        string='Fuel Records',
        compute='_compute_counts',
    )
    total_maintenance_cost = fields.Float(
        string='Total Maintenance Cost',
        compute='_compute_costs',
        digits=(16, 2),
    )
    total_fuel_cost = fields.Float(
        string='Total Fuel Cost',
        compute='_compute_costs',
        digits=(16, 2),
    )

    # ─── Compute Methods ──────────────────────────────────────────────────────

    @api.depends('insurance_expiry', 'pollution_cert_expiry')
    def _compute_expiry_days(self):
        today = date.today()
        for rec in self:
            if rec.insurance_expiry:
                delta = (rec.insurance_expiry - today).days
                rec.insurance_days_left = delta
                rec.insurance_alert = delta <= 30
            else:
                rec.insurance_days_left = 0
                rec.insurance_alert = False

            if rec.pollution_cert_expiry:
                rec.pollution_days_left = (rec.pollution_cert_expiry - today).days
            else:
                rec.pollution_days_left = 0

    @api.depends('maintenance_ids', 'fuel_ids')
    def _compute_counts(self):
        for rec in self:
            rec.maintenance_count = len(rec.maintenance_ids)
            rec.fuel_count = len(rec.fuel_ids)

    @api.depends('maintenance_ids.cost', 'fuel_ids.total_cost')
    def _compute_costs(self):
        for rec in self:
            rec.total_maintenance_cost = sum(rec.maintenance_ids.mapped('cost'))
            rec.total_fuel_cost = sum(rec.fuel_ids.mapped('total_cost'))

    # ─── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('manufacturing_year')
    def _check_manufacturing_year(self):
        current_year = date.today().year
        for rec in self:
            if rec.manufacturing_year and not (1900 <= rec.manufacturing_year <= current_year):
                raise ValidationError(
                    _('Manufacturing year must be between 1900 and %s.') % current_year
                )

    @api.constrains('capacity')
    def _check_capacity(self):
        for rec in self:
            if rec.capacity and rec.capacity < 1:
                raise ValidationError(_('Capacity must be at least 1.'))

    @api.constrains('odometer')
    def _check_odometer(self):
        for rec in self:
            if rec.odometer < 0:
                raise ValidationError(_('Odometer reading cannot be negative.'))

    _sql_constraints = [
        ('vehicle_number_unique', 'UNIQUE(vehicle_number)',
         'Vehicle Number must be unique across the fleet.'),
        ('registration_number_unique', 'UNIQUE(registration_number)',
         'Registration Number must be unique.'),
    ]

    # ─── Smart Buttons ────────────────────────────────────────────────────────

    def action_view_maintenance(self):
        """Open maintenance records for this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Records'),
            'res_model': 'transit.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_fuel(self):
        """Open fuel records for this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fuel Records'),
            'res_model': 'transit.fuel',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    # ─── Status Action Helpers ────────────────────────────────────────────────

    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})

    def action_set_out_of_service(self):
        self.write({'status': 'out_of_service'})
