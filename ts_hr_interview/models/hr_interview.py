from odoo import models, fields, api
from datetime import timedelta


class HrInterview(models.Model):
    _name = 'hr.interview'
    _rec_name = 'name'
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    name = fields.Char(string="Name")
    application_id = fields.Many2one('hr.applicant', "Application")
    start_date = fields.Datetime(string="Start Date")

    email_from = fields.Char(related="application_id.email_from")

    stage_id = fields.Selection(
        [
            ('new', "New"),
            ('today', "Today"),
            ('this_week', "This Week"),
            ('next_week', "Next Week"),
            ('up_coming', "Up Coming"),
        ],
        string="Stage",
        default='new',
        index=True,
        group_expand='_group_expand_stage'
    )

    @api.onchange('application_id')
    def _onchange_application_id(self):
        for rec in self:
            if rec.application_id:
                rec.name = rec.application_id.partner_name or rec.application_id.name

    def _get_stage(self):
        self.ensure_one()

        today = fields.Date.today()

        if not self.start_date:
            return 'new'

        start_date = fields.Date.to_date(self.start_date)

        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        start_of_next_week = end_of_week + timedelta(days=1)
        end_of_next_week = start_of_next_week + timedelta(days=6)

        if start_date == today:
            return 'today'
        elif start_of_week <= start_date <= end_of_week:
            return 'this_week'
        elif start_of_next_week <= start_date <= end_of_next_week:
            return 'next_week'
        elif start_date > end_of_next_week:
            return 'up_coming'

    @api.model
    def create(self, vals):

        if vals.get('start_date'):
            dummy = self.new(vals)
            vals['stage_id'] = dummy._get_stage()
        else:
            vals['stage_id'] = 'new'

        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'start_date' in vals:
                rec.stage_id = rec._get_stage()
        return res

    @api.model
    def _group_expand_stage(self, stages, domain, order):
        return ['new', 'today', 'this_week', 'next_week', 'up_coming']

    def view_application(self):
        self.ensure_one()
        return {
            'name': 'Application',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.application_id.id)],
            'context': {
                'create': False,
            },
        }

    @api.model
    def _cron_update_stage(self):
        records = self.search([('start_date', '!=', False)])

        for rec in records:
            new_stage = rec._get_stage()

            if rec.stage_id != new_stage:
                rec.write({'stage_id': new_stage})
