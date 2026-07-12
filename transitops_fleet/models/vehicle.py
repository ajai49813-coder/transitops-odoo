# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class TransitVehicle(models.Model):
    """
    Core vehicle model for TransitOps Fleet Management.
    Tracks complete vehicle lifecycle: registration, compliance,
    assignment, maintenance history, fuel logs, and documents.
    """
    _name = 'transit.vehicle'
    _description = 'Fleet Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    _rec_name = 'name'

    # ─── Identity ─────────────────────────────────────────────────────────────

    name = fields.Char(
        string='Vehicle Name', required=True, tracking=True,
        help='Display name e.g. "City Bus 01"',
    )
    vehicle_number = fields.Char(
        string='Vehicle Number', required=True, copy=False, tracking=True,
        help='Internal fleet number assigned by the company',
    )
    registration_number = fields.Char(
        string='Registration Number', required=True, copy=False, tracking=True,
    )
    chassis_number = fields.Char(
        string='Chassis Number', copy=False, tracking=True,
    )
    engine_number = fields.Char(
        string='Engine Number', copy=False, tracking=True,
    )

    # ─── Classification ───────────────────────────────────────────────────────

    vehicle_type = fields.Selection(
        selection=[
            ('bus', 'Bus'), ('minibus', 'Mini Bus'), ('van', 'Van'),
            ('truck', 'Truck'), ('car', 'Car'),
            ('motorcycle', 'Motorcycle'), ('other', 'Other'),
        ],
        string='Vehicle Type', required=True, tracking=True,
    )
    brand = fields.Char(string='Brand', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    color = fields.Char(string='Color', tracking=True)
    manufacturing_year = fields.Integer(string='Manufacturing Year', tracking=True)
    purchase_date = fields.Date(string='Purchase Date', tracking=True)
    capacity = fields.Integer(
        string='Capacity (Seats)',
        help='Maximum passenger or load capacity',
    )
    fuel_type = fields.Selection(
        selection=[
            ('petrol', 'Petrol'), ('diesel', 'Diesel'), ('cng', 'CNG'),
            ('electric', 'Electric'), ('hybrid', 'Hybrid'), ('lpg', 'LPG'),
        ],
        string='Fuel Type', required=True, tracking=True,
    )
    odometer = fields.Float(
        string='Current Odometer (km)', tracking=True,
        help='Latest odometer reading in kilometres',
    )
    vehicle_image = fields.Image(
        string='Vehicle Image', max_width=1024, max_height=1024,
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
        string='Status', default='available', required=True, tracking=True,
    )

    # ─── Compliance Documents ─────────────────────────────────────────────────

    insurance_number = fields.Char(string='Insurance Number', copy=False)
    insurance_expiry = fields.Date(string='Insurance Expiry Date', tracking=True)

    pollution_cert_number = fields.Char(string='Pollution Certificate Number', copy=False)
    pollution_cert_expiry = fields.Date(string='Pollution Certificate Expiry', tracking=True)

    rc_number = fields.Char(string='RC Number', copy=False, tracking=True)
    rc_expiry = fields.Date(string='RC Expiry Date', tracking=True)

    # ─── Computed: Age & Expiry Days ──────────────────────────────────────────

    vehicle_age = fields.Integer(
        string='Vehicle Age (Years)',
        compute='_compute_vehicle_age',
        store=True,
        help='Calculated from manufacturing year',
    )
    insurance_days_left = fields.Integer(
        string='Insurance Days Left',
        compute='_compute_expiry_days',
    )
    pollution_days_left = fields.Integer(
        string='Pollution Cert Days Left',
        compute='_compute_expiry_days',
    )
    rc_days_left = fields.Integer(
        string='RC Days Left',
        compute='_compute_expiry_days',
    )
    insurance_alert = fields.Boolean(
        string='Insurance Expiry Alert',
        compute='_compute_expiry_days',
        store=True,
        help='True when insurance expires within 30 days',
    )
    pollution_alert = fields.Boolean(
        string='Pollution Expiry Alert',
        compute='_compute_expiry_days',
        store=True,
    )

    # ─── Relationships ────────────────────────────────────────────────────────

    driver_id = fields.Many2one(
        comodel_name='res.partner',
        string='Assigned Driver',
        domain=[('is_company', '=', False)],
        tracking=True,
    )
    # Placeholder for transit.trip integration (managed by Trip team)
    current_trip_id = fields.Many2one(
        comodel_name='res.partner',
        string='Current Trip',
        help='Replace comodel with transit.trip when Trip module is available',
    )
    maintenance_ids = fields.One2many(
        comodel_name='transit.maintenance', inverse_name='vehicle_id',
        string='Maintenance Records',
    )
    fuel_ids = fields.One2many(
        comodel_name='transit.fuel', inverse_name='vehicle_id',
        string='Fuel Records',
    )
    document_ids = fields.One2many(
        comodel_name='transit.vehicle.document', inverse_name='vehicle_id',
        string='Documents',
    )

    # ─── Computed Counts & Costs ──────────────────────────────────────────────

    maintenance_count = fields.Integer(compute='_compute_counts')
    fuel_count = fields.Integer(compute='_compute_counts')
    document_count = fields.Integer(compute='_compute_counts')
    total_maintenance_cost = fields.Float(
        string='Total Maintenance Cost', compute='_compute_costs', digits=(16, 2),
    )
    total_fuel_cost = fields.Float(
        string='Total Fuel Cost', compute='_compute_costs', digits=(16, 2),
    )

    # ─── Compute Methods ──────────────────────────────────────────────────────

    @api.depends('manufacturing_year')
    def _compute_vehicle_age(self):
        current_year = date.today().year
        for rec in self:
            rec.vehicle_age = (
                current_year - rec.manufacturing_year
                if rec.manufacturing_year else 0
            )

    @api.depends('insurance_expiry', 'pollution_cert_expiry', 'rc_expiry')
    def _compute_expiry_days(self):
        today = date.today()
        for rec in self:
            # Insurance
            if rec.insurance_expiry:
                days = (rec.insurance_expiry - today).days
                rec.insurance_days_left = days
                rec.insurance_alert = days <= 30
            else:
                rec.insurance_days_left = 0
                rec.insurance_alert = False

            # Pollution certificate
            if rec.pollution_cert_expiry:
                days = (rec.pollution_cert_expiry - today).days
                rec.pollution_days_left = days
                rec.pollution_alert = days <= 30
            else:
                rec.pollution_days_left = 0
                rec.pollution_alert = False

            # RC
            rec.rc_days_left = (
                (rec.rc_expiry - today).days if rec.rc_expiry else 0
            )

    @api.depends('maintenance_ids', 'fuel_ids', 'document_ids')
    def _compute_counts(self):
        for rec in self:
            rec.maintenance_count = len(rec.maintenance_ids)
            rec.fuel_count = len(rec.fuel_ids)
            rec.document_count = len(rec.document_ids)

    @api.depends('maintenance_ids.cost', 'fuel_ids.total_cost')
    def _compute_costs(self):
        for rec in self:
            rec.total_maintenance_cost = sum(rec.maintenance_ids.mapped('cost'))
            rec.total_fuel_cost = sum(rec.fuel_ids.mapped('total_cost'))

    # ─── SQL Constraints ──────────────────────────────────────────────────────

    _sql_constraints = [
        ('vehicle_number_unique', 'UNIQUE(vehicle_number)',
         'Vehicle Number must be unique.'),
        ('registration_number_unique', 'UNIQUE(registration_number)',
         'Registration Number must be unique.'),
        ('chassis_number_unique', 'UNIQUE(chassis_number)',
         'Chassis Number must be unique.'),
        ('engine_number_unique', 'UNIQUE(engine_number)',
         'Engine Number must be unique.'),
    ]

    # ─── Python Constraints ───────────────────────────────────────────────────

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

    @api.constrains('insurance_expiry')
    def _check_insurance_expiry(self):
        today = date.today()
        for rec in self:
            if rec.insurance_expiry and rec.insurance_expiry < today:
                raise ValidationError(
                    _('Insurance expiry date cannot be in the past.')
                )

    @api.constrains('pollution_cert_expiry')
    def _check_pollution_expiry(self):
        today = date.today()
        for rec in self:
            if rec.pollution_cert_expiry and rec.pollution_cert_expiry < today:
                raise ValidationError(
                    _('Pollution certificate expiry date cannot be in the past.')
                )

    # ─── Smart Button Actions ─────────────────────────────────────────────────

    def action_view_maintenance(self):
        """Open maintenance records filtered for this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Records'),
            'res_model': 'transit.maintenance',
            'view_mode': 'list,form,calendar',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_fuel(self):
        """Open fuel records filtered for this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fuel Records'),
            'res_model': 'transit.fuel',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_documents(self):
        """Open documents filtered for this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicle Documents'),
            'res_model': 'transit.vehicle.document',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    # ─── Status Workflow ──────────────────────────────────────────────────────

    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})

    def action_set_out_of_service(self):
        self.write({'status': 'out_of_service'})
