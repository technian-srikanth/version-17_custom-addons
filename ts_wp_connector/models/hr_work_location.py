from odoo import fields, models
import requests
import logging

_logger = logging.getLogger(__name__)


class HRWorkLocation(models.Model):
    _inherit = "hr.work.location"

    wp_post_id = fields.Char(string="WordPress Job location ID", tracking=True)

    def _sync_location_to_wp(self):
        config = self.env['ir.config_parameter'].sudo()
        username = (config.get_param('wp_username') or "").strip()
        password = (config.get_param('wp_password') or "").strip()
        base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job-location"

        for location in self:

            if location.name:

                data = {
                    "name": location.name,
                }

                # UPDATE
                if location.wp_post_id:
                    print(location.wp_post_id)
                    response = requests.put(
                        f"{base_url}/{int(location.wp_post_id)}",
                        json=data,
                        auth=(username, password)
                    )
                else:
                    response = requests.post(
                        base_url,
                        json=data,
                        auth=(username, password)
                    )

                    if response.status_code in (200, 201):
                        location.wp_post_id = response.json().get("id")

                if response.status_code not in (200, 201):
                    raise Exception(f"WP Error: {response.text}")

    def action_publish_to_wp(self):
        self._sync_location_to_wp()

    def cron_publish_location_to_wp(self):

        loc = self.search([])
        loc._sync_location_to_wp()

    def unlink(self):

        config = self.env['ir.config_parameter'].sudo()
        username = config.get_param('wp_username', '').strip()
        password = config.get_param('wp_password', '').strip()
        base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job-location"

        for loc in self:
            if loc.wp_post_id:
                try:
                    response = requests.delete(
                        f"{base_url}/{int(loc.wp_post_id)}",
                        auth=(username, password),
                        params={'force': True},
                        timeout=30
                    )
                    if response.status_code != 200:
                        _logger.error(f"WP Delete Failed ({response.status_code}): {response.text}")
                    else:
                        _logger.info(f"Successfully deleted WP ID {loc.wp_post_id}")

                except Exception as e:
                    _logger.error(f"Request error for WP ID {loc.wp_post_id}: {e}")

        return super(HRWorkLocation, self).unlink()
