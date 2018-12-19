# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero, float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    source_availability = fields.Float(
        'Quantity In Source Location', compute='_compute_product_availability_check')
    destination_availability = fields.Float(
        'Quantity In Destination Location', compute='_compute_product_availability_check')
    product_packaging = fields.Many2one('product.packaging', string='Packaging', default=False)

    @api.one
    @api.depends('product_id', 'product_qty', 'location_id')
    def _compute_product_availability_check(self):
        squants = self.env['stock.quant'].search([
            ('location_id', '=', self.location_id.id),
            ('product_id', '=', self.product_id.id)])
        self.source_availability = sum(squants.mapped('qty'))
        dquants = self.env['stock.quant'].search([
            ('location_id', '=', self.location_dest_id.id),
            ('product_id', '=', self.product_id.id)])
        self.destination_availability = sum(dquants.mapped('qty'))

    @api.onchange('product_packaging', 'product_uom_qty')
    def _onchange_product_packaging(self):
        if not self.product_id or not self.product_uom_qty:
            self.product_packaging = False
            return {}
        if self.product_id and self.product_packaging:
            return self._check_package()

    @api.multi
    def _check_package(self):
        default_uom = self.product_id.uom_id
        pack = self.product_packaging
        qty = self.product_uom_qty
        q = default_uom._compute_quantity(pack.qty, self.product_uom)
        if qty and q and (qty % q):
            newqty = qty - (qty % q) + q
            return {
                'warning': {
                    'title': ('Warning'),
                    'message': ("This product is packaged by %.2f %s. You should sell %.2f %s.") % (pack.qty, default_uom.name, newqty, self.product_uom.name),
                },
            }
        return {}
