# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
# from openerp.osv import osv
# import time
# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
# from openerp.tools.safe_eval import safe_eval
# from datetime import datetime


class StockTransferVictoria(models.Model):
    _inherit = ["stock.transfer.victoria"]

    @api.one
    def get_itmes(self):
        if self:
            sql = """
            select
                sp.name,
                pp.default_code,
                pt.name,
                sl.name,
                sld.name,
                o.product_qty
            from stock_move_line as o
                left join stock_picking as sp on sp.id = o.picking_id
                left join product_product as pp on pp.id = o.product_id
                left join product_template as pt on pt.id = pp.product_tmpl_id
                left join stock_location as sl on sl.id = o.location_id
                left join stock_location as sld on sld.id = o.location_dest_id
            where
                sp.min_date >= '%s'::date
                    and sp.max_date <= '%s'::date
                    and sp.state in ('draft','waiting','confirmed','assigned')
            """ % (self.date_to, self.date_from)
            self.env.cr.execute(sql)
            records = self.env.cr.fetchall()
            return self.get_index(records)

    @api.multi
    def get_index(self, records):
        result = []
        for index, record in enumerate(records):
            record = list(record)
            record.insert(0, index+1)
            result.append(tuple(record))
        return result
