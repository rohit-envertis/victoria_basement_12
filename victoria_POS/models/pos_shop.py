# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import time
from email.utils import formataddr
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PosShop(models.Model):
    _name = 'pos.shop'

    def _default_company(self):
        return self.env['res.company']._company_default_get('pos.shop')

    def _default_picking_type(self):
        return self.env['stock.picking.type'].search([('name', 'ilike', 'Internal Transfers')], limit=1).id

    def _compute_stock_picking(self):
        for rec in self:
            stock_picking = self.env['stock.picking'].search([
                ('state', '!=', 'done'),
                ('location_id', '=', rec.location_id.id),
                ('picking_type_id', '=', rec.picking_type.id)
            ])
            rec.stock_picking_ids = stock_picking

    name = fields.Char(index=True)
    ref = fields.Char(string='Internal Reference', index=True)
    user_id = fields.One2many('res.users', 'pos_shop_id', string='Salesperson',
        help='The internal user that is in charge of communicating with this contact if any.')
    comment = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    street = fields.Char()
    street2 = fields.Char()
    zipcode = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char()
    email_formatted = fields.Char(
        'Formatted Email', compute='_compute_email_formatted',
        help='Format email address "Name <email@domain>"')
    phone = fields.Char()
    fax = fields.Char()
    mobile = fields.Char()
    company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)
    image = fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px",)
    image_small = fields.Binary("Small-sized image", attachment=True,
        help="Small-sized image of this contact. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")

    pos_ids = fields.One2many('pos.config', 'shop_id', string="Point Of Sale")
    location_id = fields.Many2one('stock.location', string="Stock Location")
    partner_id = fields.Many2one('res.partner', string="Related partner")
    picking_type = fields.Many2one('stock.picking.type', 'Picking Type', default=_default_picking_type)
    stock_picking_ids = fields.One2many('stock.picking', compute='_compute_stock_picking')
    count_picking_in = fields.Integer(compute='_compute_picking')
    count_picking_out = fields.Integer(compute='_compute_picking')

    _sql_constraints = [('name_uniq', 'unique (name)', "Shop already exists !")]

    @api.depends('name', 'email')
    def _compute_email_formatted(self):
        for shop in self:
            shop.email_formatted = formataddr((shop.name, shop.email))

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id:
            for pos in self.pos_ids:
                pos.write({
                    'stock_location_id': self.location_id.id
                })

    @api.onchange('picking_type')
    def _onchange_picking_type(self):
        if self.picking_type:
            for pos in self.pos_ids:
                pos.write({
                    'picking_type_id': self.picking_type.id
                })

    @api.multi
    def act_stock_transfer_in(self):
        self.ensure_one()
        from_view = self.env.ref('victoria_POS.view_picking_form_transfer')
        search_view = self.env.ref('victoria_POS.view_picking_internal_search_vb')
        return {
            'name': ('Stock Transfer In'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (from_view.id, 'form')],
            'search_view_id': search_view.id,
            'target': 'current',
            'domain': [
                    ('location_dest_id', '=', self.location_id.id),
                    ('state', 'in', ['send']),
            ],
            'context': {
                'create': False,
                'transfer_type': 'send',
                'pos_loc_id': self.location_id.id
            },
        }

    @api.multi
    def act_stock_transfer_out(self):
        self.ensure_one()
        from_view = self.env.ref('victoria_POS.view_picking_form_transfer')
        search_view = self.env.ref('victoria_POS.view_picking_internal_search_vb')
        return {
            'name': ('Stock Transfer Out'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (from_view.id, 'form')],
            'search_view_id': search_view.id,
            'target': 'current',
            'domain': [
                ('location_id', '=', self.location_id.id),
                ('state', 'not in', ['send', 'done']),
            ],
            'context': {
                'create': False,
                'transfer_type': 'request',
                'pos_loc_id': self.location_id.id
            },
        }

    @api.multi
    def act_stock_transfer_new(self):
        self.ensure_one()
        view = self.env.ref('victoria_POS.view_picking_form_transfer')
        return {
            'name': ('Stock Transfer Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'domain': [('picking_type_id', 'in', self.picking_type.id)],
            'context': {
                'default_loc_id': self.location_id.id,
                'default_location_id': self.location_id.id,
                'default_location_dest_id': self.location_id.id,
                'default_transfer_type': 'send',
                'search_default_picking_type_id': [self.picking_type.id],
                'default_picking_type_id': self.picking_type.id,
                'contact_display': 'partner_address',
                'pos_loc_id': self.location_id.id
            }
        }

    @api.multi
    def act_purchase_order_request(self):
        self.ensure_one()
        view = self.env.ref('purchase.purchase_order_form')
        return {
            'name': ('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'context': {'default_purchase_type': 'import', 'hide_landed': False},
            'target': 'current',
        }

    @api.multi
    def _compute_picking(self):
        in_data = []
        out_data = []
        for record in self:
            in_data = self.env['stock.picking'].search([
                ('location_dest_id', '=', record.location_id.id),
                ('state', 'in', ['send']),
            ])
            out_data = self.env['stock.picking'].search([
                ('location_id', '=', record.location_id.id),
                ('state', 'not in', ['send', 'done']),
            ])
            record.count_picking_in = len(in_data) or 0
            record.count_picking_out = len(out_data) or 0


class Users(models.Model):
    _inherit = 'res.users'

    pos_shop_id = fields.Many2one('pos.shop', string="POS Shop")
