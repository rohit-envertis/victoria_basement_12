# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class StockUpdate(models.Model):

    _name = 'stock.update'
    _description = 'Stock Update'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        types = type_obj.search([('code', '=', 'incoming')])#Receipt selected for picking type
        return types[:1]

    @api.depends('stock_transfer_lines.move_ids')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.stock_transfer_lines:
                moves = line.move_ids 
                moves = moves.filtered(lambda r: r.state != 'cancel')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.src_location_id = self.partner_id.property_stock_supplier.id

    name = fields.Char('Name', copy=False, readonly=True, track_visibility='always', default="New")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('transfer', 'Verify'),
        ('pass', 'Passed'),
        ('fail', 'Failed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], 'State', default='draft',
        copy=False, readonly=True, track_visibility='onchange')
    date = fields.Datetime(string='Received Date', readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', 'Vendor')
    stock_transfer_lines = fields.One2many(
        'stock.update.lines', 'update_id', 'Update Lines',
        copy=True, states={'done': [('readonly', True)]})
    notes = fields.Text('Notes ... ')
    invoice_id = fields.Many2one('account.invoice', 'Vendor Bill')
    src_location_id = fields.Many2one('stock.location', 'Source Location')

    # picking wise same as purchase
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking', default=_default_picking_type)
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Receptions', copy=False)
    dest_location_id = fields.Many2one('stock.location', 'Destination Location')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stock.update')
        vals['state'] = 'draft'
        return super(StockUpdate, self).create(vals)

    @api.multi
    def button_confirm(self):
        for rec in self:
            if not rec.stock_transfer_lines:
                raise UserError(_('Please add some lines.'))
        self._create_picking()
        self.account_invoice()
        self.state = 'confirm'

    @api.multi
    def button_transfer(self):
        self._validate_picking()
        self.state = 'transfer'

    @api.multi
    def do_fail(self):
        self.write({
            'state': 'fail',
        })
        # return self.redirect_after_pass_fail()

    @api.multi
    def do_pass(self):
        self.write({
            'state': 'pass',
        })
        # return self.redirect_after_pass_fail()

    @api.multi
    def button_done(self):
        for rec in self.picking_ids:
            rec.action_confirm()
            for pack in rec.pack_operation_ids:
                pack.write({'qty_done': pack.product_qty})
            # line.stock_picking_id.do_new_transfer()
            rec.do_new_transfer()
            self.state = 'done'

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.stock_transfer_lines.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.stock_transfer_lines._create_stock_moves(picking)
        return True

    @api.model
    def _prepare_picking(self):
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date,
            'origin': self.name,
            'location_dest_id': self.dest_location_id.id,
            'location_id': self.src_location_id.id,
        }

    @api.multi
    def _validate_picking(self):
        picking_ids = self.picking_ids
        if picking_ids:
            for picking_id in picking_ids:
                move_obj = self.env['stock.move']
                moves = move_obj.search([('picking_id', '=', picking_id.id)])
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel')).action_confirm()
                moves.force_assign()
                picking_id.message_post_with_view('mail.message_origin_link', values={'self': picking_id,
                                                                                      'origin': self},
                                                  subtype_id=self.env.ref('mail.mt_note').id)
        return True

    @api.multi
    def account_invoice(self):
        InvoiceLine = self.env['account.invoice.line']
        Invoice = self.env['account.invoice']
        invoice = Invoice.create({
                'name': self.name,
                'origin': self.name,
                'type': 'out_invoice',
                'account_id': self.partner_id.property_account_payable_id.id,
                'partner_id': self.partner_id.id,
                'comment': self.notes,
            })
        self.write({'invoice_id':invoice.id})
        for rec in self.stock_transfer_lines:
            if rec.product_id.property_account_income_id:
                account_id = rec.product_id.property_account_income_id.id
            elif rec.product_id.categ_id.property_account_income_categ_id:
                account_id = rec.product_id.categ_id.property_account_income_categ_id.id
            else:
                raise UserError(_('No account defined for product "%s".') % rec.product_id.name)
            invoice_line = InvoiceLine.create({
                        'invoice_id': invoice.id,
                        'name': rec.name,
                        'origin': rec.name,
                        'account_id': account_id,
                        'quantity': rec.product_qty,
                        'invoice_line_tax_ids': [(6, 0, [x.id for x in rec.product_id.supplier_taxes_id])],
                        'uom_id': rec.product_uom.id,
                        'price_unit': rec.price_unit,
                        'price_subtotal': rec.product_qty * rec.price_unit,
                        'product_id': rec.product_id and rec.product_id.id or False
                    })
        if any(line.invoice_line_tax_ids for line in invoice.invoice_line_ids) and not invoice.tax_line_ids:
            invoice.compute_taxes()

    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]

        # override the context to get rid of the default filtering on picking type
        result['context'] = {}
        # import pdb;pdb.set_trace()
        pick_ids = sum([order.picking_ids.ids for order in self], [])
        # choose the view_mode accordingly
        if len(pick_ids) != 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result

    @api.multi
    def action_view_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': self.invoice_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': self.invoice_id.id,
            'target': 'current',
            'domain': [('id', '=', self.invoice_id.id)],
            'context': {'active_id': self.invoice_id.id},  
        }

    @api.multi
    def action_invoice_sent_to_headoffice(self):
        Invoice = self.invoice_id
        Invoice.ensure_one()
        template = Invoice.env.ref('account.email_template_edi_invoice', False)
        compose_form = Invoice.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=Invoice.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="account.mail_template_data_notification_email_account_invoice"
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


class StockUpdatelines(models.Model):

    _name = 'stock.update.lines'
    _description = 'stock update lines'

    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            total = line.product_qty * line.price_unit
            line.update({
                'price_subtotal': total,
            })

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_po_id.id or self.product_id.uom_id.id
            self.name = self.product_id.name
            self.price_unit = self.product_id.standard_price
            self.src_location_id = self.update_id.partner_id.property_stock_supplier.id

    update_id = fields.Many2one('stock.update', 'Lines', required=True, ondelete='cascade')
    name = fields.Text(string='Description', required=True)
    # product_id = fields.Many2one('product.product', string='Product', domain=['&',('state', 'in',['progress','done']),('purchase_ok','=',True)])
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)])
    product_qty = fields.Float(string='Quantity', required=True)
    price_unit = fields.Float(string='Unit Price', required=True)
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure', required=True)
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', store=True)
    dest_location_id = fields.Many2one('stock.location', 'Destination Location', default=lambda self: self.env.ref('stock.stock_location_stock').id)
    src_location_id = fields.Many2one('stock.location', 'Source Location')
    move_ids = fields.One2many('stock.move', 'stock_update_line_id', string='Reservation', readonly=True, ondelete='set null', copy=False)

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                continue
            qty = 0.0
            price_unit = line.price_unit
            for move in line.move_ids.filtered(lambda x: x.state != 'cancel'):
                qty += move.product_qty
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'date': line.update_id.date,
                'location_id': line.update_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.dest_location_id.id,
                'picking_id': picking.id,
                'partner_id': line.update_id.partner_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'stock_update_line_id': line.id,
                'price_unit': price_unit,
                'picking_type_id': line.update_id.picking_type_id.id,
                'origin': line.update_id.name,
                'route_ids': line.update_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.update_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id': line.update_id.picking_type_id.warehouse_id.id,
            }
            # Fullfill all related procurements with this  line
            diff_quantity = line.product_qty - qty
            
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done


class StockMove(models.Model):
    _inherit = 'stock.move'

    stock_update_line_id = fields.Many2one('stock.update.lines', string='stock update lines')
