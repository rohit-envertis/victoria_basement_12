# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    loc_id = fields.Many2one('stock.location', 'Location')

    @api.constrains('location_id', 'location_dest_id')
    def _check_location(self):
        for rec in self:
            if rec.location_id == rec.location_dest_id:
                raise ValidationError(('You cannot have same location for source and destination'))
        return True

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        if self.picking_type_id and self.env.context.get('default_location_dest_id'):
            self.location_id = self.env.context.get('default_location_dest_id')
            self.location_dest_id = ''

    @api.onchange('transfer_type')
    def onchange_transfer(self):
        if self.transfer_type == 'send':
            self.location_id = self.loc_id.id
            self.location_dest_id = False
        elif self.transfer_type == 'request':
            self.location_id = False
            self.location_dest_id = self.loc_id.id

    @api.multi
    def write(self, vals):
        if vals.get('transfer_type') == 'send':
            vals['location_id'] = self.loc_id.id
        elif vals.get('transfer_type') == 'request':
            vals['location_dest_id'] = self.loc_id.id
        return super(StockPicking, self).write(vals)
