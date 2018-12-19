# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime

import odoo.addons.decimal_precision as dp


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_web_category = fields.Boolean(string='Is Web Category')
    categ_code = fields.Char(string='Category Code')
    logo = fields.Binary(string="Logo")
    displayy_name = fields.Char(string="Display Name")
    

class PriceUpdate(models.TransientModel):
    _name = 'price.update'
    _description = 'Price Update'

    new_price = fields.Float(string='Now Price')
    current_price = fields.Float(string='Current Price')
    product_id = fields.Many2one('product.product', string='Product')
    product_tmpl_id = fields.Many2one('product.template', string='Template')
    product_variant_count = fields.Integer(string='Variant Count', related='product_tmpl_id.product_variant_count')

    @api.model
    def default_get(self, fields):
        res = super(PriceUpdate, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.template' and self.env.context.get('active_id'):
            product = self.env['product.product'].search([('product_tmpl_id', '=', self.env.context['active_id'])],
                                                         limit=1)
            res['product_id'] = product.id
            res['current_price'] = product.list_price
        elif not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.product' and self.env.context.get('active_id'):
            product = self.env['product.product'].browse(self.env.context['active_id'])
            res['product_id'] = product.id
            res['current_price'] = product.lst_price
        return res

    @api.multi
    def change_product_price(self):
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'product.template' and \
                self.env.context.get('active_id'):
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', self.env.context['active_id'])],
                                                            limit=1)
        elif self.env.context.get('active_id') and self.env.context.get('active_model') == 'product.product' and \
                self.env.context.get('active_id'):
            product_id = self.env['product.product'].browse(self.env.context['active_id'])
        # vals = {
        #     'new_price': self.new_price,
        #     'changed_date': datetime.now(),
        #     'old_price': self.current_price,
        #     'price_history_id': product_id.id,
        #     'user_id': self.env.user.id,
        # }
        product_id.write({'list_price': self.new_price})
        # self.env['price.history'].create(vals)
        return {'type': 'ir.actions.act_window_close'}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # state = fields.Selection([('new', 'New'), ('progress', 'In Progress'), ('done', 'Done')], default='new',
    # string='State')
    brand_id = fields.Many2one('product.brand', string='Brand')
    own_product = fields.Boolean(string='Own Product')
    track_activity = fields.Boolean(string='Track Activity')
    title = fields.Char(string='Title', translate=True)
    title1 = fields.Char(string='Title', translate=True)
    category_name = fields.Char(string='Category Name', store=True)
    keyword = fields.Char(string='Keyword')
    meta_description = fields.Text(string='Meta Description', translate=True,
        help="A precise description of the Product, used only for internal information purposes.")
    web_category_id = fields.Many2one('product.web.category', string='Web Category')
    max_discount = fields.Float(string='Max Discount (%)', default=0.0)
    price_history_ids = fields.One2many('price.history', 'price_history_id', string='Price History')
    publish_on_website = fields.Boolean(string='Visible in Website', copy=False)
    list_price = fields.Float(string='Sale Price', default=1.0, digits=dp.get_precision('Shop Price'),
                              help="Base price to compute the customer price. Sometimes called the catalog price.")
    lst_price = fields.Float(string='Public Price', related='list_price', digits=dp.get_precision('Shop Price'))
    standard_price = fields.Float(string='Cost', compute='_compute_standard_price', inverse='_set_standard_price',
                                  search='_search_standard_price', digits=dp.get_precision('Purchase Price'),
                                  groups="base.group_user",
                                  help="Cost of the product, in the default unit of measure of the product.")
    rrp = fields.Float(string='R.R.P.', default=1.0, digits=dp.get_precision('Shop Price'))
    price_label = fields.Selection([('shop', 'Shop Price'), ('hot', 'Hot Price')], default='shop',
                                   string='Which price you want to show?')
    start_date = fields.Date(string='Start Date', copy=False)
    end_date = fields.Date(string='End Date', copy=False)
    cartoon_qty = fields.Float(string='Quantity per Cartoon',
                               help="The total number of products you can have per cartton.")
    inner_qty = fields.Float(string='Inner Quantity')
    discount_price = fields.Float(string='Discounted Price')
    dicount_price_type = fields.Selection([('none', 'None'),('hot', 'Hot Price'),
                                           ('chopped', 'Chopped Price'),
                                           ('basement', 'Basement Price')],
                                          string='Dicounted Price Type', default='none')
    height = fields.Float(string='Height')
    width = fields.Float(string='Width')
    depth = fields.Float(string='Depth')
    landed_cost = fields.Float(string='Landed Cost', digits=dp.get_precision('Landed Price'))
    style_id = fields.Many2one('product.style', string='Styles')
    product_set = fields.Char(string='Set')
    made_in = fields.Char(string='Made In')
    store_only = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Store Only')
    long_description = fields.Text(string='Long Description', translate=True)
    induction = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Induction')
    halogen = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Halogen')
    gas = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Gas')
    electric = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Electric')
    oven = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Oven')
    dish_wash = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Dishwash')
    free_shipping = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Free Shipping')
    feature = fields.Html(string="Features")
    benefits = fields.Html(string="Benefits")
    contain = fields.Html(string="Contain")
    faq = fields.Html(string="Frequently Asked Questions")
    campaign = fields.Char(string='Campaign')
    sw_featured = fields.Boolean(string='Sw Featured')
    special_flag = fields.Boolean(string='Special Flag')
    special_week = fields.Boolean(string='Special Week')
    new_arrival = fields.Boolean(string='New Arrival')
    free_delivery = fields.Boolean(string='Free Delivery')
    on_sale = fields.Boolean(string='On Sale')
    color_code = fields.Char(string='Color Code')
    capacity = fields.Char(string='Capacity')
    components = fields.Text(string='Components')
    collections = fields.Char(string='Collections')
    cover = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Cover')
    interior = fields.Char(string='Interior')
    handle = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Handle')
    stovetop = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Stovetop')
    microwave = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Microwave')
    fridge = fields.Selection([('Yes', 'Yes'), ('No', 'No')], default='No', string='Fridge')
    hand_wash = fields.Selection([('Yes', 'Yes'), ('No', 'No')],default='No', string='Hand Wash')
    temperature = fields.Char(string='Temperature')
    suitability = fields.Char(string='Suitability')
    warranty = fields.Char(string='Warranty')
    voltage = fields.Char(string='Voltage')
    wattage = fields.Char(string='Wattage')
    instruction_booklet = fields.Binary(string="Instruction Booklet")
    instruction_booklet_name = fields.Char(string='File Name')
    diameter = fields.Char(string='Diameter')
    discount_percent = fields.Float(string="Discount %")
    mpn = fields.Char(string='MPN',
                      help="Manufacturer Part Numbers to help buyers quickly find the items they’re looking for")
    gtin = fields.Char(string='GTINs',
                       help=" Global Trade Item Numbers to help buyers quickly find the items they’re looking for")
    product_tree_name = fields.Char(string='Product Tree', compute='_compute_tree_name')
    description = fields.Html(string="Description")
    material = fields.Char(string='Materials')
    stock_code = fields.Char(string='Stock Code')
    video_url = fields.Char(string='Video Url')

    def _compute_tree_name(self):
        for line in self:
            name = ''
            if line.brand_id:
                name = ''+line.brand_id.name + ' - '
            name += line.name
            line.update({'product_tree_name': name})
    
    @api.onchange('discount_price', 'list_price')
    def onchange_discount_price(self):
        for line in self:
            if line.discount_price and line.list_price:
                line.discount_percent = (1 - line.discount_price/line.list_price) * 100
    

    # @api.multi
    # def publish_on_website_button(self):
    #     for record in self:
    #         record.publish_on_website = not record.publish_on_website

    @api.onchange('categ_id')
    def get_the_name_for_filter(self):
        if self.categ_id.parent_id :
            self.category_name = self.categ_id.parent_id.name + '/' + self.categ_id.name
        else:
            self.category_name = self.categ_id.name

    @api.multi
    def write(self, vals):
        for rec in self:
            # product_id = self.env['product.product'].search([('product_tmpl_id', '=', rec.id)], limit=1)
            if 'list_price' in vals:
                values = {
                    'new_price': vals.get('list_price'),
                    'changed_date': datetime.now(),
                    'old_price': rec.list_price,
                    'price_history_id': rec.id,
                    'user_id': self.env.user.id
                }
                self.env['price.history'].create(values)
        return super(ProductTemplate, self).write(vals)

    @api.onchange('name', 'default_code')
    def onchange_name(self):
        if self.name:
            self.title = self.name + ' - Victoria basement'
        if self.default_code:
            self.keyword = self.default_code


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     print("\n\n\n\n-----------------------name", name, args)
    #     res = super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)
    #     print("\n\n\n\n\---------->>>>>>>>>>res", res)
    #     return res
    #
    # @api.multi
    # def name_get(self):
    #
    #     res = super(ProductProduct, self).name_get()
    #     print("\n\n\n\n--------->>>>>>>", res)
    #     return res

    suggested_products = fields.Many2many('product.product', 'suggested_product', 'product_id', 'suggest_product_id',
                                          string='Suggested Products')
    # price_history_ids = fields.One2many('price.history', 'price_history_id', 'Price History')
    standard_price = fields.Float(string='Cost', company_dependent=True, digits=dp.get_precision('Purchase Price'),
                                  groups="base.group_user",
                                  help="Cost of the product template used for standard stock valuation in accounting "
                                       "and used as a base price on purchase orders. Expressed in the default "
                                       "unit of measure of the product.")
    # lst_price = fields.Float(
    #     'Sale Price', compute='_compute_product_lst_price',
    #     digits=dp.get_precision('Sale Price'), inverse='_set_product_lst_price',
    #     help="The sale price is managed from the product template. Click on the 'Variant Prices' button "
    #          "to set the extra attribute prices.")
    alt_barcode = fields.Char(string='Alt Barcode', copy=False, help="International Alternet Article Number used "
                                                                     "for product identification.")

    @api.onchange('name', 'default_code')
    def onchange_product_name(self):
        if self.name:
            self.title = self.name + ' - Victoria basement'
        if self.default_code:
            self.keyword = self.default_code


class PriceHistory(models.Model):
    _name = 'price.history'
    _description = 'Price History'
    _order = 'changed_date'

    old_price = fields.Float(string='Was Price', digits=dp.get_precision('Sale Price'))
    new_price = fields.Float(string='Now Price', digits=dp.get_precision('Sale Price'))
    changed_date = fields.Datetime(string='Date')
    price_history_id = fields.Many2one('product.template', string='Product')
    user_id = fields.Many2one('res.users', string='Responsible')
    # template_history_id = fields.Many2one('product.template', 'Product')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # @api.onchange('price_unit')
    def onchange_price_unit(self):
        if not self.product_id:
            return
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)
        price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, self.product_id.supplier_taxes_id,
                                                                     self.taxes_id) if seller else 0.0
        if price_unit > 0.0 and self.price_unit > price_unit:
            return False
        return True

    _constraints = [
        (onchange_price_unit, 'Product Purchase Price should be less than Contract Price', ['price_unit']),
    ]


class ProductFeature(models.TransientModel):
    _name = "product.feature.wizards"
    _description = 'Product Feature'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    feature = fields.Html(string="Features", sanitize_attributes=False)

    @api.model
    def default_get(self, fields):
        res = super(ProductFeature, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.product' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].browse(self.env.context['active_id']).id
            res['feature'] = self.env['product.product'].browse(self.env.context['active_id']).feature
        return res

    @api.multi
    def change_feature(self):
        for wizard in self:
            feature = wizard.feature
            wizard.product_id.write({'feature': feature})
            return {'type': 'ir.actions.act_window_close'}


class ProductBenefits(models.TransientModel):
    _name = "product.benefit.wizards"
    _description = 'Product Benefits'


    product_id = fields.Many2one('product.product', string='Product', required=True)
    benefit = fields.Html(string="Benefits", sanitize_attributes=False)

    @api.model
    def default_get(self, fields):
        res = super(ProductBenefits, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.product' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].browse(self.env.context['active_id']).id
            res['benefit'] = self.env['product.product'].browse(self.env.context['active_id']).benefits
        return res
        
    @api.multi
    def change_benefit(self):
        for wizard in self:
            benefit = wizard.benefit
            wizard.product_id.write({'benefits': benefit})
            return {'type': 'ir.actions.act_window_close'}


class ProductContains(models.TransientModel):
    _name = "product.contain.wizards"
    _description = 'Product Contains'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    contain = fields.Html(string="Contains", sanitize_attributes=False)

    @api.model
    def default_get(self, fields):
        res = super(ProductContains, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.product' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].browse(self.env.context['active_id']).id
            res['contain'] = self.env['product.product'].browse(self.env.context['active_id']).contain
        return res
        
    @api.multi
    def change_contain(self):
        for wizard in self:
            contain = wizard.contain
            wizard.product_id.write({'contain': contain})
            return {'type': 'ir.actions.act_window_close'}


class ProductFaq(models.TransientModel):
    _name = "product.faq.wizards"
    _description = 'Product Faq'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    faq = fields.Html(string="Features", sanitize_attributes=False)

    @api.model
    def default_get(self, fields):
        res = super(ProductFaq, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.product' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].browse(self.env.context['active_id']).id
            res['faq'] = self.env['product.product'].browse(self.env.context['active_id']).faq
        return res
        
    @api.multi
    def change_faq(self):
        for wizard in self:
            faq = wizard.faq
            wizard.product_id.write({'faq': faq})
            return {'type': 'ir.actions.act_window_close'}


class ProductDescription(models.TransientModel):
    _name = "product.description.wizards"
    _description = 'Product Description'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    description = fields.Html(string="Features", sanitize_attributes=False)

    @api.model
    def default_get(self, fields):
        res = super(ProductDescription, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'product.product' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].browse(self.env.context['active_id']).id
            res['description'] = self.env['product.product'].browse(self.env.context['active_id']).description
        return res
        
    @api.multi
    def change_description(self):
        for wizard in self:
            description = wizard.description
            wizard.product_id.write({'description': description})
            return {'type': 'ir.actions.act_window_close'}
