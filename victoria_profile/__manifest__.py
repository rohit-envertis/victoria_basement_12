# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria Profile',
    'version': '12.0',
    'summary': 'Victoria Profile',
    'sequence': 1,
    'description': """
Victoria Profile
=========================
Setup Victoria's Basement
    """,
    'category': 'Victoria',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'crm',
        'point_of_sale',
        'stock_account',
        'barcodes',
    ],
    'data': [
        'security/security_victoriya_group.xml',
        'data/data.xml',
        'data/victoria_product_data.xml',
        'views/victoria_config_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
