from odoo import fields, models


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    interview_count = fields.Integer('Interview Count', compute='_compute_interview_count')

    def view_applicant_interviews(self):
        self.ensure_one()
        context = {
            'default_application_id': self.id
        }
        return {
            'name': 'Interviews',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.interview',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': context,
        }

    def _compute_interview_count(self):
        for record in self:
            record.interview_count = self.env['hr.interview'].search_count([
                ('application_id', '=', record.id)
            ])
