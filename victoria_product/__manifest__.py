# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Victoria Product',
    'version' : '12.0',
    'summary': 'Victoria Product Custom',
    'sequence': 2,
    'description': """
Victoria Product
================
Product Custom
    """,
    'category': 'base',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'product',
        'stock',
        'victoria_profile',
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/product_product_view.xml',
        'views/product_brand_view.xml',
        'views/product_style_view.xml',
        'views/stock_level.xml',
        'views/webclient_templates.xml',
        'views/product_webcategory_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
