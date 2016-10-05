# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    sp_delivery_name = fields.Char(related='sale_id.order_delivery_name',string="B2C Order Delivery Name",readonly=True)
    sp_delivery_address = fields.Char(related='sale_id.order_delivery_address',string="B2C Order Delivery Address",readonly=True)
    sp_delivery_phone = fields.Char(related='sale_id.order_delivery_phone',string="B2C Order Delivery Phone",readonly=True)

    email_sign = fields.Boolean(string="Indication for B2C delivery information sent")
