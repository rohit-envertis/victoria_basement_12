# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria POS',
    'version': '12.0',
    'summary': 'Victoria POS Custom',
    'sequence': 8,
    'description': """
Victoria POS
================
Point Of Sale Customization
    """,
    'category': 'Point Of Sale',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'point_of_sale',
        'victoria_product',
        'victoria_stock',
        'victoria_profile',
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/pos_shop_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_move_view.xml',
        'views/purchase_view.xml',
        'views/report_saledetails.xml',
       
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

