# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api, _
from openerp.exceptions import UserError
import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'	
    order_delivery_name = fields.Char(string='B2C order delivery name', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_address = fields.Char(string='B2C order delivery address', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_phone = fields.Char(string='B2C order delivery phone', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    b2c_flag = fields.Boolean(related='partner_id.b2c_flag', string="B2C flag", readonly=True, help='Is this for a B2C transactions?')
        # 添加字段， 只要客户属于B2C，则订单属于B2C，用于筛选条件,用于view的字段可视

    @api.multi
    def show_something(self):       # for study purpose, the first method
        for order in self:
            #order.show_all_sale_order_search()
            #order.show_all_date_time()
            #order.show_order_line()
            order.search_sale_order_date_range()


    @api.multi
    def search_sale_order_date_range(self,start_datetime=fields.Date.today()+' 00:00:00',end_datetime=fields.Date.today()+' 23:59:59'):
        # 筛选一定时间范围内的SO，默认为系统当天，NOTE：所有时间为本地时间，两个参数为string 'YYYY-MM-DD HH:MM:SS'
        order = self.env['sale.order'].sudo().search([])
        list = '\n'
        for record in order:
            order_time_CST = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, timestamp=fields.Datetime.from_string(record.date_order)))
            # if order_time_CST >= start_datetime and order_time_CST <= end_datetime:
            #     list += record.name
            list += record.name + ' ' + order_time_CST + ' ' + record.date_order + '\n'
        raise UserError(_("Filtered Order.name: %s \n\n ") % (list))


    @api.multi
    def show_all_sale_order_search(self):
        names = self.env['sale.order'].sudo().search([])
        list = []
        for partner in names:
            list += (partner.id, partner.name)
        raise UserError(_("self.env.search.List: %s \n\n List.id:List.name: %s \n\n "
                          "uid: %s \n\n cr: %s \n\n context: %s \n\n context['tz']: %s \n") % \
                        (names, list, self.env.uid, self.env.cr,
                         self.env.context, self.env.context['tz']))


    @api.multi
    def show_all_date_time(self):
        for order in self:
            raise UserError(_("order.date_order: %s\n\n"
                              "order.create_date: %s\n\n"
                              "write_date:%s\n\n "
                              "datetime.datetime.now(): %s\n\n"
                              "datetime.now.strftime: %s \n\n"
                              "self.env.user.tz: %s \n\n"
                              "self.env.user.tz_offset: %s\n\n"
                              "fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()): %s\n\n"
                              "fields.Datetime.context_timestamp(self, timestamp=fields.Datetime.from_string(order.date_order)): %s") % \
                        (order.date_order,
                         order.create_date,
                         order.write_date,
                         datetime.datetime.now(),
                         datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         self.env.user.tz,
                         self.env.user.tz_offset,
                         fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()),
                         fields.Datetime.context_timestamp(self, timestamp=fields.Datetime.from_string(order.date_order))))
        # usage: show order dates and tzs



    @api.multi
    def show_order_line(self):  # for study purpose
        raise UserError(_('%s') % \
                        (self.order_line))




class ResPartner(models.Model):
    _inherit = 'res.partner'
    b2c_flag = fields.Boolean(string='B2C Flag', required=False, default=False,
                              help='Is this for a B2C transactions?', readonly=True)


    @api.multi
    def action_confirm_b2c(self):
        # if partner.create_uid == self.env.user.id:
        # if self.create_uid.id == self.env.user.id:
        for partner in self:
            if partner.b2c_flag is False and partner.customer:
                # self.write({"b2c_flag": True})
                partner.b2c_flag = True
         # raise UserError(_('%s,%s,%s') % \
         #                 (self.create_uid.id,self.env.user.id,self.b2c_flag))   #for test only

    @api.multi
    def action_delete_b2c(self):
        # if partner.create_uid == self.env.user.id:
        # if self.create_uid.id == self.env.user.id:
        for partner in self:
            if partner.b2c_flag and partner.customer:
                # self.write({"b2c_flag": False })
                partner.b2c_flag = False

