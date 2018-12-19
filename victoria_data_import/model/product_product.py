# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [
        ('barcode_uniq', 'CHECK(1=1)', _("A barcode can only be assigned to one product !")),
    ]
