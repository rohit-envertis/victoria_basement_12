# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria Purchases',
    'version': '12.0',
    'summary': 'Victoria Purchases Custom',
    'sequence': 5,
    'description': """
Victoria Purchases
======================
Purchase Customization
    """,
    'category': 'Purchases',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'stock_landed_costs',
        'victoria_product',
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'wizard/stock_price_update_views.xml',
        'views/purchase_brand.xml',
        'views/stock_landed_cost.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,


}