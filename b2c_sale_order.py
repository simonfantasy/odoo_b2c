# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'	
    order_delivery_name = fields.Char(string='B2C order delivery name')
    order_delivery_address = fields.Char(string='B2C order delivery address')
    order_delivery_phone = fields.Char(string='B2C order delivery phone')
