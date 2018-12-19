# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria Stock',
    'version': '12.0',
    'summary': 'Victoria Stock Custom',
    'sequence': 6,
    'description': """
Victoria Stock
================
Stock Custom
    """,
    'category': 'Warehouse',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'stock',
        'victoria_purchase',
    ],
    'data': [
        # Views
        'views/report_stock.xml',
        'views/stock_quant_view.xml',
        'views/stock_picking_view.xml',
        'wizard/views/wiz_change_location_view.xml',
        'views/res_company_view.xml',
        'report/delivery_report_menu.xml',
        'report/delivery_report_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

