# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	@api.depends('move_lines')
	def _compute_order_delivery(self):
		for picking in self:
		    sale_order = False
		    for move in picking.move_lines:
			if move.procurement_id.sale_line_id:
			    sale_order = move.procurement_id.sale_line_id.order_id
			    break
			picking.sp_delivery_name = sale_order.order_delivery_name if sale_order else False
#			picking.sp_delivery_address = sale_order.order_delivery_address if sale_order else False
#			picking.sp_delivery_phone = sale_order.order_delivery_phone if sale_order else False
	
	def _search_order_delivery(self, operator, value):
	        moves = self.env['stock.move'].search(
			[('picking_id', '!=', False), ('procurement_id.sale_line_id.order_id', operator, value)]
				)
		return [('order_delivery_name', 'in', moves.mapped('picking_id').ids)]


	sp_delivery_name = fields.Many2one(comodel_name='sale.order', string="B2C Order Delivery Name",
			                   compute='_compute_order_delivery', search='_search_order_delivery')
	sp_delivery_address = fields.Many2one(comodel_name='sale.order', string="B2C Order Delivery Address",
                                           compute='_compute_order_delivery', search='_search_order_delivery')
	sp_delivery_phone = fields.Many2one(comodel_name='sale.order', string="B2C Order Delivery Phone",
                                           compute='_compute_order_delivery', search='_search_order_delivery')

