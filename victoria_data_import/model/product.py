from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_nos = fields.Integer('Stock Number')  # Connecting field
    stock_code = fields.Char('Stock Code')


class ProductCategory(models.Model):
    _inherit = 'product.category'

    stock_nos = fields.Integer('Stock Number')  # Connecting field
