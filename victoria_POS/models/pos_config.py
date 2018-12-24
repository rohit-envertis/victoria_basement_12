# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import timedelta


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _default_picking_type(self):
        return self.env['stock.picking.type'].search([('name', 'ilike', 'Internal Transfer')], limit=1).id

    picking_type = fields.Many2one('stock.picking.type', 'Picking Type', default=_default_picking_type)
    shop_id = fields.Many2one('pos.shop', 'Shop')

    @api.onchange('shop_id')
    def _onchange_shop_id(self):
        if self.shop_id:
            self.stock_location_id = self.shop_id.location_id and self.shop_id.location_id.id or False


class ReportSaleDetails(models.AbstractModel):
    _name = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, configs=False, track_activity=False):
        """ Serialise the orders of the day information

        params: date_start, date_stop string representing the datetime of order
        """
        if not configs:
            configs = self.env['pos.config'].search([])

        today = fields.Datetime.from_string(fields.Date.context_today(self))
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            # start by default today 00:00:00
            date_start = today

        if date_stop:
            # set time to 23:59:59
            date_stop = fields.Datetime.from_string(date_stop)
        else:
            # stop by default today 23:59:59
            date_stop = today + timedelta(days=1, seconds=-1)

        # avoid a date_stop smaller than date_start
        date_stop = max(date_stop, date_start)

        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)

        orders = self.env['pos.order'].search([
            ('date_order', '>=', date_start),
            ('date_order', '<=', date_stop),
            ('state', 'in', ['paid', 'invoiced', 'done']),
            ('config_id', 'in', configs.ids)])

        user_currency = self.env.user.company_id.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id.compute(order.amount_total, user_currency)
            else:
                total += order.amount_total
            currency = order.session_id.currency_id
            for line in order.lines:
                product_sold = {}
                if not track_activity:
                    key = (line.product_id, line.price_unit, line.discount)
                    products_sold.setdefault(key, 0.0)
                    products_sold[key] += line.qty
                if track_activity:
                    sold_by = order.user_id
                    date_order = order.date_order
                    key = (line.product_id, line.price_unit, line.discount, sold_by, date_order)
                    products_sold.setdefault(key, 0.0)
                    products_sold[key] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'total': 0.0})
                        taxes[tax['id']]['total'] += tax['amount']
        st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)]).ids
        if st_line_ids:
            self.env.cr.execute("""
                SELECT aj.name, sum(amount) total
                FROM account_bank_statement_line AS absl,
                     account_bank_statement AS abs,
                     account_journal AS aj
                WHERE absl.statement_id = abs.id
                    AND abs.journal_id = aj.id
                    AND absl.id IN %s
                GROUP BY aj.name
            """, (tuple(st_line_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []
        if not track_activity:
            return {
                'total_paid': user_currency.round(total),
                'payments': payments,
                'company_name': self.env.user.company_id.name,
                'taxes': taxes.values(),
                'products': sorted([{
                    'product_id': product.id,
                    'product_name': product.name,
                    'code': product.default_code,
                    'quantity': qty,
                    'price_unit': price_unit,
                    'discount': discount,
                    'uom': product.uom_id.name
                } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
            }
        else:
            return {
                'total_paid': user_currency.round(total),
                'payments': payments,
                'company_name': self.env.user.company_id.name,
                'taxes': taxes.values(),
                'products': sorted([{
                    'sold_by': sold_by.name,
                    'order_date': date_order,
                    'product_id': product.id,
                    'track_activity': product.track_activity,
                    'product_name': product.name,
                    'code': product.default_code,
                    'quantity': qty,
                    'price_unit': price_unit,
                    'discount': discount,
                    'uom': product.uom_id.name
                } for (product, price_unit, discount, sold_by, date_order), qty in products_sold.items()], key=lambda l: l['sold_by'])
            }

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs, data['track_activity']))
        return self.env['report'].render('point_of_sale.report_saledetails', data)


class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'
    _description = 'Open Sale Details Report'

    track_activity = fields.Boolean('Track Activity')

    @api.multi
    def generate_report(self):
        data = {
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'config_ids': self.pos_config_ids.ids,
            'track_activity': self.track_activity
        }
        return self.env['report'].get_action(
            [], 'point_of_sale.report_saledetails', data=data)


class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_user_id = fields.Many2one(
        'res.users', related='order_id.user_id', string='Salesman',
        help="Person who uses the cash register. It can be a reliever, a student or an interim employee."
    )
