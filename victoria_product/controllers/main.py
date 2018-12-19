# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class ProductBrand(http.Controller):                                                                                             

    @http.route(['/get_brand'], type='http', auth="public", website=True)
    def get_brand_json(self):
        brands = request.env['product.brand'].sudo().search([])
        data={}
        for brand in brands:
            url = ''
            brand_name = brand.name.strip()
            if brand.brand_url:
                url = brand.brand_url
            data.update({brand.id: [brand_name, url]})
        return json.dumps(data)


class ProductStyle(http.Controller):  

    @http.route(['/get_style_active'], type='http', auth="public", website=True)
    def get_style_active_json(self):
        # offset = nos * 100
        styles = request.env['product.style'].sudo().search([('active', '=', True)])
        data = {}
        host = '52.62.177.84'
        port = 80
        for style in styles:
            if style.web_enabled:
                url = ''
                if style.logo:
                    url = '%s://%s:%s/web/image?model=%s&id=%d&field=logo' % ('http', host, port, 'product.style',
                                                                              int(style.id))
                style_name = style.name.strip()
                code = style.stock_nos
                data.update({style.id: [style_name, url, style.category_id.id, code]})
                _logger.info('following data (%s)', (data,))
        return json.dumps(data)

    @http.route(['/get_style_inactive'], type='http', auth="public", website=True)
    def get_style_inactive_json(self):
        styles = request.env['product.style'].sudo().search([('active', '=', False)])
        data = {}
        host = '52.62.177.84'
        port = 80
        for style in styles:
            if style.web_enabled:
                url = ''
                if style.logo:
                    url = '%s://%s:%s/web/image?model=%s&id=%d&field=logo' % ('http', host, port, 'product.style',
                                                                              int(style.id))
                style_name = style.name.strip()
                data.update({style.id: [style_name, url, style.category_id.id]})
        return json.dumps(data)

    @http.route(['/get_stock_code'], type='http', auth="public", website=True)
    def get_stock_code_json(self):
        styles = request.env['product.style'].sudo().search([('active', '=', True)])
        data={}
        for style in styles:
            code = style.stock_nos
            data.update({style.id: [code]})
            _logger.info('following data (%s)', (data,))
        return json.dumps(data)