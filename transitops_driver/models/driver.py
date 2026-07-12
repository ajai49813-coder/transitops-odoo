# -*- coding: utf-8 -*-
"""Transit Driver model for TransitOps – Smart Transport Operations Platform."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TransitDriver(models.Model):
    """Represents a driver in the TransitOps platform."""

    _name = 'transit.driver'
    _description = 'Transit Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'driver_id asc'

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    driver_id = fields.Char(
        string='Driver ID',
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
    )
    name = fields.Char(string='Full Name', required=True, tracking=True)
    photo = fields.Image(string='Photo', max_width=256, max_height=256)
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string='Gender',
    )
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=False)
    phone = fields.Char(string='Phone Number', tracking=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    emergency_contact = fields.Char(string='Emergency Contact')
    blood_group = fields.Selection(
        [
            ('a+', 'A+'), ('a-', 'A-'),
            ('b+', 'B+'), ('b-', 'B-'),
            ('ab+', 'AB+'), ('ab-', 'AB-'),
            ('o+', 'O+'), ('o-', 'O-'),
        ],
        string='Blood Group',
    )

    # -------------------------------------------------------------------------
    # License
    # -------------------------------------------------------------------------
    license_number = fields.Char(string='License Number', tracking=True)
    license_type = fields.Selection(
        [
            ('light', 'Light Vehicle'),
            ('heavy', 'Heavy Vehicle'),
            ('commercial', 'Commercial'),
            ('motorcycle', 'Motorcycle'),
        ],
        string='License Type',
    )
    license_issue_date = fields.Date(string='License Issue Date')
    license_expiry_date = fields.Date(string='License Expiry Date', tracking=True)
    license_status = fields.Selection(
        [('active', 'Active'), ('expired', 'Expired'), ('suspended', 'Suspended')],
        string='License Status',
        compute='_compute_license_status',
        store=True,
        tracking=True,
    )
    license_expiry_warning = fields.Boolean(
        string='Expiring Soon',
        compute='_compute_license_status',
        store=True,
    )

    # -------------------------------------------------------------------------
    # Employment & Status
    # -------------------------------------------------------------------------
    driver_status = fields.Selection(
        [
            ('available', 'Available'),
            ('on_trip', 'On Trip'),
            ('on_leave', 'On Leave'),
            ('off_duty', 'Off Duty'),
            ('suspended', 'Suspended'),
        ],
        string='Driver Status',
        default='available',
        tracking=True,
    )
    joining_date = fields.Date(string='Joining Date')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)

    # -------------------------------------------------------------------------
    # Vehicle Assignment
    # -------------------------------------------------------------------------
    vehicle_id = fields.Many2one(
        'transit.vehicle',
        string='Assigned Vehicle',
        tracking=True,
        domain="[('active', '=', True)]",
    )

    # -------------------------------------------------------------------------
    # Computed fields
    # -------------------------------------------------------------------------
    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.date_of_birth:
                rec.age = (
                    today.year - rec.date_of_birth.year
                    - ((today.month, today.day) < (rec.date_of_birth.month, rec.date_of_birth.day))
                )
            else:
                rec.age = 0

    @api.depends('license_expiry_date')
    def _compute_license_status(self):
        today = date.today()
        warning_threshold = today + timedelta(days=30)
        for rec in self:
            if not rec.license_expiry_date:
                rec.license_expiry_warning = False
                # Preserve manually set suspended status
                if rec.license_status != 'suspended':
                    rec.license_status = 'active'
                continue
            if rec.license_expiry_date < today:
                rec.license_status = 'expired'
                rec.license_expiry_warning = False
            elif rec.license_expiry_date <= warning_threshold:
                rec.license_status = 'active'
                rec.license_expiry_warning = True
            else:
                rec.license_status = 'active'
                rec.license_expiry_warning = False

    # -------------------------------------------------------------------------
    # ORM overrides
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('driver_id', 'New') == 'New':
                vals['driver_id'] = self.env['ir.sequence'].next_by_code('transit.driver') or 'New'
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains('license_number')
    def _check_unique_license(self):
        for rec in self:
            if rec.license_number:
                duplicate = self.search([
                    ('license_number', '=', rec.license_number),
                    ('id', '!=', rec.id),
                ])
                if duplicate:
                    raise ValidationError(
                        f"License number '{rec.license_number}' is already assigned to {duplicate[0].name}."
                    )

    @api.constrains('vehicle_id', 'driver_status', 'license_status')
    def _check_vehicle_assignment(self):
        for rec in self:
            if not rec.vehicle_id:
                continue
            if rec.driver_status == 'suspended':
                raise ValidationError(
                    "Cannot assign a vehicle to a suspended driver."
                )
            if rec.license_status == 'expired':
                raise ValidationError(
                    "Cannot assign a vehicle to a driver with an expired license."
                )
            # Ensure no other active record for this driver has the same vehicle
            duplicate = self.search([
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('id', '!=', rec.id),
                ('active', '=', True),
            ])
            if duplicate:
                raise ValidationError(
                    f"Vehicle is already assigned to driver {duplicate[0].name} ({duplicate[0].driver_id})."
                )

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------
    @api.onchange('license_expiry_date')
    def _onchange_license_expiry_date(self):
        if not self.license_expiry_date:
            return
        today = date.today()
        warning_threshold = today + timedelta(days=30)
        if self.license_expiry_date < today:
            return {
                'warning': {
                    'title': 'License Expired',
                    'message': 'The license expiry date has already passed. License status will be set to Expired.',
                }
            }
        if self.license_expiry_date <= warning_threshold:
            return {
                'warning': {
                    'title': 'License Expiring Soon',
                    'message': f'The license will expire on {self.license_expiry_date}. Please renew it soon.',
                }
            }

    @api.onchange('driver_status')
    def _onchange_driver_status(self):
        if self.driver_status == 'suspended' and self.vehicle_id:
            self.vehicle_id = False
            return {
                'warning': {
                    'title': 'Vehicle Unassigned',
                    'message': 'The vehicle assignment has been removed because the driver is suspended.',
                }
            }
