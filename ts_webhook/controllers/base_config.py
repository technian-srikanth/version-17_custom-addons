from odoo import api, models
import requests
import logging

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Base, self).create(vals_list)
        # if not self._context.get('skip_webhook'):
        self._process_webhooks(records, 'on_create', data_list=vals_list)
        return records

    def write(self, vals):
        res = super(Base, self).write(vals)
        self._process_webhooks(self, 'on_update', data_list=[vals])
        return res

    def _process_webhooks(self, records, trigger_type, data_list=None):
        webhooks = self.env['webhook.config'].sudo().search([
            ('model_id.model', '=', self._name),
            (trigger_type, '=', True),
            ('active', '=', True)
        ])

        if not webhooks:
            return

        for record, payload in zip(records, data_list):
            full_payload = dict(payload)
            full_payload['id'] = record.id

            for hook in webhooks:
                try:
                    requests.post(
                        hook.url,
                        json=full_payload,
                        timeout=5
                    )
                except Exception as e:
                    _logger.error(f"Webhook failed for {self._name} ID {record.id}: {e}")
