# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TransitFuel(models.Model):
    """
    Fuel log entry for a fleet vehicle.
    Automatically calculates total cost and fuel efficiency (mileage).
    """
    _name = 'transit.fuel'
    _description = 'Vehicle Fuel Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fuel_date desc'
    _rec_name = 'reference'

    # ─── Reference ────────────────────────────────────────────────────────────

    reference = fields.Char(
        string='Fuel Entry ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )

    # ─── Core Fields ──────────────────────────────────────────────────────────

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle',
        string='Vehicle',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
    )
    fuel_station = fields.Char(string='Fuel Station', tracking=True)
    fuel_date = fields.Date(
        string='Fuel Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    fuel_type = fields.Selection(
        related='vehicle_id.fuel_type',
        string='Fuel Type',
        store=True,
        readonly=True,
        help='Pulled automatically from the vehicle record',
    )
    quantity = fields.Float(
        string='Quantity (Litres)',
        required=True,
        digits=(16, 3),
        tracking=True,
    )
    cost_per_litre = fields.Float(
        string='Cost Per Litre',
        required=True,
        digits=(16, 2),
        tracking=True,
    )
    # ─── Computed: Total Cost ─────────────────────────────────────────────────
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        digits=(16, 2),
        tracking=True,
    )
    odometer_reading = fields.Float(
        string='Odometer Reading (km)',
        required=True,
        digits=(16, 2),
        tracking=True,
        help='Odometer at the time of fuelling',
    )
    # ─── Computed: Mileage (km/L) ─────────────────────────────────────────────
    mileage = fields.Float(
        string='Mileage (km/L)',
        compute='_compute_mileage',
        store=True,
        digits=(16, 2),
        help='Fuel efficiency calculated from previous fuel entry odometer',
    )
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('company_account', 'Company Account'),
        ],
        string='Payment Method',
        default='cash',
    )
    notes = fields.Text(string='Notes')

    # ─── Compute Methods ──────────────────────────────────────────────────────

    @api.depends('quantity', 'cost_per_litre')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.cost_per_litre

    @api.depends('odometer_reading', 'vehicle_id', 'fuel_date')
    def _compute_mileage(self):
        """
        Mileage = (current odometer – previous odometer) / quantity.
        Looks up the most recent prior fuel entry for the same vehicle.
        """
        for rec in self:
            if not rec.vehicle_id or not rec.odometer_reading or not rec.quantity:
                rec.mileage = 0.0
                continue

            prev = self.search(
                [
                    ('vehicle_id', '=', rec.vehicle_id.id),
                    ('odometer_reading', '<', rec.odometer_reading),
                    ('id', '!=', rec.id),
                ],
                order='odometer_reading desc',
                limit=1,
            )
            if prev:
                distance = rec.odometer_reading - prev.odometer_reading
                rec.mileage = distance / rec.quantity if rec.quantity else 0.0
            else:
                rec.mileage = 0.0

    # ─── Sequence Generation ──────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'transit.fuel'
                ) or _('New')
            # Update vehicle odometer if this reading is higher
        records = super().create(vals_list)
        for rec in records:
            if rec.odometer_reading > rec.vehicle_id.odometer:
                rec.vehicle_id.odometer = rec.odometer_reading
        return records

    # ─── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_('Fuel quantity must be greater than zero.'))

    @api.constrains('cost_per_litre')
    def _check_cost(self):
        for rec in self:
            if rec.cost_per_litre <= 0:
                raise ValidationError(_('Cost per litre must be greater than zero.'))

    @api.constrains('odometer_reading', 'vehicle_id')
    def _check_odometer(self):
        for rec in self:
            if rec.odometer_reading < rec.vehicle_id.odometer:
                # Allow equal (same fill-up point) but not less
                if rec.odometer_reading < (rec.vehicle_id.odometer - 1):
                    raise ValidationError(
                        _('Odometer reading (%s km) is less than the vehicle\'s '
                          'current odometer (%s km).')
                        % (rec.odometer_reading, rec.vehicle_id.odometer)
                    )
