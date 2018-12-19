# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    min_date = fields.Datetime(
        'Scheduled Date', compute='_compute_dates', inverse='_set_min_date', store=True,
        index=True, track_visibility='onchange',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    max_date = fields.Datetime(
        'Max. Expected Date', compute='_compute_dates', store=True,
        index=True,
        help="Scheduled time for the last part of the shipment to be processed")

    @api.one
    @api.depends('move_lines.date_expected')
    def _compute_dates(self):
        self.min_date = min(self.move_lines.mapped('date_expected') or [False])
        self.max_date = max(self.move_lines.mapped('date_expected') or [False])

    @api.one
    def _set_min_date(self):
        self.move_lines.write({'date_expected': self.min_date})


class StockTransferVictoria(models.Model):
    _name = 'stock.transfer.victoria'
    _description = 'Stock Transfer Victoria'

    name = fields.Char(
        'Name', default=lambda self: self.env['ir.sequence'].next_by_code('stock.transfer.victoria'),
        copy=False, readonly=True, track_visibility='always')
    date_to = fields.Date('Date To')
    date_from = fields.Date('Date From')
    transfer_lines = fields.One2many(
        'stock.transfer.victoria.lines', 'transfer_id', 'Transfer Lines',
        copy=True, states={'recheck': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('compute', 'Compute'),
        ('check', 'Check'),
        ('recheck', 'Re-check'),
        ('cancel', 'Cancelled')], 'State', default='draft',
        copy=False, readonly=True, track_visibility='onchange')

    @api.multi
    def compute_stock_transfer_lines(self):
        StockPicking = self.env['stock.picking']
        Stocking = StockPicking.search([('min_date', '>=', self.date_to), ('max_date', '<=', self.date_from),
                                        ('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned'])])
        val_line_values = {}
        for rec in Stocking:
            val_line_values.update({'transfer_id': self.id, 'name': rec.name, 'picking_type_id': rec.picking_type_id.id,
                                    'state': rec.state, 'stock_picking_id': rec.id})
            self.env['stock.transfer.victoria.lines'].create(val_line_values)
        self.state = 'compute'

    @api.multi
    def button_check(self):
        self.state = 'check'

    @api.multi
    def button_recheck(self):
        for line in self.transfer_lines:
            if line.check and line.recheck:
                line.stock_picking_id.action_confirm()
                for pack in line.stock_picking_id.pack_operation_ids:
                    pack.write({'qty_done': pack.product_qty})
                line.stock_picking_id.do_new_transfer()
        self.state = 'recheck'

    @api.multi
    def button_done(self):
        self.state = 'draft'

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'


class StockTransferVictorialines(models.Model):
    _name = 'stock.transfer.victoria.lines'
    _description = 'Stock Transfer Victoria'

    name = fields.Char('Description')
    transfer_id = fields.Many2one(
        'stock.transfer.victoria', 'Lines',
        required=True, ondelete='cascade')
    # product_id = fields.Many2one('product.product', 'Product', required=True)
    # product_uom_qty = fields.Float('Quantity')
    # product_uom = fields.Many2one(
    #     'product.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'),
        ('assigned', 'Available'), ('done', 'Done')], string='Status')
    check = fields.Boolean("Check")
    recheck = fields.Boolean("Re-Check")
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type')
    stock_picking_id = fields.Many2one('stock.picking', 'Picking')
