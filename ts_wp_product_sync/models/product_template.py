import requests

from odoo import fields, models


class WPProduct(models.Model):
    _inherit = 'product.template'

    wp_product_id = fields.Integer(string="wordpress Product ID")

    def _sync_products_from_wp(self):
        config = self.env['ir.config_parameter'].sudo()
        username = (config.get_param('wp_username') or "").strip()
        password = (config.get_param('wp_password') or "").strip()
        base_url = (config.get_param('wp_product_api') or "").strip()

        response = requests.get(base_url, auth=(username, password))

        if response.status_code == 200:
            data = response.json()

            for product in data:
                wp_id = product.get('id')
                name = product.get('title', {}).get('rendered', '')

                existing = self.search([('wp_product_id', '=', wp_id)], limit=1)

                if existing:
                    existing.write({
                        'name': name
                    })
                else:
                    self.create({
                        'name': name,
                        'wp_product_id': wp_id
                    })

    def _cron_sync_products(self):
        self._sync_products_from_wp()
