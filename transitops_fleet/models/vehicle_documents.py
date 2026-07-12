# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TransitVehicleDocument(models.Model):
    """
    Document store for a fleet vehicle.
    Supports insurance copies, RC, PUC, service bills, invoices,
    and any other vehicle-related files. Files are stored as binary
    attachments and can be downloaded directly from the form view.
    """
    _name = 'transit.vehicle.document'
    _description = 'Vehicle Document'
    _inherit = ['mail.thread']
    _order = 'document_date desc'
    _rec_name = 'name'

    # ─── Core Fields ──────────────────────────────────────────────────────────

    name = fields.Char(
        string='Document Name', required=True, tracking=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name='transit.vehicle', string='Vehicle',
        required=True, ondelete='cascade', tracking=True, index=True,
    )
    document_type = fields.Selection(
        selection=[
            ('insurance', 'Insurance Copy'),
            ('rc', 'Registration Certificate (RC)'),
            ('puc', 'Pollution Certificate (PUC)'),
            ('service_bill', 'Service Bill'),
            ('invoice', 'Invoice'),
            ('permit', 'Permit'),
            ('fitness', 'Fitness Certificate'),
            ('other', 'Other'),
        ],
        string='Document Type', required=True, tracking=True,
    )
    document_date = fields.Date(
        string='Document Date', default=fields.Date.today, tracking=True,
    )
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    document_number = fields.Char(string='Document Number', copy=False)

    # ─── File Attachment ──────────────────────────────────────────────────────

    file = fields.Binary(
        string='Upload File', attachment=True,
        help='Upload PDF, image, or any document file',
    )
    file_name = fields.Char(string='File Name')
    file_size = fields.Integer(
        string='File Size (bytes)', compute='_compute_file_size',
    )

    # ─── Status ───────────────────────────────────────────────────────────────

    is_expired = fields.Boolean(
        string='Expired', compute='_compute_is_expired', store=True,
    )
    days_to_expiry = fields.Integer(
        string='Days to Expiry', compute='_compute_is_expired', store=True,
    )
    notes = fields.Text(string='Notes')

    # ─── Compute Methods ──────────────────────────────────────────────────────

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days
                rec.days_to_expiry = delta
                rec.is_expired = delta < 0
            else:
                rec.days_to_expiry = 0
                rec.is_expired = False

    def _compute_file_size(self):
        """Approximate file size from base64 encoded binary length."""
        for rec in self:
            if rec.file:
                # base64 encodes 3 bytes as 4 chars; approximate raw size
                rec.file_size = int(len(rec.file) * 3 / 4)
            else:
                rec.file_size = 0

    # ─── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('file', 'file_name')
    def _check_file_type(self):
        """Allow only PDF and image files for security."""
        allowed = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        for rec in self:
            if rec.file_name:
                ext = rec.file_name.lower()
                if not any(ext.endswith(a) for a in allowed):
                    raise ValidationError(
                        _('Only PDF and image files are allowed. '
                          'Received: %s') % rec.file_name
                    )

    # ─── Download Action ──────────────────────────────────────────────────────

    def action_download(self):
        """Return URL action to download the attached file."""
        self.ensure_one()
        if not self.file:
            raise ValidationError(_('No file attached to this document.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/file/%s?download=true' % (
                self._name, self.id, self.file_name or 'document'
            ),
            'target': 'self',
        }
