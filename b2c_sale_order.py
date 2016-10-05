# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api, _
from openerp.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'	
    order_delivery_name = fields.Char(string='B2C order delivery name',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_address = fields.Char(string='B2C order delivery address',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_phone = fields.Char(string='B2C order delivery phone',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    b2c_flag = fields.Boolean(related='partner_id.b2c_flag', string="B2C flag",readonly=True,help='Is this for a B2C transactions?')
        # 添加字段， 只要客户属于B2C，则订单属于B2C，用于筛选条件

    @api.multi
    def show_something(self):       # for study purpose
        names = self.env['sale.order'].sudo().search([])
        list = []
        for partner in names:
            list += (partner.id,partner.name)
        raise UserError(_("List: %s \n List.id:List.name:\n %s") % \
                        (names,list))


    @api.multi
    def show_something_order_line(self):  # for study purpose
        raise UserError(_('%s') % \
                        (self.order_line))




class ResPartner(models.Model):
    _inherit = 'res.partner'
    b2c_flag = fields.Boolean(string='B2C Flag',required=False,default=False,help='Is this for a B2C transactions?')


    @api.one
    def action_confirm_b2c(self):
        for partner in self:
            if partner.create_uid == self.env.user.id:
                partner.b2c_flag = True
        return ()
