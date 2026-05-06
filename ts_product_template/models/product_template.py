from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    contact_ids = fields.One2many('artist.contact.line', string="Manager", inverse_name="product_id")


class ArtistContactLine(models.Model):
    _name = 'artist.contact.line'

    name = fields.Char(string="Name")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")

    product_id = fields.Many2one(comodel_name='product.template', string="Product")
