# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TransitMaintenance(models.Model):
    """
    Maintenance record for a fleet vehicle.
    Tracks service history, costs, garage details, upcoming service dates,
    and automatically creates activity reminders for approaching services.
    """
    _name = 'transit.maintenance'
    _description = 'Vehicle Maintenance Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc'
    _rec_name = 'reference'

    # ─── Reference ────────────────────────────────────────────────────────────

    reference = fields.Char(
        string='Maintenance ID', required=True, copy=False,
        readonly=True, default=lambda self: _('New'),
    )

    # ─── Core Fields ──────────────────────────────────────────────────────────

    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle', string='Vehicle',
        required=True, ondelete='cascade', tracking=True, index=True,
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
        string='Service Type', required=True, tracking=True,
    )
    service_date = fields.Date(
        string='Service Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    next_service_date = fields.Date(string='Next Service Date', tracking=True)
    garage_name = fields.Char(string='Garage Name')
    mechanic_name = fields.Char(string='Mechanic Name')
    cost = fields.Float(string='Maintenance Cost', digits=(16, 2), tracking=True)
    description = fields.Text(string='Description / Work Done')

    # ─── Status ───────────────────────────────────────────────────────────────

    status = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status', default='scheduled', required=True, tracking=True,
    )

    # ─── Computed ─────────────────────────────────────────────────────────────

    is_overdue = fields.Boolean(
        string='Overdue', compute='_compute_overdue', store=True,
        help='True when next service date has passed and not completed/cancelled',
    )
    days_until_service = fields.Integer(
        string='Days Until Next Service',
        compute='_compute_overdue', store=True,
    )

    @api.depends('next_service_date', 'status')
    def _compute_overdue(self):
        today = fields.Date.today()
        for rec in self:
            if rec.next_service_date:
                delta = (rec.next_service_date - today).days
                rec.days_until_service = delta
                rec.is_overdue = (
                    delta < 0 and rec.status not in ('completed', 'cancelled')
                )
            else:
                rec.days_until_service = 0
                rec.is_overdue = False

    # ─── Sequence ─────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('transit.maintenance')
                    or _('New')
                )
        records = super().create(vals_list)
        # Schedule activity reminder if next_service_date is set
        for rec in records:
            rec._schedule_service_reminder()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'next_service_date' in vals:
            for rec in self:
                rec._schedule_service_reminder()
        return result

    # ─── Activity Reminder ────────────────────────────────────────────────────

    def _schedule_service_reminder(self):
        """
        Create a To-Do activity on the vehicle record when next service
        date is within 7 days, so fleet managers get notified in the chatter.
        """
        if not self.next_service_date:
            return
        today = fields.Date.today()
        days_left = (self.next_service_date - today).days
        if 0 <= days_left <= 7 and self.status not in ('completed', 'cancelled'):
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if activity_type:
                self.vehicle_id.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=_('Service Due: %s') % self.reference,
                    note=_('Vehicle %s is due for %s on %s.')
                         % (self.vehicle_id.name,
                            dict(self._fields['service_type'].selection).get(self.service_type),
                            self.next_service_date),
                    date_deadline=self.next_service_date,
                )

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

    # ─── Workflow Actions ─────────────────────────────────────────────────────

    def action_start(self):
        """Mark In Progress and set vehicle to maintenance status."""
        for rec in self:
            rec.status = 'in_progress'
            rec.vehicle_id.status = 'maintenance'

    def action_complete(self):
        """Mark Completed and restore vehicle to available."""
        for rec in self:
            rec.status = 'completed'
            rec.vehicle_id.status = 'available'

    def action_cancel(self):
        self.filtered(lambda r: r.status != 'completed').write({'status': 'cancelled'})
