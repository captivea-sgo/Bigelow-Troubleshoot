# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class Custom_quality_check(models.Model):
    _name = 'custom.quality.check'
    
    product_id  = fields.Many2one('product.product',string="Product")
    quantity = fields.Float(string="Quantity")
    lot_id = fields.Many2one('stock.production.lot',string="Lot")
    workorder_id = fields.Many2one('mrp.workorder',string="Workorder")
    name = fields.Char(string="Name")


class Mrpworkorder(models.Model):
    _inherit = "mrp.workorder"

    custom_quality_check_id = fields.Many2one('custom.quality.check',string="Custom Quality Check")
    custom_compponent_id = fields.Many2one('product.product',related="custom_quality_check_id.product_id",string="Product")
    custom_lot_id = fields.Many2one('stock.production.lot',related="custom_quality_check_id.lot_id",string="Lot Custom",readonly=False)
    custom_quantity = fields.Float(string="Quantity Custom",related="custom_quality_check_id.quantity",readonly=False)
    custom_final_step = fields.Boolean(string="Final Step")
    custom_uom_id = fields.Many2one('uom.uom',string="UOM")
    custom_quality_check = fields.Boolean(string="Final",compute="_compute_custom_quality")
    name_quality_custom = fields.Char(related="custom_quality_check_id.name")
    actual_custom_quantity = fields.Float(string="Actual Qty",store=True)
    secondary_product_id_ids = fields.One2many('finished.goods', 'secondary_workorder_id')
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')], string="Tracking", help="Ensure the traceability of a storable product in your warehouse.", related="custom_compponent_id.tracking")
    

    def action_custom_done(self):
        res = super(Mrpworkorder,self).action_custom_done()
        producr_moves = self.production_id.move_finished_ids

        move_ids = []
        for move in producr_moves :
            if move.product_id.id == self.product_id.id :
                move_ids.append(move.id)

        for line in self.secondary_product_id_ids :
            move_val = {
                    'workorder_id' : self.id,
                    'product_id' : line.product_id.id,
                    'product_uom_qty' : line.product_qty,
                    'name' : self.production_id.name,
                    'product_uom' : line.product_id.uom_id.id,
                    'location_id' : line.product_id.property_stock_production.id,
                    'location_dest_id' : self.production_id.location_dest_id.id,
                    'production_id' : self.production_id.id
            }
            stock_move = self.env['stock.move'].sudo().create(move_val)
            line_vals = {'product_id' :line.product_id.id,
                        'product_uom_id' :line.product_id.uom_id.id,
                        'qty_done' : line.product_qty,
                        'move_id' : stock_move.id,
                        'location_id': line.product_id.property_stock_production.id,
                        'location_dest_id': self.production_id.location_dest_id.id,
                        'workorder_id': self.id,
                        'lot_id' : line.lot_id.id ,

            }
            
            stock_move_line = self.env['stock.move.line'].sudo().create(line_vals)
            move_ids.append(stock_move.id)
            stock_move.sudo()._action_confirm()
        self.production_id.move_finished_ids = [(6,0,move_ids)]
        return

        
    def action_next_custome(self) :
        title = 'Register ' + self.custom_quality_check_id.name + '(s) ' + '"' +self.custom_compponent_id.name +'"'
        if self.custom_lot_id.name : 
            result = self.custom_compponent_id.name + '-' + self.custom_lot_id.name  + ',' + str(self.custom_quantity) + self.custom_compponent_id.uom_id.name
        else : 
            result = self.custom_compponent_id.name  + ',' + str(self.custom_quantity) + self.custom_compponent_id.uom_id.name

        value = {
            'product_id' : self.custom_compponent_id.id,
            'product_qty': self.custom_quantity,
            'secondary_workorder_id' : self.id,
            'lot_id' :self.custom_lot_id.id,
            'title' :title,
            'result' :result,

            }

        secondary_product = self.env['finished.goods'].create(value)
        quality = self.env['custom.quality.check'].search([('workorder_id','=',self.id),('id','>',self.custom_quality_check_id.id)],limit=1)
        if quality.id :
            self.custom_quality_check_id = quality.id
            self.custom_quantity = quality.quantity
            self.actual_custom_quantity = quality.quantity
        else :
            self.custom_final_step = True
            self.custom_quality_check_id = False
        return

    @api.onchange('custom_quantity')
    def onchange_custom_quantity(self) :
        self.actual_custom_quantity = self.custom_quantity
        return

    def _compute_custom_quality(self):
        for line in self :
            if line.custom_quality_check_id :
                line.custom_quality_check = True
            else :
                line.custom_quality_check = False
        return


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def _generate_workorders(self, exploded_boms):
        workorders = self.env['mrp.workorder']
        res = super(MrpProduction,self)._generate_workorders(exploded_boms)
        workorders_res = self.env['mrp.workorder'].search([('production_id','=',self.id)],order="id desc", limit=1)
        if workorders_res :
            quality_list= []
            for bom,bom_data in exploded_boms :
                for line in bom.secondary_byproduct :
                    if line.product_id.tracking == 'none' or line.product_id.tracking == 'lot' : 
                        qty_second = 0
                        if bom.product_qty > 0 :
                            qty_second = line.product_planned_qty / bom.product_qty

                        quality_obj = self.env['custom.quality.check'].create({'product_id' : line.product_id.id,
                                                                'quantity' :qty_second * self.product_qty,
                                                                 
                                                                'workorder_id' : workorders_res.id,
                                                                'custom_uom_id' : line.product_uom_id.id,
                                                                'name' : 'Secondary' })

                        
                        quality_list.append(quality_obj.id)

                    else :
                        qty_second = 0
                        if bom.product_qty > 0 :

                            qty_second = line.product_planned_qty / bom.product_qty

                        for i in range(0,int(qty_second)):
                            quality_obj = self.env['custom.quality.check'].create({'product_id' : line.product_id.id,
                                                                'quantity' :1,
                                                                # 'lot_id' : lot_new,
                                                                'workorder_id' : workorders_res.id,
                                                                'custom_uom_id' : line.product_uom_id.id,
                                                                'name' : 'Secondary' })

                            quality_list.append(quality_obj.id)
                        

            quality_list.sort()
            if len(quality_list) > 0 :
                workorders_res.custom_quality_check_id = quality_list[0]

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: