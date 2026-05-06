from odoo import api, fields, models, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    manager_name = fields.Char(string="Manager Name")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
