# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TransitFuel(models.Model):
    """
    Fuel log entry for a fleet vehicle.
    Auto-calculates: total cost, mileage per fill-up,
    average mileage across all entries, and fuel consumption rate.
    """
    _name = 'transit.fuel'
    _description = 'Vehicle Fuel Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fuel_date desc'
    _rec_name = 'reference'

    # ─── Reference ────────────────────────────────────────────────────────────

    reference = fields.Char(
        string='Fuel Entry ID', required=True, copy=False,
        readonly=True, default=lambda self: _('New'),
    )

    # ─── Core Fields ──────────────────────────────────────────────────────────

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle', string='Vehicle',
        required=True, ondelete='cascade', tracking=True, index=True,
    )
    fuel_station = fields.Char(string='Fuel Station', tracking=True)
    fuel_date = fields.Date(
        string='Fuel Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    fuel_type = fields.Selection(
        related='vehicle_id.fuel_type', string='Fuel Type',
        store=True, readonly=True,
    )
    quantity = fields.Float(
        string='Quantity (Litres)', required=True,
        digits=(16, 3), tracking=True,
    )
    cost_per_litre = fields.Float(
        string='Cost Per Litre', required=True,
        digits=(16, 2), tracking=True,
    )
    odometer_reading = fields.Float(
        string='Odometer Reading (km)', required=True,
        digits=(16, 2), tracking=True,
    )
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Cash'), ('card', 'Card'),
            ('upi', 'UPI'), ('company_account', 'Company Account'),
        ],
        string='Payment Method', default='cash',
    )
    notes = fields.Text(string='Notes')

    # ─── Computed Fields ──────────────────────────────────────────────────────

    total_cost = fields.Float(
        string='Total Cost', compute='_compute_total_cost',
        store=True, digits=(16, 2), tracking=True,
    )
    mileage = fields.Float(
        string='Mileage (km/L)', compute='_compute_mileage',
        store=True, digits=(16, 2),
        help='Fuel efficiency for this fill-up vs previous odometer',
    )
    avg_mileage = fields.Float(
        string='Avg Mileage (km/L)', compute='_compute_avg_mileage',
        digits=(16, 2),
        help='Average mileage across all fuel entries for this vehicle',
    )
    fuel_consumption = fields.Float(
        string='Fuel Consumption (L/100km)', compute='_compute_fuel_consumption',
        digits=(16, 2),
        help='Litres consumed per 100 km (inverse of mileage)',
    )

    @api.depends('quantity', 'cost_per_litre')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.quantity * rec.cost_per_litre

    @api.depends('odometer_reading', 'vehicle_id', 'quantity')
    def _compute_mileage(self):
        """
        Mileage (km/L) = distance since last fill-up / quantity filled.
        Finds the previous fuel entry by odometer reading.
        """
        for rec in self:
            if not rec.vehicle_id or not rec.odometer_reading or not rec.quantity:
                rec.mileage = 0.0
                continue
            prev = self.search(
                [('vehicle_id', '=', rec.vehicle_id.id),
                 ('odometer_reading', '<', rec.odometer_reading),
                 ('id', '!=', rec.id)],
                order='odometer_reading desc', limit=1,
            )
            if prev:
                distance = rec.odometer_reading - prev.odometer_reading
                rec.mileage = distance / rec.quantity if rec.quantity else 0.0
            else:
                rec.mileage = 0.0

    @api.depends('vehicle_id')
    def _compute_avg_mileage(self):
        """Average mileage = total distance / total fuel for the vehicle."""
        for rec in self:
            if not rec.vehicle_id:
                rec.avg_mileage = 0.0
                continue
            all_entries = self.search(
                [('vehicle_id', '=', rec.vehicle_id.id),
                 ('mileage', '>', 0)],
            )
            if all_entries:
                rec.avg_mileage = sum(all_entries.mapped('mileage')) / len(all_entries)
            else:
                rec.avg_mileage = 0.0

    @api.depends('mileage')
    def _compute_fuel_consumption(self):
        """Fuel consumption in L/100km = 100 / mileage."""
        for rec in self:
            rec.fuel_consumption = (100.0 / rec.mileage) if rec.mileage else 0.0

    # ─── Sequence ─────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('transit.fuel')
                    or _('New')
                )
        records = super().create(vals_list)
        # Keep vehicle odometer in sync with latest reading
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
            if rec.odometer_reading < (rec.vehicle_id.odometer - 1):
                raise ValidationError(
                    _('Odometer reading (%s km) is less than the vehicle\'s '
                      'current odometer (%s km).')
                    % (rec.odometer_reading, rec.vehicle_id.odometer)
                )
