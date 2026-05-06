from odoo import fields, models, api
import requests
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wp_post_id = fields.Integer(string='Engage4more ID')

    @api.model
    def _sync_products_from_eng4more(self):
        url = "https://engage4more.com/api/v1.1/cards/?ordering=priority_order&page=1&category__id=23"
        existing_products = {rec.wp_post_id: rec for rec in self.search([('wp_post_id', '!=', False)])}
        while url:
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                for item in data.get("results", []):
                    wp_id = item.get("id")
                    name = item.get("name")
                    title = item.get("title")
                    if not wp_id:
                        continue
                    vals = {
                        'name': name,
                        'wp_post_id': wp_id,
                    }
                    product = existing_products.get(wp_id)
                    if product:
                        product.write({
                            'name': name,
                            'description': title,
                        })
                    else:
                        new_product = self.create(vals)
                        existing_products[wp_id] = new_product

                url = data.get("next")
            except Exception as e:
                _logger.exception("Sync Failed: %s", str(e))
                break