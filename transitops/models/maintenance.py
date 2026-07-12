# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TransitMaintenance(models.Model):
    """Vehicle maintenance record."""
    _name = 'transit.maintenance'
    _description = 'Transit Maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Reference', required=True, copy=False)
    vehicle_id = fields.Many2one('transit.vehicle', string='Vehicle', required=True, tracking=True)
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('inspection', 'Inspection'),
        ('emergency', 'Emergency'),
    ], string='Type', default='preventive', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True)
    scheduled_date = fields.Date('Scheduled Date', required=True)
    completed_date = fields.Date('Completed Date')
    description = fields.Text('Description')
    cost = fields.Float('Cost')
    odometer_at_service = fields.Float('Odometer at Service (km)')
    next_service_km = fields.Float('Next Service at (km)')
    next_service_date = fields.Date('Next Service Date')
    technician = fields.Char('Technician')
    notes = fields.Text('Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('transit.maintenance') or 'MAINT/NEW'
        return super().create(vals_list)

    def action_complete(self):
        self.write({'status': 'completed', 'completed_date': fields.Date.today()})

    def action_start(self):
        self.write({'status': 'in_progress'})
