# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('trip.brand'))
    street = fields.Char(size=128, string="Street")
    street2 = fields.Char(size=128, string="Street2")
    zip_code = fields.Char(size=24, string="Zip")
    city = fields.Char(size=24, string="City")
    state_id = fields.Many2one('res.country.state', string="State")
    country_id = fields.Many2one('res.country', string="Country")
    email = fields.Char(size=64, string="Email")
    phone = fields.Char(size=64, string="Phone")
    fax = fields.Char(size=64, string="Fax")
    website = fields.Char(string="Website", size=64)
    rml_header1 = fields.Char(string='Brand Tagline')
    logo = fields.Binary(string="Logo")
    is_own = fields.Boolean(string="Is own Brand")
    brand_url = fields.Char(string='Brand Url')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Brand name must be unique !')
    ]
