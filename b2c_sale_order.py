# -*- coding: utf-8 -*-
#!/usr/bin/env python
from openerp import models, fields, api, _
from openerp.exceptions import UserError
import datetime
from openerp.tools.misc import xlwt
import re
import shutil
import base64
from cStringIO import StringIO  # not necessary
import os


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_delivery_name = fields.Char(string='B2C order delivery name', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_address = fields.Char(string='B2C order delivery address', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    order_delivery_phone = fields.Char(string='B2C order delivery phone', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    b2c_flag = fields.Boolean(related='partner_id.b2c_flag', string="B2C Order", readonly=True, help='Is this for a B2C transactions?')
        # 添加字段， 只要客户属于B2C，则订单属于B2C，用于筛选条件,用于view的字段可视
    b2c_delivery_notify = fields.Boolean(string='B2C delivery notified？', readonly=True)
    b2c_sales_notify = fields.Boolean(string='B2C sales notified？', readonly=True)


    @api.model
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


    @api.model
    def filter_sale_order_b2c(self, order):
        return order.filtered('b2c_flag')


    def write_xls(self, c_fields, rows, filename=0, sheet=[], xls_path=''):
        if not filename:
            filename = 'Export-' + datetime.datetime.strftime(
                fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()), '%Y%m%d-%H.%M.%S')\
                     +'.xls'

        if not xls_path:
            xls_path = self.env['ir.config_parameter'].search([('key', '=', 'xls_path')]).value

        os.chdir(xls_path)  # todo add Exceptions

        if not sheet:
            sheet.append('Sheet 1')

        workbook = xlwt.Workbook()
        for sheetname in sheet:
            worksheet = workbook.add_sheet(sheetname)

        base_style = xlwt.easyxf('align: wrap yes, vert centre, horiz center')
        date_style = xlwt.easyxf('align: wrap yes, vert centre, horiz center', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes, vert centre, horiz center', num_format_str='YYYY-MM-DD HH:mm:SS')

        for i, fieldname in enumerate(c_fields[0]):    # c_fields是列名的list , 列宽的list
            worksheet.write(0, i, fieldname, base_style)
            worksheet.col(i).width = c_fields[1][i]   # 设置列宽

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

        workbook.save(filename.encode('utf-8'))


    @api.model
    def update_b2c_customer_list(self):
        partner = self.env['res.partner'].sudo().search([('customer', '=', True),('b2c_flag', '=', True)])
        b2c_list = partner.mapped(lambda r: [r.id, r.name, r.email])
        return b2c_list


    @api.model
    def create_b2c_notification(self):
        obj = self.env['sale.order']
        attach_obj = self.env['ir.attachment']
        b2c_list = obj.update_b2c_customer_list()
        order_in_date = obj.search_sale_order_date_range()  #全局搜索在日期范围内的订单
        order = obj.filter_sale_order_b2c(order_in_date[0])    # 对搜索订单结果进行二次筛选出B2C订单
        # excel_field = {  # 用于导出Excel的订单字段， 对象field : Excel列名, Excel列宽
        #     'name': [ u'订单编号', 2500],
        #     'date_order': [u'订单时间', 5500],
        #     'order_line.product_id.name': [u'产品名称', 6500],
        #     'order_line.product_qty': [u'产品数量', 2000],
        #     'order_delivery_name': [u'收件人', 3000],
        #     'order_delivery_address': [u'收件地址', 20000],
        #     'order_delivery_phone': [u'收件电话', 6000]
        #     }    # 没用到
        excel_field_keys =['name', 'date_order', 'order_line.product_id.name', 'order_line.product_qty',
                           'order_delivery_name', 'order_delivery_address', 'order_delivery_phone' ]
        excel_field = [ [u'订单编号', u'订单时间', u'产品名称', u'产品数量', u'收件人', u'收件地址', u'收件电话'],
                        [ 2500, 5500, 6500, 2000, 3000, 12000, 4000] ]

        f_order = []
        rows = []
        # xls_path = './b2cxls/'

        for index, customer in enumerate(b2c_list):
            f_order.append(order.filtered(lambda r: (r.partner_id.id == customer[0]) and (r.b2c_delivery_notify == False)))
                #格式化的订单，按照订单客户分类，并只保留没通知发运的订单
                # NOTE: partner_id是个many2one类型，这样返回的是res.partner对象，必须用res.partner.id来做判断
            rows.append([])

            for i, record in enumerate(f_order[index]):
                if len(record.order_line) != 1:
                    break
                rows[index].append([])
                rows[index][i].append(record.name)
                order_date_cst = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(self, timestamp=fields.Datetime.from_string(record.date_order)))
                rows[index][i].append(order_date_cst)
                rows[index][i].append(record.order_line.product_id.name)
                rows[index][i].append(record.order_line.product_qty)
                rows[index][i].append(record.order_delivery_name)
                rows[index][i].append(record.order_delivery_address)
                rows[index][i].append(record.order_delivery_phone)

            if len(rows[index]):
                rows[index].append([])    # 最后加一个合计行
                formula = 'SUM(D2:D'+str(len(rows[index]))+')'  # -1 +1: -1是因为上面加了1行，+1是因为列名占了第一行
                count = 'COUNT(D2:D'+str(len(rows[index]))+')'
                rows[index][i+1].append(u'订单合计：')
                rows[index][i+1].append(xlwt.Formula(count))
                rows[index][i+1].append(u'数量合计：')
                rows[index][i+1].append(xlwt.Formula(formula))

                filename = b2c_list[index][1] + u'运单信息-' + datetime.datetime.strftime(
                    fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()), '%Y%m%d-%H.%M.%S')\
                     + '.xls'
                sheet = [ b2c_list[index][1] + u'运单' + datetime.datetime.strftime(
                    fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()), '%Y%m%d %H:%M:%S')]
                obj.write_xls(excel_field, rows[index], filename, sheet)

                full_filename = xls_path+filename
                shutil.move(filename, full_filename)
                f_order[index].write({"b2c_delivery_notify": True})

                #below: 把文件重新写到新建的ir.attachment里面
                f = open(full_filename, 'r')
                new_attach=attach_obj.create({ 'name': sheet[0],
                                    'type': 'binary',
                                    'datas': base64.encodestring(f.read()),
                                    'datas_fname': filename,
                                    'b2c': True,
                                    'b2c_sent': False,
                                    'b2c_email': customer[2]
                               })
                f.close()
                new_attach.res_id = new_attach.id   # 该attachment的resource是其本身



    @api.model
    def create_b2c_sales_summary(self):
        # obj = self.env['sale.order']
        # attach_obj = self.env['ir.attachment']

        b2c_sales_group_list = self.env['res.groups'].search([('name', '=', u'B2C sale agent')])   # b2c销售的访问组

        # b2c_sales_group_list.ensure_one()   不能用在这里，在scheduled action里用就出错，ensure_one()针对的是self
        b2c_user_list = b2c_sales_group_list.users       # 获得访问组里的用户, 如果上一条是multiple records, 这里会报错，不能赋值

        excel_field = [[u'订单编号', u'订单时间', u'产品名称', u'产品数量', u'单价', u'小计', u'收件人', u'收件地址', u'收件电话'],
                         [ 2500, 5500, 6500, 2000, 2500, 3000, 3000, 12000, 4000] ]

        order = self.env['sale.order'].search([('b2c_flag', '=', True), ('b2c_sales_notify', '=', False)])  # 全部的未汇总的b2c订单

        f_order = []
        rows = []
        # xls_path = './b2cxls/sale_order/'


        for index, salesman in enumerate(b2c_user_list):
            f_order.append(order.filtered(lambda r: r.user_id.id == salesman.id))
                #格式化的订单，按照订单销售分类，并只保留该销售的订单
                # NOTE: partner_id是个many2one类型，这样返回的是res.partner对象，必须用res.partner.id来做判断
            rows.append([])

            for i, record in enumerate(f_order[index]):
                # if len(record.order_line) != 1:
                #     break
                rows[index].append([])
                rows[index][i].append(record.name)
                order_date_cst = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(self, timestamp=fields.Datetime.from_string(record.date_order)))
                rows[index][i].append(order_date_cst)
                rows[index][i].append(record.order_line.product_id.name)
                rows[index][i].append(record.order_line.product_qty)
                rows[index][i].append(record.order_line.price_unit)
                rows[index][i].append(record.order_line.price_total)
                rows[index][i].append(record.order_delivery_name)
                rows[index][i].append(record.order_delivery_address)
                rows[index][i].append(record.order_delivery_phone)

            if len(rows[index]):
                rows[index].append([])    # 最后加一个合计行
                formula = 'SUM(D2:D'+str(len(rows[index]))+')'  # -1 +1: -1是因为上面加了1行，+1是因为列名占了第一行
                count = 'COUNT(D2:D'+str(len(rows[index]))+')'
                formula2 = 'SUM(F2:F'+str(len(rows[index]))+')'  # -1 +1: -1是因为上面加了1行，+1是因为列名占了第一行
                rows[index][i+1].append(u'订单合计：')
                rows[index][i+1].append(xlwt.Formula(count))
                rows[index][i+1].append(u'数量合计：')
                rows[index][i+1].append(xlwt.Formula(formula))
                rows[index][i+1].append(u'价格合计：')
                rows[index][i+1].append(xlwt.Formula(formula2))

                filename = u'{0}订单汇总-{1}.xls'\
                    .format(salesman.name.encode('utf-8'),  datetime.datetime.strftime(
                    fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()), '%Y%m%d-%H.%M.%S') )
                        # 这是个utf-8字符串，下面处理标准io时，因为python默认ascii，遇到中文可能出问题，需要注意
                        # 在write_xls里加入对filename.encode('utf-8")

                sheet = [salesman.name + u'订单汇总' + datetime.datetime.strftime(
                    fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now()), '%Y%m%d %H:%M:%S')]

                self.env['sale.order'].write_xls(excel_field, rows[index], filename, sheet)

                # full_filename = xls_path+filename
                # shutil.move(filename, full_filename)

                f_order[index].write({"b2c_sales_notify": True})

                #below: 把文件重新写到新建的ir.attachment里面
                f = open(filename.encode('utf-8'), 'r')
                new_attach = self.env['ir.attachment'].create({ 'name': sheet[0],
                                    'type': 'binary',
                                    'datas': base64.encodestring(f.read()),
                                    'datas_fname': filename.encode('utf-8'),
                                    'b2c': True,
                                    'b2c_sent': False,
                                    'b2c_email': salesman.email
                               })
                f.close()
                new_attach.res_id = new_attach.id   # 该attachment的resource是其本身



    @api.model
    def b2c_send_email(self):
        b2c_attachment_to_send = self.env['ir.attachment']. \
            search([('b2c', '=', True), ('b2c_sent', '=', False)])

        email_list = b2c_attachment_to_send.mapped('b2c_email')  # 用tosend的attachment中的email作为索引
        email_list = list(set(email_list))  # 合并相同邮件地址

        mail_template = self.env['mail.template'].search([('name', '=', 'B2C_Send_Mail')])

        for index, email_address in enumerate(email_list):
            attachment = b2c_attachment_to_send.filtered(lambda r: r.b2c_email == email_list[index])
            mail_dict = mail_template.generate_email(
                0)  # 返回的是mail字段字典 # mail.template用记录的resource，对应res_id的那个记录的report作为附件
            mail_dict['email_to'] = email_list[index]
            email = self.env['mail.mail'].create(mail_dict)
            email.mail_message_id.write({'attachment_ids': [(4, attachment.mapped('id'))]})

        b2c_attachment_to_send.write({'b2c_sent': True})


                ########################### For testing purpose: #################3

    @api.multi
    def show_something(self):  # for study purpose, the first method  # for the show env button
        for order in self:

           # # Test Case from xls file to ir.attachment
           #  f = open('./b2cxls/B2C运单信息-20161009-00.53.23.xls', 'r')
           #  attach_obj = self.env['ir.attachment']
           #  attach_obj.create({'name': 'b2c del',
           #                     'type': 'binary',
           #                     'datas': base64.encodestring(f.read()),
           #                     'datas_fname': 'B2C运单信息-20161009-00.53.23.xl'
           #                     })
           #  f.close()

            # order.show_all_sale_order_search()
            # order.show_all_date_time()     # Case 1
            # order.show_order_line()       # Case 2

            # # Case for SO_search_time test
            # show = order.search_sale_order_date_range()
            # show_b2c = order.filter_sale_order_b2c(show[0])
            # raise UserError(_("Returned SO: %s\n\n "
            #                   "Start: %s \n\n End: %s \n\n "
            #                   "Filter b2c SO: %s \n") %
            #                 (show[0],show[1],show[2],show_b2c) )

            # #Case for write_xls test
            # cfields = [['col-1','col-2','col-3','col-4','col-5'],[2500,5500,6500,5000,6000]]
            # rrows = [ ['11','12','13','14','15'],
            #           ['21','22','23','24','25'],
            #           [u'SO00134', u'2016-09-27 23:59:59.00', u'Propomax无酒精绿蜂胶30ml', u'200', u'xxx']]
            # workbook = order.write_xls(cfields, rrows)
            # raise UserError(_("workbook: \n%s") % (workbook))

            # Case for update_b2c_customer_list
            # l = order.update_b2c_customer_list()
            # raise UserError(_("B2C list:\n {0}\n".format(l)))

            # # # Case for create_b2c_notification
            # order.create_b2c_notification()
            # ## raise UserError(_("B2C List: \n {0} \n\n order: \n {1}\n\n rows:{2}".format(b2c_list, record, rows)))
            # ## When using write or create, no raise following, otherwise write or create not working


            # Case for email generating test
            # order.b2c_send_email()

            # pass

            # Case for b2c sale summary
            order.create_b2c_sales_summary()


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


    @api.multi
    def action_confirm_b2c(self):
        # if partner.create_uid == self.env.user.id:
        # if self.create_uid.id == self.env.user.id:
        for partner in self:
            if partner.b2c_flag is False and partner.customer:
                # self.write({"b2c_flag": True})
                partner.b2c_flag = True


    @api.multi
    def action_delete_b2c(self):
        # if partner.create_uid == self.env.user.id:
        # if self.create_uid.id == self.env.user.id:
        for partner in self:
            if partner.b2c_flag and partner.customer:
                # self.write({"b2c_flag": False })
                partner.b2c_flag = False



class IrAttachmentB2C(models.Model):
    _inherit = 'ir.attachment'


    b2c = fields.Boolean(string='B2C', help= 'A B2C order\'s delivery list', readonly=True, default= False)
    b2c_sent = fields.Boolean(string='B2C sent', readonly=True, default= False)
    b2c_email = fields.Char(string= 'B2C email', readonly=True)



