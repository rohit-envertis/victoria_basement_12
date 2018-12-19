# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockChecker(models.Model):
    _name = 'stock.checker'
    _inherit = ["mail.thread"]
    _description = 'Product Stock'
    _order = 'id desc'

    name = fields.Char(string="Reference", size=16, copy=False, default='/')
    quant_ids = fields.One2many('stock.quant', 'checker_id', string="Quant", copy=False)
    user_id = fields.Many2one('res.users', string=_('Operator'), default=lambda self: self.env.user)
    location = fields.Many2many('stock.location', 'loc_stock_check_rel', 'loca', 'stock_check', string='Location', required=True)
    product_type = fields.Many2many('product.category', 'categ_stock_check_rel', 'category', 'stock_check', string='Category')
    nagative_qty = fields.Boolean(string="Only Negative Quantity")
    min_qty = fields.Integer(string="Quantity <=")
    state = fields.Selection([('draft', 'New'), ('done', 'Generated'), ('close', 'Done')], string='Status', default='draft', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        obj_sequence = self.env['ir.sequence']
        vals.update({'name': obj_sequence.next_by_code('stock.checker.seq')})
        res = super(StockChecker, self).create(vals)
        return res

    def get_location(self):
        if self.location:
            loc = self.location
            l1 = []
            l2 = []
            for j in loc:
                l1.append(j.name)
                l2.append(j.id)
        return l1, l2

    def get_category(self):
        if self.product_type:
            categ = self.product_type
            l2 = []
            for j in categ:
                l2.append(j.id)
            return l2
        return ''

    def fetch_product(self):
        lines = []
        loc = self.get_location()
        minimum_qty = self.min_qty
        nagative_qty = self.nagative_qty
        if loc[1] and nagative_qty:
            quants = self.env['stock.quant'].search([('location_id', 'in', loc[1]), ('qty', '<=', 0)])
        elif loc[1] and minimum_qty != 0:
            quants = self.env['stock.quant'].search([('location_id', 'in', loc[1]), ('qty', '<=', minimum_qty)])
        elif loc[1] and minimum_qty == 0:
            quants = self.env['stock.quant'].search([('location_id', 'in', loc[1])])
        else:
            quants = self.env['stock.quant'].search([])
        return quants

    def generate_product(self, generator_id):
        vals = {}
        quants = self.fetch_product()
        categ = self.get_category()
        if categ:
            quants = quants.filtered(lambda r: r.product_id.categ_id.id in categ)
            self.quant_ids = quants
        else:
            self.quant_ids = quants

    @api.multi
    def refresh_product_list(self):
        fetch_product = []
        # self.quant_ids.unlink()
        self.generate_product(self.id)
        self.state = 'done'

    @api.multi
    def state_close(self):
        self.state = 'close'


class StockCheckerProduct(models.Model):
    _inherit = "stock.quant"

    checker_id = fields.Many2one(
        'stock.checker',
        string="Checker",
    )
    # sale_price = fields.Char(string="Sale Price", related='product_id.product_tmpl_id.list_price')
    product_code = fields.Char(string="Code", related='product_id.default_code')
    categ_id = fields.Many2one('product.category', related='product_id.categ_id', string=_('Category'))
