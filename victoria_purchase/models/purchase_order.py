# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning, RedirectWarning

import odoo.addons.decimal_precision as dp


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    PURCHASE_TYPE_SELECTION = [
        ('local', _('Local Purchase')),
        ('import', _('Import Purchase'))]
    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.onchange('purchase_type')
    def onchange_purchase(self):
        ctx = dict(self.env.context)
        if self.purchase_type in ['local']:
            ctx.update({
                'hide_landed': 1,
            })
        else:
             ctx.update({
                'hide_landed': 0,
            })
        return {'context':ctx}

    @api.depends('partner_id')
    def _compute_payment(self):
        move_payment_id = []
        domain = [('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id), ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
        domain.extend([('credit', '=', 0), ('debit', '>', 0)])
        lines = self.env['account.move.line'].search(domain)
        if len(lines) != 0:
            move_payment_id.extend([line.payment_id.id for line in lines])
        for order in self:
            account_payment_obj = self.env['account.payment']
            partner = order.partner_id
            if partner:
                payments = account_payment_obj.search([('partner_id', '=', partner.id), ('id', '=', move_payment_id)])
                order.payment_ids = payments
                order.po_payment = len(payments)

    cost_id = fields.Many2one('stock.landed.cost')
    purchase_type = fields.Selection(PURCHASE_TYPE_SELECTION,
        string='Purchase Type',
        states={
            'confirmed': [('readonly',True)],
            'approved': [('readonly',True)],
            'done': [('readonly',True)]},
        )
    partner_id = fields.Many2one('res.partner',
        string='Vendor', required=False,
        states=READONLY_STATES, change_default=True,
        track_visibility='always')
    date_order = fields.Datetime('Order Date', required=False,
        states=READONLY_STATES, index=True, 
        copy=False, default=fields.Datetime.now,\
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    currency_id = fields.Many2one('res.currency', 'Currency', 
        required=False, states=READONLY_STATES,\
        default=lambda self: self.env.user.company_id.currency_id.id)
    stock_cost_lines = fields.One2many('stock.landed.cost.lines', 'purchase_cost_id', 'Cost Lines')
    ll_amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all_landed', track_visibility='always')
    ll_amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all_landed')
    ll_amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all_landed')
    account_move_id = fields.Many2one('account.move', 'Journal Entry')
    # account_journal_id = fields.Many2one('account.journal', 'Account Journal', copy=False)
    valuation_adjustment_lines = fields.One2many('stock.valuation.adjustment.lines', 'purchase_cost_id', 'Valuation Adjustments')
    payment_ids = fields.Many2many('account.payment', compute="_compute_payment", string='Payment', copy=False)
    po_payment = fields.Integer(compute="_compute_payment", string='# of Payments', copy=False, default=0)

    @api.depends('stock_cost_lines.price_total')
    def _amount_all_landed(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.stock_cost_lines:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'll_amount_untaxed': order.currency_id.round(amount_untaxed),
                'll_amount_tax': order.currency_id.round(amount_tax),
                'll_amount_total': amount_untaxed + amount_tax,
            })
    #FIX - it is not updating landed cost in purchase order line
    def _compute_total_landed(self):
        dict = {}
        for lines in self.valuation_adjustment_lines:
            if lines.product_id.id in dict:
                dict[lines.product_id.id] += lines.additional_landed_cost
            else :
                dict[lines.product_id.id] = lines.additional_landed_cost
        for order in self.order_line:
            if order.product_id.id :
                qty = order.product_qty
                vals = dict.get(order.product_id.id,0)
                only_ld = vals / qty
                ld = only_ld + order.price_unit
                order.write({'landed_cost':ld})
        return True
        
    def get_valuation_lines(self):
        lines = []
        for purchase_order_line in self.mapped('order_line'):
            if purchase_order_line.product_id.valuation != 'real_time' or purchase_order_line.product_id.cost_method != 'real':
                continue
            vals = {
                'product_id': purchase_order_line.product_id.id,
                'purchase_cost_id': purchase_order_line.order_id.id,
                'quantity': purchase_order_line.product_qty,
                'former_cost': sum(cost.price_unit * cost.product_qty for cost in purchase_order_line),
                'weight': purchase_order_line.product_id.weight * purchase_order_line.product_qty,
                'volume': purchase_order_line.product_id.volume * purchase_order_line.product_qty
            }
            lines.append(vals)
        if not lines :
            raise UserError(('The selected purchase order does not contain any line that would be impacted by landed costs. Landed costs are only possible for products configured in real time valuation with real price costing method. Please make sure it is the case, or you selected the correct product'))
        
        return lines

    @api.multi
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('purchase_cost_id', 'in', self.ids)]).unlink()
        digits = dp.get_precision('Product Price')(self._cr)
        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost.order_line):
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.stock_cost_lines:
                    val_line_values.update({'purchase_cost_id': cost.id, 'cost_line_id': cost_line.id})
                    AdjustementLines.create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_cost += val_line_values.get('former_cost', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)
                total_line += 1

            for line in cost.stock_cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = tools.float_round(value, precision_digits=digits[1], rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        # self.button_confirm()
        if towrite_dict:
            for key, value in towrite_dict.items():
                AdjustementLines.browse(key).write({'additional_landed_cost': value})
        self._compute_total_landed()
        return True

    def _check_sum(self):
        prec_digits = self.env['decimal.precision'].precision_get('Account')
        for landed_cost in self:
            total_amount = sum(landed_cost.valuation_adjustment_lines.mapped('additional_landed_cost'))
            if not tools.float_compare(total_amount, landed_cost.ll_amount_total, precision_digits=prec_digits) == 0:
                return False
            val_to_cost_lines = defaultdict(lambda: 0.0)
            for val_line in landed_cost.valuation_adjustment_lines:
                val_to_cost_lines[val_line.cost_line_id] += val_line.additional_landed_cost
            if any(tools.float_compare(cost_line.price_unit, val_amount, precision_digits=prec_digits) != 0
                   for cost_line, val_amount in val_to_cost_lines.iteritems()):
                return False
        return True

    # @api.multi
    # def button_confirm(self):
    #     res = super(purchase_order, self).button_confirm()
    #     # if self.stock_cost_lines:
    #     #     self.compute_landed_cost()
    #     if self.valuation_adjustment_lines:
    #         # if not self._check_sum():
    #         #     raise UserError(('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))   
    #         for cost in self:
    #             # if not self.account_move_id:
    #             move = self.env['account.move'].create({
    #                 'journal_id': cost.account_journal_id.id,
    #                 'date': cost.date_order[:10],
    #                 'ref': cost.name
    #             })
    #             for line in cost.valuation_adjustment_lines.filtered(lambda line: line.purchase_cost_id):
    #                 qty_out = 0
    #                 for quant in line:
    #                     qty_out += quant.quantity
    #                 line._create_accounting_entries(move, qty_out)
    #             cost.write({'account_move_id': move.id})
    #             move.post()
    #         self._compute_total_landed()
    #         return res

    @api.multi
    def action_open_payment(self):
        '''
        This function returns an action that display existing vendor payment.
        When only one found, show the vendor payment immediately.
        '''
        action = self.env.ref('victoria_purchase.action_account_payments_payable_vb')
        result = action.read()[0]

        #override the context to get rid of the default filtering
        ctx = {
            'default_payment_type': 'outbound',
            'default_partner_type': 'supplier',
            'default_partner_id': self.partner_id.id
        }
        result['context'] = ctx

        #choose the view_mode accordingly
        if len(self.payment_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.payment_ids.ids) + ")]"
        elif len(self.payment_ids) == 1:
            res = self.env.ref('account.view_account_payment_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.payment_ids.id
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)])
    # product_id = fields.Many2one('product.product', string='Product', domain=['&',('state', 'in',['new','progress','done']),('purchase_ok','=',True)])
    landed_cost = fields.Float('Landed Cost', digits=dp.get_precision('Purchase Price'), copy=False)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Purchase Price'))

    # @api.onchange('price_unit')
    def onchange_price_unit(self):
        if not self.product_id:
            return
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)
        price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, self.product_id.supplier_taxes_id, self.taxes_id) if seller else 0.0
        if price_unit > 0.0 and self.price_unit > price_unit:
            return False
        return True

    _constraints = [
        (onchange_price_unit, 'Product Purchase Price should be less than Contract Price', ['price_unit']),
    ]


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('price_unit')
    def onchange_price_unit_less(self):
        if not self.product_id:
            return
        user_is_admin = self.env['res.users'].browse(self.env.user.id)._is_admin()
        for line in self:
            # price_unit = line.product_id.standard_price
            seller = line.product_id._select_seller(
            partner_id=line.invoice_id.partner_id,
            quantity=line.quantity,
            date=line.invoice_id.date_invoice and line.invoice_id.date_invoice[:10],
            uom_id=line.uom_id)
            price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, line.product_id.supplier_taxes_id, line.invoice_line_tax_ids) if seller else 0.0
            if line.price_unit == price_unit:
                continue
            else:
                if user_is_admin:
                    if line.price_unit < price_unit:
                        raise Warning(("Product unit price of vendor bill less than product unit price (%s) of purchase order") % price_unit)
                    else:
                        raise Warning(("Product unit price of vendor bill more than product unit price (%s) of purchase order") % price_unit)
                else:
                    if line.price_unit < price_unit:
                        raise Warning(("Product unit price of vendor bill less than product unit price (%s) of purchase order") % price_unit)
                    else:
                        pass

    def onchange_price_unit(self):
        user_is_admin = self.env['res.users'].browse(self.env.user.id)._is_admin()
        for line in self:
            seller = line.product_id._select_seller(
                partner_id=line.invoice_id.partner_id,
                quantity=line.quantity,
                date=line.invoice_id.date_invoice and line.invoice_id.date_invoice[:10],
                uom_id=line.uom_id)
            price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, line.product_id.supplier_taxes_id, line.invoice_line_tax_ids) if seller else 0.0      
            if not user_is_admin and  line.price_unit > price_unit:
                return False
            return True

    _constraints = [(onchange_price_unit, 'Product unit price of vendor bill must be same or more than product unit price of purchase order.', ['price_unit'])]
