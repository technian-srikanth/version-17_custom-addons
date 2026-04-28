from odoo import models, fields


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    flexible_hours = fields.Float(
        string="Flexible Hours",
        default=9.0,
        help="Number of hours to log in timesheets for this holiday"
    )

    def _timesheet_prepare_line_values(
            self, index, employee_id, work_hours_data, day_date, work_hours_count
    ):
        self.ensure_one()

        values = super()._timesheet_prepare_line_values(
            index, employee_id, work_hours_data, day_date, work_hours_count
        )

        values['unit_amount'] = self.flexible_hours

        return values

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
