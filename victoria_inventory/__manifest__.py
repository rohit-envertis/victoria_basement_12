# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria Inventory',
    'version': '12.0',
    'summary': 'Victoria Inventory Custom',
    'sequence': 7,
    'description': """
Victoria Inventory
==================
Inventory Custom
    """,
    'category': 'Inventory',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'stock',
        'victoria_product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_view.xml',
        'views/stock_update.xml',
        'report/requet_docket_report.xml',
        'report/requet_docket_report_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
