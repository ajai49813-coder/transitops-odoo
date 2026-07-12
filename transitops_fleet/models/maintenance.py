# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TransitMaintenance(models.Model):
    """
    Maintenance record for a fleet vehicle.
    Tracks service history, costs, garage details, and upcoming service dates.
    """
    _name = 'transit.maintenance'
    _description = 'Vehicle Maintenance Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc'
    _rec_name = 'reference'

    # ─── Reference ────────────────────────────────────────────────────────────

    reference = fields.Char(
        string='Maintenance ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Auto-generated unique maintenance reference',
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
    service_type = fields.Selection(
        selection=[
            ('oil_change', 'Oil Change'),
            ('tire_rotation', 'Tire Rotation / Replacement'),
            ('brake_service', 'Brake Service'),
            ('engine_overhaul', 'Engine Overhaul'),
            ('transmission', 'Transmission Service'),
            ('electrical', 'Electrical Repair'),
            ('ac_service', 'AC Service'),
            ('body_repair', 'Body Repair'),
            ('general', 'General Service'),
            ('other', 'Other'),
        ],
        string='Service Type',
        required=True,
        tracking=True,
    )
    service_date = fields.Date(
        string='Service Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    next_service_date = fields.Date(
        string='Next Service Date',
        tracking=True,
    )
    garage_name = fields.Char(string='Garage Name')
    mechanic_name = fields.Char(string='Mechanic Name')
    cost = fields.Float(
        string='Maintenance Cost',
        digits=(16, 2),
        tracking=True,
    )
    description = fields.Text(string='Description / Work Done')

    # ─── Status ───────────────────────────────────────────────────────────────

    status = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='scheduled',
        required=True,
        tracking=True,
    )

    # ─── Computed: Overdue Flag ───────────────────────────────────────────────

    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue',
        store=True,
        help='True when next service date has passed and status is not completed/cancelled',
    )

    @api.depends('next_service_date', 'status')
    def _compute_overdue(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_overdue = (
                bool(rec.next_service_date)
                and rec.next_service_date < today
                and rec.status not in ('completed', 'cancelled')
            )

    # ─── Sequence Generation ──────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'transit.maintenance'
                ) or _('New')
        return super().create(vals_list)

    # ─── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('service_date', 'next_service_date')
    def _check_dates(self):
        for rec in self:
            if rec.next_service_date and rec.service_date:
                if rec.next_service_date < rec.service_date:
                    raise ValidationError(
                        _('Next Service Date cannot be earlier than Service Date.')
                    )

    @api.constrains('cost')
    def _check_cost(self):
        for rec in self:
            if rec.cost < 0:
                raise ValidationError(_('Maintenance cost cannot be negative.'))

    # ─── Status Workflow Actions ──────────────────────────────────────────────

    def action_start(self):
        """Mark maintenance as In Progress and update vehicle status."""
        for rec in self:
            rec.status = 'in_progress'
            rec.vehicle_id.status = 'maintenance'

    def action_complete(self):
        """Mark maintenance as Completed and set vehicle back to Available."""
        for rec in self:
            rec.status = 'completed'
            rec.vehicle_id.status = 'available'

    def action_cancel(self):
        rec = self.filtered(lambda r: r.status != 'completed')
        rec.write({'status': 'cancelled'})
