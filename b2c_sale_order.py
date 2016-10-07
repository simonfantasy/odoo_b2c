# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api, _
from openerp.exceptions import UserError
import datetime
from openerp.tools.misc import xlwt
import re
from cStringIO import StringIO  # not necessary

class SaleOrder(models.Model):
    _inherit = 'sale.order'	
    order_delivery_name = fields.Char(string='B2C order delivery name', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_address = fields.Char(string='B2C order delivery address', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_phone = fields.Char(string='B2C order delivery phone', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    b2c_flag = fields.Boolean(related='partner_id.b2c_flag', string="B2C Order", readonly=True, help='Is this for a B2C transactions?')
        # 添加字段， 只要客户属于B2C，则订单属于B2C，用于筛选条件,用于view的字段可视
    b2c_delivery_notify = fields.Boolean(string='B2C delivery notified？', default=False, readonly=True)


    @api.multi
    def search_sale_order_date_range(self, start_datetime=0, day_offset=0, range=0):
        # 筛选一定时间范围内的SO，默认为系统当天，NOTE：所有时间为本地时间，时间参数为string 'YYYY-MM-DD HH:MM:SS'
        # range =  [ start_time - day_offset ->  + range]
        # 其他参数单位为days, range=0 则以当前时刻为end_datetime
        # default: start_time: 当天00:00:00；  day_offset: 0 days,  end_time: 当前时刻
        if start_datetime is 0:
            start_datetime = fields.Date.context_today(self)+' 00:00:00'
            # NOTE: context_today的参数在函数参数里没法调用，因此用这样的方法来定义默认参数
            #       默认开始时间为当天 00:00:00
        d_format = "%Y-%m-%d %H:%M:%S"
        if day_offset:
            start_datetime=datetime.datetime.strftime(
                datetime.datetime.strptime(start_datetime, d_format) - datetime.timedelta(days=day_offset), d_format)
            # NOTE：使用参数day_offset来向前偏移天数，支持小数
            #       可以不输入start_datetime参数，用day_offset作为昨天、前天、10天前的输入
        if not range:
            end_datetime = datetime.datetime.strftime(
                fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()),d_format)
        else:
            sec_range = range*24*3600 - 0.0001   #timedealta使用秒作为输入，默认= 1天-0.1us，range整数天数结束时不跨天
            end_datetime = datetime.datetime.strftime(
                datetime.datetime.strptime(start_datetime, d_format) + datetime.timedelta(0, sec_range), d_format)
        order = self.env['sale.order'].sudo().search([])
        order_list = self.env['sale.order']   # self.env to create an  empty recordset
        for record in order:
            order_time_cst = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self, timestamp=fields.Datetime.from_string(record.date_order)))
            if start_datetime <= order_time_cst <= end_datetime:
                order_list += record
        return [order_list, start_datetime, end_datetime]


    @api.multi
    def filter_sale_order_b2c(self, order):
        order_list = order
        for record in order:
            if not record.b2c_flag:
                order_list -= record
        return order_list


    def write_xls(self, c_fields, rows):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(u'B2C订单发运信息汇总')

        for i, fieldname in enumerate(c_fields):    # c_fields是列名的list
            worksheet.write(0, i, fieldname)
            worksheet.col(i).width = 300*len(fieldname)    # 按照列名长度设置列宽  BAD

        base_style = xlwt.easyxf('align: wrap yes, vert centre, horiz center')
        date_style = xlwt.easyxf('align: wrap yes, vert centre, horiz center', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes, vert centre, horiz center', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = base_style                         # 判断value的类型，用不同的style
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)  # re.sub实现正则替换， 把回车换成空格
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                worksheet.write(row_index + 1, cell_index, cell_value, cell_style)   # +1的意思是c_fields已经占了第一行

        workbook.save('save.xls')
        return workbook


########################### For testing purpose: #################3

    @api.multi
    def show_something(self):  # for study purpose, the first method  # for the show env button
        for order in self:
            #order.show_all_sale_order_search()
            # order.show_all_date_time()     # Case 1
            # order.show_order_line()       # Case 2

            ## Case for SO_search_time test
            # show = order.search_sale_order_date_range()
            # show_b2c = order.filter_sale_order_b2c(show[0])
            # raise UserError(_("Returned SO: %s\n\n "
            #                   "Start: %s \n\n End: %s \n\n "
            #                   "Filter b2c SO: %s \n") %
            #                 (show[0],show[1],show[2],show_b2c) )


            #Case for write_xls test
            cfields = ['col-1','col-2','col-3','col-4','col-5']
            rrows = [ ['11','12','13','14','15'],
                     ['21','22','23','24','25']]
            workbook = order.write_xls(cfields, rrows)
            raise UserError(_("workbook: \n%s") % (workbook))



    @api.multi
    def show_all_sale_order_search(self):
        names = self.env['sale.order'].sudo().search([])
        list = '\n'
        for partner in names:
            list += str(partner.id) + ' ' + partner.name + '\n'
        raise UserError(_("self.env.search.List: %s \n\n List.id:List.name: %s \n\n "
                          "uid: %s \n\n cr: %s \n\n context: %s \n\n context['tz']: %s \n\n "
                          "type of record: %s") % \
                        (names, list, self.env.uid, self.env.cr,
                         self.env.context, self.env.context['tz'], type(names)))


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


################# Testing purpose done: ##############################



class ResPartner(models.Model):
    _inherit = 'res.partner'
    b2c_flag = fields.Boolean(string='B2C ONLY', required=False, default=False,
                              help='Is this for a B2C transactions?', readonly=True)


    @api.one
    def action_confirm_b2c(self):
        # if partner.create_uid == self.env.user.id:
        # if self.create_uid.id == self.env.user.id:
        for partner in self:
            if partner.b2c_flag is False and partner.customer:
                # self.write({"b2c_flag": True})
                partner.b2c_flag = True
         # raise UserError(_('%s,%s,%s') % \
         #                 (self.create_uid.id,self.env.user.id,self.b2c_flag))   #for test only


    @api.one
    def action_delete_b2c(self):
        # if partner.create_uid == self.env.user.id:
        # if self.create_uid.id == self.env.user.id:
        for partner in self:
            if partner.b2c_flag and partner.customer:
                # self.write({"b2c_flag": False })
                partner.b2c_flag = False

