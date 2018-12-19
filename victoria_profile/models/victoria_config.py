# -*- coding: utf-8 -*-
from odoo import models, api

#
# class StockConfigurationSettings(models.TransientModel):
#     _inherit = 'stock.config.settings'

    # @api.onchange('group_stock_production_lot')  # Lots and Serial Numbers
    # def onchange_group_stock_production_lot(self):
    #     if self.group_stock_tracking_lot == 1:  # Packages
    #         self.warehouse_and_location_usage_level = 2  # Warehouses and Locations usage level
    #         # Option 3 : Manage several Warehouses, each one composed by several stock locations
    #     else:
    #         self.warehouse_and_location_usage_level = 1  # Warehouses and Locations usage level
    #         # Option 2 : Manage only 1 Warehouse, composed by several stock locations
