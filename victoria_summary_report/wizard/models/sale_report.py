# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from datetime import datetime

class SaleOrderSummary(models.TransientModel):
    _name = 'sale.order.summary'

    select_date = fields.Datetime(string="Select Date")

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['select_date'])[0]
        return self.env.ref('victoria_summary_report.action_sale_order_summary_report').report_action(self, data)


class ReportDailyReorder(models.AbstractModel):
    _name = 'report.victoria_summary_report.order_summary_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        sale_id = self.env['sale.order'].search([])
        sale_order_lst = []
        for sale in sale_id:
            if sale.date_order.date() == docs.select_date.date():
                sale_order_lst.append(sale)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'sale_list': sale_id,
            'sale_order_lst': sale_order_lst
        }
        return docargs