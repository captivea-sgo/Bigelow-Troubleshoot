# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class FinishedGoods(models.Model):  
    _name = 'finished.goods'
    
    product_id = fields.Many2one('product.product',string="Product",readonly=True)
    product_qty = fields.Float('Quantity',default=1)
    finished_workorder_id = fields.Many2one('mrp.workorder',string="Workorder")
    secondary_workorder_id = fields.Many2one('mrp.workorder',string="Secondary Workorder")
    byproduct_workorder_id = fields.Many2one('mrp.workorder',string="Byproduct Workorder")
    lot_id = fields.Many2one('stock.production.lot',string="Lot")
    title = fields.Char(string="Title")
    result = fields.Char(string="Result")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: