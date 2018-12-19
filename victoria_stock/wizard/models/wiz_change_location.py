# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.osv import osv
from datetime import timedelta


class wiz_change_location(models.TransientModel):
    _name = 'wiz.change.location'
    _description = 'Wiz Change Location'

    wiz_location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        required=True)
    picking_id = fields.Many2one(
        "stock.picking", string="Picking"
    )

    @api.model
    def default_get(self, fields):
        result = super(wiz_change_location, self).default_get(fields)
        result['picking_id'] = result.get('picking_id', self._context.get('active_id'))
        picking_id = self.env['stock.picking'].browse(result['picking_id'])
        result['wiz_location_dest_id'] = picking_id.location_dest_id and picking_id.location_dest_id.id or False
        return result

    @api.multi
    def dest_loc_change(self):
        picking_id = self.picking_id
        # stock_location_paths = self.env['stock.location.path'].search([('picking_id', '=', picking_id)])
        # mrp_repairs = self.env['mrp.repair'].browse(picking_id)
        # mrp_repair_lines = self.env['mrp.repair.line'].browse(picking_id)
        if self.wiz_location_dest_id != picking_id.location_dest_id:
            if picking_id.move_lines:
                moves = picking_id.move_lines
                for move in moves:
                    move.write({
                        'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
                    })
            if picking_id.pack_operation_ids:
                operations = picking_id.pack_operation_ids
                for operation in operations:
                    operation.write({
                        'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
                    })
            if picking_id.pack_operation_pack_ids:
                operation_packs = picking_id.pack_operation_pack_ids
                for pakes in operation_packs:
                    pakes.write({
                        'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
                    })
            # if picking_id.picking_type_id:
            #     picking_type = picking_id.picking_type_id
            #     picking_type.write({
            #             'default_location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
            #         })
            # if stock_location_paths:
            #     for paths in stock_location_paths:
            #         paths.write({
            #             'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
            #         })
            # if mrp_repairs:
            #     for repair in mrp_repairs:
            #         if repair.operations:
            #             operation_lines = repair.operations
            #             for line in operation_lines:
            #                 line.write({
            #                     'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
            #                 })
            #         repair.write({
            #             'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
            #         })
            picking_id.write({
                'location_dest_id': self.wiz_location_dest_id and self.wiz_location_dest_id.id or False
            })
            picking_id.message_post(body='Location Change successfully done.')
        return {'type': 'ir.actions.act_window_close'}
