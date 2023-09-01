from odoo import api, fields, models, _
from datetime import datetime


class DummyOrders(models.Model):
    _name = 'dummy.orders'
    _description = 'Dummy Orders'

    name = fields.Char('Description')
    session_id = fields.Many2one('pos.session', 'Session')
    order_date = fields.Datetime('Date Order')
    order_line = fields.One2many('dummy.orders.line', 'dummy_orders_id', 'Orders')
    salesman = fields.Char('Salesman')
    reason = fields.Text('Reason')

    def create_to_all_order(self, orders, context=None):
        dummy_orders_obj = self.pool.get('dummy.orders')
        order_line = []

        for line in orders[0]['data']['lines']:
            product_line = [0] * 3
            product_line[0] = 0
            product_line[1] = False
            product_line[2] = {'product_id': line[2]['product_id'],
                               'quantity': line[2]['qty'],
                               'unit_price':line[2]['price_unit'],
                               'discount': line[2]['discount'],
                               'subtotal': (line[2]['qty'] * line[2]['price_unit']) - ((line[2]['qty'] * line[2]['price_unit']) * (line[2]['discount'] * 0.01)),
                               }
            order_line.append(product_line)

        vals = {'order_line': order_line,
                'session_id': orders[0]['data']['pos_session_id'],
                'order_date': datetime.today(),
                'reason': orders[0]['data']['reason'],
                'salesman': orders[0]['data']['destroy_user']}

        dummy_orders_obj.create(vals)


class AllOrdersLine(models.Model):
    _name = 'dummy.orders.line'
    _description = 'Dummy Orders Line'

    product_id = fields.Many2one('product.template', 'Product')
    dummy_orders_id = fields.Many2one('dummy.orders', 'Order')
    quantity = fields.Float('Quantity')
    unit_price = fields.Float('Unit Price')
    discount = fields.Float('Discount(%)')
    subtotal = fields.Float('Subtotal w/o Tax')
