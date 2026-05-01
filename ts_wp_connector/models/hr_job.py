import requests
from odoo import models, fields
from bs4 import BeautifulSoup
import logging

_logger = logging.getLogger(__name__)


class HrJob(models.Model):
    _inherit = "hr.job"

    #wordpress job publish id
    website_job_id = fields.Char(string="WordPress Job ID", tracking=True)

    #multiple job location for one job position
    work_location_id = fields.Many2many('hr.work.location', string='Work Location')

    #tasks and responsibilities
    role_line_ids = fields.One2many("hr.job.line", string="Tasks and Responsibilities",
                                                 inverse_name="job_id")
    #skills and qualifications
    job_requirement_ids = fields.One2many("hr.job.requirement.line", string="Skills and Qualifications",
                                                inverse_name="job_id")

    def _sync_jobs_to_wp(self):

        config = self.env['ir.config_parameter'].sudo()
        username = (config.get_param('wp_username') or "").strip()
        password = (config.get_param('wp_password') or "").strip()
        # base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job"
        base_url = (config.get_param('wp_job_api') or "").strip()

        for job in self:

            if job.description and job.name:

                raw_desc = job.description
                soup = BeautifulSoup(raw_desc, "html.parser")

                for tag in soup.find_all(True):
                    for attr in list(tag.attrs):
                        if attr.startswith("data-"):
                            del tag.attrs[attr]

                if not soup.find("p"):
                    lines = [l.strip() for l in raw_desc.split("\n") if l.strip()]
                    html_content = "".join(f"<p>{l}</p>" for l in lines)
                else:
                    html_content = str(soup)

                wp_status = "publish" if job.website_published else "draft"

                data = {
                    "title": job.name,
                    "content": html_content,
                    "status": wp_status,

                }

                acf_data = {}

                if job.role_line_ids:
                    acf_data["job_tasks_and_responsibilities"] = [
                        {"task_and_responsibility": x.roles_id.name}
                        for x in job.role_line_ids
                    ]

                if job.job_requirement_ids:
                    acf_data["job_skills_and_qualifications"] = [
                        {"skill_and_qualification": x.requirement_id.name}
                        for x in job.job_requirement_ids
                    ]
                if job.no_of_recruitment:
                    acf_data["job_openings"] = str(job.no_of_recruitment)

                if acf_data:
                    data["acf"] = acf_data

                if job.department_id and job.department_id.wp_department_id:
                    data["job-type"] = [int(job.department_id.wp_department_id)]

                if job.work_location_id:
                    data["job-location"] = [
                        int(loc.wp_location_id)
                        for loc in job.work_location_id
                        if loc.wp_location_id
                    ]

                # UPDATE
                if job.website_job_id:
                    response = requests.put(
                        f"{base_url}/{int(job.website_job_id)}",
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
                        job.website_job_id = response.json().get("id")

                if response.status_code not in (200, 201):
                    raise Exception(f"WP Error: {response.text}")

    def action_publish_to_wp(self):
        self._sync_jobs_to_wp()

    def cron_publish_jobs_to_wp(self):

        jobs = self.search([])
        jobs._sync_jobs_to_wp()

    def unlink(self):
        config = self.env['ir.config_parameter'].sudo()
        username = config.get_param('wp_username', '').strip()
        password = config.get_param('wp_password', '').strip()
        # base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job"
        base_url = (config.get_param('wp_job_api') or "").strip()


        _logger.info("Starting unlink process for %s records", len(self))

        for job in self:
            if job.website_job_id:
                wp_id = int(job.website_job_id)
                _logger.info("Attempting to delete WP Post ID: %s", wp_id)

                try:
                    response = requests.delete(
                        f"{base_url}/{wp_id}",
                        auth=(username, password),
                        params={'force': False},
                        timeout=15
                    )

                    if response.status_code == 200:
                        _logger.info("Successfully trashed WP ID: %s", wp_id)
                    else:
                        _logger.warning("WP ID %s not deleted. Status: %s | Response: %s",
                                        wp_id, response.status_code, response.text)

                except requests.exceptions.Timeout:
                    _logger.error("Timeout: WordPress site took too long to respond for ID %s", wp_id)
                except Exception as e:
                    _logger.error("Unexpected error for WP ID %s: %s", wp_id, e)
            else:
                _logger.info("Odoo record %s has no website_job_id, skipping WP deletion", job.id)

        return super(HrJob, self).unlink()

