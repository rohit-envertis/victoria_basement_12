# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria Check Stock',
    'version': '12.0',
    'summary': 'Victoria Check Products Stock',
    'sequence': 10,
    'description': """
Victoria check current product stock
================
Product Custom
    """,
    'category': 'Stock',
    'website': 'https://www.envertis.com.au',
    'images': [],
    'depends': [
        'victoria_profile',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/product_stock_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
