# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPriceUpdate(models.TransientModel):
    _name = 'stock.price.update'
    _description = 'Price Update'

    invoice_id = fields.Many2one('account.invoice')
    invoice_line_id = fields.Many2one('account.invoice.line')

    @api.model
    def default_get(self, fields):
        res = super(StockPriceUpdate, self).default_get(fields)
        if not res.get('invoice_line_id') and self._context.get('active_id'):
            res['invoice_line_id'] = self._context['active_id']
        return res

    # @api.multi
    # def process(self):
    #     self.ensure_one()
    #     # If still in draft => confirm and assign
    #     if self.invoice_id:
    #         pass
