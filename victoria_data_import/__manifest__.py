# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Victoria Data Import',
    'version' : '10.2007.10.27.0',
    'summary': 'Victoria Data Import',
    'sequence': 3,
    'description': """
Victoria Data Import
=============
Using script import product data.
    """,
    'category': 'Victoria',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'base', 'product', 'stock',
    ],
    'data': [
        # Datas
        'data/data.xml',
        # Views
        'views/product_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
