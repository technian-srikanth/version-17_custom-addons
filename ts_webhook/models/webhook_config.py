from odoo import models, fields


class WebhookConfig(models.Model):
    _name = 'webhook.config'
    _description = 'Webhook Config'

    name = fields.Char(required=True)
    url = fields.Text(required=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, ondelete='cascade')
    on_create = fields.Boolean(string='On Create', default=True)
    on_update = fields.Boolean(string='On Update', default=True)
    active = fields.Boolean(default=True)
