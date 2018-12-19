from odoo import api, fields, models, _
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # product_id = fields.Many2one('product.product', string='Product', domain=['&',('state', '=','done'),('sale_ok','=',True)])
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)])

    @api.onchange('product_uom_qty', 'product_packaging')
    def _check_package(self):
        default_uom = self.product_id.uom_id
        pack = self.product_packaging
        qty = self.product_uom_qty
        q = default_uom._compute_quantity(pack.qty, self.product_uom)
        if qty and q and (qty % q):
            newqty = qty - (qty % q) + q
            self.product_uom_qty = q
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _("This product is packaged by %.2f %s. You should sell %.2f %s.") % (pack.qty, default_uom.name, newqty, self.product_uom.name),
                },
            }
        return {}
