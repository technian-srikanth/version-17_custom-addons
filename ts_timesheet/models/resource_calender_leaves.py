from odoo import models, fields, api
from datetime import datetime, time


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    flexible_hours = fields.Float(
        string="Flexible Hours",
        default=9.0,
        help="Number of hours to log in timesheets for this holiday"
    )

    def write(self, vals):
        res = super(ResourceCalendarLeaves, self).write(vals)
        for record in self:
            if record.flexible_hours:
                d_from = record.date_from.date()
                d_to = record.date_to.date()

                domain = [
                    ('date', '>=', d_from),
                    ('date', '<=', d_to),
                    ('name', 'ilike', 'Time Off'),
                ]
                if record.resource_id:
                    domain.append(('employee_id', '=', record.resource_id.employee_id.id))

                elif record.calendar_id:
                    employees = self.env['hr.employee'].search([
                        ('resource_calendar_id', '=', record.calendar_id.id)
                    ])
                    domain.append(('employee_id', 'in', employees.ids))

                lines = self.env["account.analytic.line"].search(
                    domain
                )
                for line in lines:
                    line.unit_amount = record.flexible_hours
        return res


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.model_create_multi
    def create(self, vals_list):

        lines = super().create(vals_list)

        for line in lines:

            if not line.employee_id or not line.date:
                continue

            date_start = fields.Datetime.to_datetime(line.date)
            date_end = datetime.combine(line.date, time.max)

            holiday = self.env["resource.calendar.leaves"].search([
                ('date_from', '<=', date_end),
                ('date_to', '>=', date_start),
            ], limit=1)

            if holiday:
                line.unit_amount = holiday.flexible_hours

        return lines
