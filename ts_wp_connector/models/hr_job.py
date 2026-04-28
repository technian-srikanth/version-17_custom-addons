import requests
from odoo import models, fields
from bs4 import BeautifulSoup


class HrJob(models.Model):
    _inherit = "hr.job"

    wp_post_id = fields.Char(string="WordPress Job ID",tracking=True)
    work_location_id = fields.Many2many('hr.work.location', string='Work Location')
    tasks_responsibilities_ids = fields.One2many("job.task.responsibilities", string="Tasks and Responsibilities",
                                                 inverse_name="job_id")
    skills_qualifications_ids = fields.One2many("job.skills.qualifications", string="Skills and Qualifications",
                                                inverse_name="job_id")

    def _sync_jobs_to_wp(self):
        base_url = "https://staging-9a67-technianscom.wpcomstaging.com/wp-json/wp/v2/job"

        config = self.env['ir.config_parameter'].sudo()
        username = (config.get_param('wp_username') or "").strip()
        password = (config.get_param('wp_password') or "").strip()

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

                if job.tasks_responsibilities_ids:
                    acf_data["job_tasks_and_responsibilities"] = [
                        {"task_and_responsibility": x.name}
                        for x in job.tasks_responsibilities_ids
                    ]

                if job.skills_qualifications_ids:
                    acf_data["job_skills_and_qualifications"] = [
                        {"skill_and_qualification": x.name}
                        for x in job.skills_qualifications_ids
                    ]
                if job.no_of_recruitment:
                    acf_data["job_openings"] = str(job.no_of_recruitment)

                if acf_data:
                    data["acf"] = acf_data

                if job.department_id and job.department_id.wp_post_id:
                    data["job-type"] = [int(job.department_id.wp_post_id)]

                if job.work_location_id:
                    data["job-location"] = [
                        int(loc.wp_post_id)
                        for loc in job.work_location_id
                        if loc.wp_post_id
                    ]

                # UPDATE
                if job.wp_post_id:
                    response = requests.put(
                        f"{base_url}/{int(job.wp_post_id)}",
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
                        job.wp_post_id = response.json().get("id")

                # ERROR HANDLING
                if response.status_code not in (200, 201):
                    raise Exception(f"WP Error: {response.text}")

    def action_publish_to_wp(self):
        self._sync_jobs_to_wp()

    def cron_publish_jobs_to_wp(self):

        jobs = self.search([])
        jobs._sync_jobs_to_wp()


class HrJobResponsibilities(models.Model):
    _name = "job.task.responsibilities"

    name = fields.Text(string="Description")
    job_id = fields.Many2one("hr.job", string="Job")


class HRSkillsQualifications(models.Model):
    _name = "job.skills.qualifications"

    name = fields.Text(string="Description")
    job_id = fields.Many2one("hr.job", string="Job")
