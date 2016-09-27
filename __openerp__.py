{
	  'name': 'B2C Modification',
	  'description':"""
Extend the B2C Flexibility:

1.销售订单增加b2c发货信息。

2.出库单关联上述字段

""",
	   'author': 'Simon Feng',
          'depends': ['sale_stock'],





	'data' : [
		'b2c_sale_order_view.xml',
		'b2c_stock_picking_view.xml',
#	'b2c_menu.xml',
	],
}


