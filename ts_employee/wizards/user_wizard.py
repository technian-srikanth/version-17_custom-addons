from odoo import models, fields


class UserWizardForm(models.TransientModel):
    _name = 'user.wizard'

    name = fields.Char()
    login = fields.Char()
    user_id = fields.Many2one('res.users')
    hr_employee_id = fields.Many2one('hr.employee')

    sales_groups_id = fields.Many2one('res.groups', string="Sales", domain="[('category_id.name','=','Sales')]")
    attendance_groups_id = fields.Many2one('res.groups', string="Attendances",
                                           domain="[('category_id.name','=','Attendances')]")
    timeoff_groups_id = fields.Many2one('res.groups', string="Time Off", domain="[('category_id.name','=','Time Off')]")
    recruitment_groups_id = fields.Many2one('res.groups', string="Recruitment",
                                            domain="[('category_id.name','=','Recruitment')]")
    timesheet_groups_id = fields.Many2one('res.groups', string="Timesheet",
                                          domain="[('category_id.name','=','Timesheets')]")

    def save_user(self):

        for record in self:

            if not record.login:
                continue

            employee = record.hr_employee_id

            if employee.user_id:
                employee.user_id.write({
                    'name': record.name,
                    'login': record.login,
                    'email': record.login,
                })
                record.user_id = employee.user_id
                continue

            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.login,
                'email': record.login,
                'employee_id': employee.id,
                'groups_id': [(6, 0, [
                    self.env.ref('base.group_user').id,
                    record.sales_groups_id.id,
                    record.attendance_groups_id.id,
                    record.timeoff_groups_id.id,
                    record.recruitment_groups_id.id,
                    record.timesheet_groups_id.id,
                ])]
            })

            employee.user_id = user
            record.user_id = user
