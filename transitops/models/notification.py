# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TransitNotification(models.Model):
    """Alert and notification model for TransitOps."""
    _name = 'transit.notification'
    _description = 'Transit Notification'
    _inherit = ['mail.thread']
    _rec_name = 'title'
    _order = 'alert_date desc, id desc'

    title = fields.Char('Alert Title', required=True)
    alert_type = fields.Selection([
        ('low_fuel', 'Low Fuel'),
        ('high_fuel_consumption', 'High Fuel Consumption'),
        ('maintenance_due', 'Maintenance Due'),
        ('insurance_expiry', 'Insurance Expiry'),
        ('vehicle_doc_expiry', 'Vehicle Document Expiry'),
        ('driver_license_expiry', 'Driver License Expiry'),
        ('general', 'General'),
        ('fuel_anomaly', 'Fuel Anomaly'),
    ], string='Alert Type', required=True)
    description = fields.Text('Description')
    vehicle_id = fields.Many2one('transit.vehicle', string='Related Vehicle')
    driver_id = fields.Many2one('transit.driver', string='Related Driver')
    alert_date = fields.Datetime('Alert Date', default=fields.Datetime.now, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ], string='Status', default='active', tracking=True)
    severity = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Severity', default='info', required=True)
    resolved_date = fields.Datetime('Resolved Date')
    resolved_by = fields.Many2one('res.users', string='Resolved By')

    def action_resolve(self):
        self.write({
            'status': 'resolved',
            'resolved_date': fields.Datetime.now(),
            'resolved_by': self.env.uid,
        })

    def action_dismiss(self):
        self.write({'status': 'dismissed'})

    @api.model
    def get_active_count(self):
        return self.search_count([('status', '=', 'active')])
