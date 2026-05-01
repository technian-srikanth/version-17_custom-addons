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

    @api.depends('start_date')
    def _compute_stage(self):
        today = fields.Date.today()

        for rec in self:
            rec.stage_id = rec._get_stage(today)

    def _get_stage(self, today=None):
        self.ensure_one()

        today = today or fields.Date.today()

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

    @api.model_create_multi
    def create(self, vals_list):
        today = fields.Date.today()

        for vals in vals_list:

            if vals.get('application_id') and not vals.get('name'):
                applicant = self.env['hr.applicant'].browse(vals['application_id'])
                vals['name'] = applicant.partner_name or applicant.name

            if vals.get('start_date'):
                dummy = self.new(vals)  # temporary record
                vals['stage_id'] = dummy._get_stage(today)
            else:
                vals['stage_id'] = 'new'

        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)

        today = fields.Date.today()

        for rec in self:

            if 'application_id' in vals and not vals.get('name'):
                if rec.application_id:
                    rec.name = rec.application_id.partner_name or rec.application_id.name

            if 'start_date' in vals:
                rec.stage_id = rec._get_stage(today)

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
        # today = fields.Date.today()
        today = fields.Date.from_string('2026-05-04')

        for rec in records:
            new_stage = rec._get_stage(today)

            if rec.stage_id != new_stage:
                rec.write({'stage_id': new_stage})
