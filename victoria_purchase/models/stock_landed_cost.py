# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons.stock_landed_costs.models import product


class LandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.currency_id, line.product_qty, product=line.product_id, partner=line.purchase_cost_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    purchase_cost_id = fields.Many2one('purchase.order', 'Landed Cost', ondelete='cascade')
    cost_id = fields.Many2one('stock.landed.cost',required=False)
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)
    product_qty = fields.Integer(default=1)
    currency_id = fields.Many2one(related='purchase_cost_id.currency_id', store=True, string='Currency', readonly=True)
    split_method = fields.Selection(product.SPLIT_METHOD, string='Split Method', required=True, default='by_quantity')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            self.quantity = 0.0
        self.name = self.product_id.name or ''
        self.split_method = self.product_id.split_method or 'by_quantity'
        self.price_unit = self.product_id.standard_price or 0.0
        self.account_id = self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id.id


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    _description = 'Stock Valuation Adjustment Lines'

    purchase_cost_id = fields.Many2one('purchase.order', 'Landed Cost')
    cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', ondelete='cascade', required=False)

    def _create_accounting_entries(self, move, qty_out):
        cost_product = self.cost_line_id.product_id
        if not cost_product:
            return False
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        debit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = self.cost_line_id.account_id.id or cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))

        return self._create_account_move_line(move, credit_account_id, debit_account_id, qty_out, already_out_account_id)

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        AccountMoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
        base_line = {
            'name': self.name,
            'move_id': move.id,
            'product_id': self.product_id.id,
            'quantity': self.quantity,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.create(debit_line)
        AccountMoveLine.create(credit_line)
        move.assert_balanced()
        return True
