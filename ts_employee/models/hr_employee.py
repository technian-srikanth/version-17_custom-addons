from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def create_user(self):
        context = {
            'default_name': self.name,
            'default_login': self.work_email,
            'default_hr_employee_id': self.id,

        }
        return {
            'name': 'Create User Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'user.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('ts_employee.view_user_wizard_form').id,
            'target': 'new',
            'context': context,
        }


class User(models.Model):
    _inherit = 'res.users'

    employee_id = fields.Many2one('hr.employee')
