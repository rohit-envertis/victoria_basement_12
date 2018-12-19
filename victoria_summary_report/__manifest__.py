# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Victoria Sales Report',
    'version': '12.0',
    'summary': 'Victoria Sales Report',
    'sequence': 4,
    'description': """
Victoria Sales
================
Sales Customization
    """,
    'category': 'Sales',
    'website': 'https://www.envertis.com.au',
    'images': [
    ],
    'depends': [
        'crm',
    ],
    'data': [
        'wizard/views/sale_wizard_view.xml',
        'wizard/report/sale_summary_menu.xml',
        'wizard/report/order_summary_report.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

