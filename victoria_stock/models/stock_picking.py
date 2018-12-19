# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import namedtuple
import json
import time

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def get_invoice_address(self, origin):
        order_id = self.env['sale.order'].search([('name', '=', str(origin))])
        if order_id and order_id.partner_invoice_id:
            invoice_address = order_id.partner_invoice_id
        return invoice_address

    @api.multi
    def get_deliver_address(self, origin):
        order_id = self.env['sale.order'].search([('name', '=', str(origin))])
        if order_id and order_id.partner_shipping_id:
            deliver_address = order_id.partner_shipping_id
        return deliver_address

    show_location = fields.Boolean(compute='_compute_show_location')
    state = fields.Selection([
        ('draft', 'Confirm'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'), ('pick', 'Picked'),
        ('verify', 'Verified'),
        ('send', 'Transferred'),
        ('done', 'Done')], string='Status')
    check_in = fields.Boolean(compute='_compute_check_in_out')
    check_out = fields.Boolean(compute='_compute_check_in_out')
    transfer_type = fields.Selection([('send', 'Send Goods'), ('request', 'Request Goods')], string='Transfer Type', default='send')

    @api.one
    @api.depends('transfer_type', 'location_id', 'location_dest_id', 'state')
    def _compute_check_in_out(self):
        pos_loc_id = self._context.get('pos_loc_id')
        self.check_in = False
        self.check_out = False
        for picking in self:
            if picking.location_id.id == pos_loc_id:
                self.check_in = True
            elif picking.location_dest_id.id == pos_loc_id:
                self.check_out = True

    @api.one
    @api.depends('name', 'picking_type_id', 'picking_type_code')
    def _compute_show_location(self):
        po = self.env['purchase.order'].search([('name', '=', self.origin)])
        type = po.purchase_type
        for picking in self:
            if picking.picking_type_code in ('incoming', 'internal') and ("IN" in picking.name) and type == 'local':
                self.show_location = True

    @api.multi
    def change_location(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Change Location',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.change.location',
            'target': 'new',
        }
        return action

    @api.multi
    def button_pick(self):
        if not self.move_lines or not self.pack_operation_ids:
            raise UserError(_('You can not pick without move line or operation line.'))
        self.state = 'pick'

    @api.multi
    def button_verify(self):
        if not self.move_lines or not self.pack_operation_ids:
            raise UserError(_('You can not pick without move line or operation line.'))
        self.state = 'verify'

    @api.multi
    def button_send(self):
        if not self.move_lines or not self.pack_operation_ids:
            raise UserError(_('You can not pick without move line or operation line.'))
        self.state = 'send'

    @api.multi
    def button_receive(self):
        if not self.move_lines or not self.pack_operation_ids:
            raise UserError(_('You can not pick without move line or operation line.'))
        self.do_transfer()

    @api.multi
    def button_receive2(self):
        if not self.move_lines or not self.pack_operation_ids:
            raise UserError(_('You can not pick without move line or operation line.'))
        self.do_transfer()


class StockLocation(models.Model):
    _inherit = 'stock.location'

    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')


class Company(models.Model):
    _inherit = "res.company"

    abn = fields.Char(string="ABN")