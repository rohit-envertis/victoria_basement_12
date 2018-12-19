# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductStyle(models.Model):
    _name = 'product.style'
    _description = 'Product Style'
    _order = 'name'

    name = fields.Char('Style')
    category_id = fields.Many2one(
        'product.category', string='Category')
    logo = fields.Binary('Logo')
    active = fields.Boolean('Active')
    style_url = fields.Char('Style Url')
    code = fields.Char("Code")
    web_enabled = fields.Boolean("Web Enabled")
    stock_nos = fields.Char("Stock Nos")
