from odoo import fields, models
import requests
import logging

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    wp_post_id = fields.Char(string="WordPress Department ID", tracking=True)

    def _sync_department_to_wp(self):
        config = self.env['ir.config_parameter'].sudo()
        username = (config.get_param('wp_username') or "").strip()
        password = (config.get_param('wp_password') or "").strip()

        base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job-type"
        for department in self:

            if department.name:

                data = {
                    "name": department.name,
                }

                # UPDATE
                if department.wp_post_id:
                    print(department.wp_post_id)
                    response = requests.put(
                        f"{base_url}/{int(department.wp_post_id)}",
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
                        department.wp_post_id = response.json().get("id")

                if response.status_code not in (200, 201):
                    raise Exception(f"WP Error: {response.text}")

    def action_publish_to_wp(self):
        self._sync_department_to_wp()

    def cron_publish_department_to_wp(self):

        departments = self.search([])
        departments._sync_department_to_wp()

    def unlink(self):
        config = self.env['ir.config_parameter'].sudo()
        username = config.get_param('wp_username', '').strip()
        password = config.get_param('wp_password', '').strip()
        base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job-type"

        for department in self:
            if department.wp_post_id:
                try:
                    response = requests.delete(
                        f"{base_url}/{int(department.wp_post_id)}",
                        auth=(username, password),
                        params={'force': True},
                        timeout=60
                    )
                    if response.status_code not in [200, 201]:
                        _logger.error(f"WP Delete Failed ({response.status_code}): {response.text}")
                    else:
                        _logger.info(f"Successfully deleted WP ID {department.wp_post_id}")

                except Exception as e:
                    _logger.error(f"Network error while deleting WP ID {department.wp_post_id}: {e}")

        return super(HrDepartment, self).unlink()
