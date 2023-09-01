import collections

from odoo import fields, api, models
from odoo.osv.expression import AND
from datetime import timedelta, date
from datetime import datetime
import datetime

import pytz


class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    pos_config_ids = fields.Many2many('pos.config', 'pos_detail_configs', default="")
    start_date = fields.Datetime(required=True,
                                 default=datetime.datetime.now().replace(hour=23, minute=00, second=00) - timedelta(
                                     days=2))
    end_date = fields.Datetime(required=True, default=datetime.datetime.now().replace(hour=16, minute=59, second=59) - timedelta(
                                     days=1))

    def generate_report(self):
        location_name = []
        for loc in self.pos_config_ids:
            location_name.append(loc.name)
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': location_name}
        return self.env.ref('pos_report.sale_details_report_customize').report_action([], data=data)


'''  Create new model based on the original template  '''


class PosReport(models.AbstractModel):
    _name = "report.pos_report.report_sale"

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):

        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]

        if (session_ids):
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                # start by default today 00:00:00
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                # avoid a date_stop smaller than date_start
                if (date_stop < date_start):
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                # stop by default today 23:59:59
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                          [('date_order', '>=', fields.Datetime.to_string(date_start)),
                           ('date_order', '<=', fields.Datetime.to_string(date_stop))]
                          ])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        orders = self.env['pos.order'].search(domain)

        user_currency = self.env.company.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(
                        line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty,
                        product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount': 0.0, 'base_amount': 0.0})
                        taxes[tax['id']]['tax_amount'] += tax['amount']
                        taxes[tax['id']]['base_amount'] += tax['base']
                else:
                    taxes.setdefault(0, {'name': ('No Taxes'), 'tax_amount': 0.0, 'base_amount': 0.0})
                    taxes[0]['base_amount'] += line.price_subtotal_incl

        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                    SELECT method.name, sum(amount) total
                    FROM pos_payment AS payment,
                         pos_payment_method AS method
                    WHERE payment.payment_method_id = method.id
                        AND payment.id IN %s
                    GROUP BY method.name
                """, (tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []

        return {
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'payments': payments,
            'company_name': self.env.company.name,
            'taxes': list(taxes.values()),
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'uom': product.uom_id.name
            } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }

    '''  Get Report Values from Receipt Orders  '''

    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        start_date = datetime.datetime.strptime(data['date_start'], '%Y-%m-%d %H:%M:%S')
        end_date = datetime.datetime.strptime(data['date_stop'], '%Y-%m-%d %H:%M:%S')
        print_date = datetime.datetime.now().strftime("%m/%d/%Y")
        location = data['config_ids']
        model_order = self.env['pos.order'].search([])
        i = 1
        product_qty = number_customer = return_value = 0
        id = None
        amount_total_order_lst, tax_lst, discount_lst, lst_receipt = [], [], [], []
        column_lst, sub_total_lst, total_column_discount, payments = [], [], [], []
        dic, product_category, lst_payment = {}, {}, {}
        payment_method = ""
        total_morning = total_afternoon = total_evening = 0
        r_morning = r_afternoon = r_evening = 0
        n_morning = n_afternoon = n_evening = 0

        # Start Restaurant Hotel Card ==================
        hotel_column_lst, hotel_total_tax, hotel_sale_total, hotel_total_column_discount = [], [], [], []
        hotel_dict, hotel_product_category = {}, {}
        hotel_total_qty = hotel_tax_cal = hotel_subtotal_cal = 0
        is_restaurant = False
        act_domain = [
            ("o_date", ">=", start_date),
            ("o_date", "<=", end_date),
            ('state', '=', 'done'),
        ]
        hotel_card_order = self.env['hotel.restaurant.order'].search(act_domain)
        # --------------------------

        # Start Activity Hotel Card ==================
        activity_column_lst, activity_total_tax, activity_sale_total, activity_total_column_discount = [], [], [], []
        activity_dict, activity_product_category = {}, {}
        activity_total_qty = activity_tax_cal = activity_subtotal_cal = 0
        is_activity = False
        activity_domain = [
            ("date_order", ">=", start_date),
            ("date_order", "<=", end_date),
            ('state', '=', 'done'),
        ]
        activity_card_order = self.env['activity'].search(activity_domain)

        # ---------------------------

        hours = 7
        hours_add = datetime.timedelta(hours=hours)

        # loop order from pos order
        for order in model_order:
            order_date = order.date_order + hours_add

            if (order.date_order >= start_date) and (end_date >= order.date_order):
                if order.session_id.config_id.name in location:
                    number_customer += order.customer_count

                    # Morning, Afternoon, Evening order number, receipt number and total
                    # hour +7
                    # example: 03:00:00+07:00:00=10:00:00am
                    check_date = order.date_order.strftime("%H:%M:%S")
                    if check_date < '03:00:00':
                        r_morning += 1
                        n_morning += order.customer_count
                        total_morning += order.amount_paid

                    elif check_date >= '03:00:00' and check_date < '10:00:00':
                        r_afternoon += 1
                        n_afternoon += order.customer_count
                        total_afternoon += order.amount_paid

                    else:
                        r_evening += 1
                        n_evening += order.customer_count
                        total_evening += order.amount_paid

                    # payment
                    for payment in order.payment_ids:
                        payment_method = payment.payment_method_id.name

                    for payment in order.payment_ids:
                        list_name, list_value = [], []
                        list_name.append(payment.payment_method_id.name)
                        list_value.append(payment.amount)
                        lst_payment = dict(zip(list_name, list_value))
                        payments.append(lst_payment)
                    # ----------------------------------------

                    #  subtotal
                    total_tax_dis = "%.2f" % round(order.amount_paid, 2)
                    total_tax_dis_str = '$ ' + str(total_tax_dis)
                    tax = order.amount_tax
                    tax_str = '$ ' + "%.2f" % tax
                    tax_lst.append(tax)
                    sub_total = round((order.amount_paid - order.amount_tax), 2)
                    amount_total_order_lst.append(float(total_tax_dis))
                    num_order = order.name
                    lst_receipt.append(num_order)

                    if len(lst_receipt) > 1:
                        data['ref'] = ' (' + lst_receipt[-1] + ' --> ' + lst_receipt[0] + ')'
                    else:
                        data['ref'] = ' (' + lst_receipt[0] + ')'
                    order_date_list = {
                        'order_date': order_date,
                        'i': i,
                        'pos_reference': order.name,
                        'payment_method': payment_method,
                        'sub_total': '$ ' + "%.2f" % sub_total,
                        'tax_str': tax_str,
                        'total_tax_dis_str': total_tax_dis_str
                    }
                    i += 1
                    dic[order.name] = {
                        'discount_lst': [],
                        'receipt_ref': order.name,
                    }
                    sub_total_lst.append(sub_total)

                    for line in order.lines:
                        dic[order.name]['discount_lst'].append((line.qty * line.price_unit * line.discount) / 100)
                        product_qty += line.qty

                        if line.product_id:
                            if line.product_id.categ_id.display_name in product_category:
                                product_category[line.product_id.categ_id.display_name]['qty'] += line.qty
                                product_category[line.product_id.categ_id.display_name]['discount'] += round(
                                    ((line.qty * line.price_unit * line.discount) / 100), 2)
                                product_category[line.product_id.categ_id.display_name]['sub_lst'] += round(
                                    line.price_subtotal, 2)
                                product_category[line.product_id.categ_id.display_name]['tax'] += round(
                                    line.price_subtotal_incl - line.price_subtotal, 2)
                                product_category[line.product_id.categ_id.display_name]['total_price'] += round(
                                    line.price_subtotal_incl, 2)
                            else:
                                product_category.update({
                                    line.product_id.categ_id.display_name: {
                                        'name': line.product_id.categ_id.display_name,
                                        'qty': line.qty,
                                        'discount': round(((line.qty * line.price_unit * line.discount) / 100), 2),
                                        'sub_lst': round(line.price_subtotal, 2),
                                        'tax': round(line.price_subtotal_incl - line.price_subtotal, 2),
                                        'total_price': round(line.price_subtotal_incl, 2)
                                    }
                                })

                    for key in dic:
                        if dic[key]['receipt_ref'] == order_date_list['pos_reference']:
                            order_date_list['discount_lst'] = "$ " + "%.2f" % round(sum(dic[key]['discount_lst']), 2)
                            total_column_discount.append(round(sum(dic[key]['discount_lst']), 2))
                            column_lst.append(order_date_list)

        data['product_category'] = []
        for item in product_category.items():
            data['product_category'].append(item[1])

        # calculate the same payment method
        counter = collections.Counter()
        for type in payments:
            counter.update(type)
        sum_payment_method = dict(counter)
        # ---------------------------------

        # Start loop order from Hotel Restaurant: Hotel Card Print Report
        for order in hotel_card_order:

            hotel_order_date = order.o_date + hours_add

            if order.pos_ids.name in location:
                if len(order) != 0:
                    is_restaurant = True
                hotel_tax_cal = order.amount_total - order.amount_subtotal
                hotel_total_tax.append(hotel_tax_cal)
                hotel_subtotal_cal = round(order.amount_subtotal, 2)
                hotel_subtotal = '$ ' + "%.2f" % hotel_subtotal_cal
                hotel_tax = '$ ' + "%.2f" % hotel_tax_cal
                hotel_total_amount = '$' + "%.2f" % round(order.amount_total, 2)

                hotel_order_date_list = {
                    'hotel_order_date': hotel_order_date,
                    'hotel_order_number': order.order_no,
                    'hotel_sub_total': hotel_subtotal,
                    'hotel_tax': hotel_tax,
                    'hotel_total': hotel_total_amount,
                }

                hotel_dict[order.order_no] = {
                    'hotel_discount_lst': [],
                    'hotel_receipt_ref': order.order_no,
                }
                hotel_sale_total.append(hotel_subtotal_cal)

                for line in order.order_list_ids:
                    hotel_dict[order.order_no]['hotel_discount_lst'].append(
                        (line.item_qty * line.item_rate * line.discount_lst) / 100)
                    hotel_total_qty += line.item_qty

                    if line.menucard_id:
                        if line.menucard_id.categ_id.name in hotel_product_category:
                            hotel_product_category[line.menucard_id.categ_id.name]['hotel_qty'] += line.item_qty
                            hotel_product_category[line.menucard_id.categ_id.name]['hotel_discount'] += round(
                                ((line.item_qty * line.item_rate * line.discount_lst) / 100), 2)
                            hotel_product_category[line.menucard_id.categ_id.name]['hotel_sub_lst'] += round(
                                line.price_subtotal, 2)
                            hotel_product_category[line.menucard_id.categ_id.name]['hotel_tax'] += round(
                                ((line.price_subtotal * order.tax) / 100), 2)
                            hotel_product_category[line.menucard_id.categ_id.name]['hotel_total_price'] += round(
                                (line.price_subtotal + ((line.price_subtotal * order.tax) / 100)), 2)
                        else:
                            hotel_product_category.update({
                                line.menucard_id.categ_id.name: {
                                    'hotel_name': line.menucard_id.categ_id.name,
                                    'hotel_qty': line.item_qty,
                                    'hotel_discount': round(
                                        ((line.item_qty * line.item_rate * line.discount_lst) / 100), 2),
                                    'hotel_sub_lst': round(line.price_subtotal, 2),
                                    'hotel_tax': round(((line.price_subtotal * order.tax) / 100), 2),
                                    'hotel_total_price': round(
                                        (line.price_subtotal + ((line.price_subtotal * order.tax) / 100)), 2)
                                }
                            })
                for key in hotel_dict:
                    if hotel_dict[key]['hotel_receipt_ref'] == hotel_order_date_list['hotel_order_number']:
                        hotel_order_date_list['hotel_discount_lst'] = "$ " + "%.2f" % round(
                            sum(hotel_dict[key]['hotel_discount_lst']), 2)
                        hotel_total_column_discount.append(round(sum(hotel_dict[key]['hotel_discount_lst']), 2))
                        hotel_column_lst.append(hotel_order_date_list)

        data['hotel_product_category'] = []
        for item in hotel_product_category.items():
            data['hotel_product_category'].append(item[1])
        # end restaurant---------------------------------

        # Start loop order from Hotel Activity: Hotel Card Print Report
        for order in activity_card_order:

            activity_order_date = order.date_order + hours_add

            if order.pos_activity_ids.name in location:
                if len(order) != 0:
                    is_activity = True
                activity_tax_cal = order.amount_total - order.amount_subtotal
                activity_total_tax.append(activity_tax_cal)
                activity_subtotal_cal = round(order.amount_subtotal, 2)
                activity_subtotal = '$ ' + "%.2f" % activity_subtotal_cal
                activity_tax = '$ ' + "%.2f" % activity_tax_cal
                activity_total_amount = '$' + "%.2f" % round(order.amount_total, 2)

                activity_order_date_list = {
                    'activity_order_date': activity_order_date,
                    'activity_order_number': order.name,
                    'activity_sub_total': activity_subtotal,
                    'activity_tax': activity_tax,
                    'activity_total': activity_total_amount,
                }

                activity_dict[order.name] = {
                    'activity_discount_lst': [],
                    'activity_receipt_ref': order.name,
                }
                activity_sale_total.append(activity_subtotal_cal)

                for line in order.booking_items:
                    activity_dict[order.name]['activity_discount_lst'].append(
                        (line.qty * line.unit_price * line.discount) / 100)
                    activity_total_qty += line.qty

                    if line.destination:
                        if line.destination.service_categ_id.display_name in activity_product_category:
                            activity_product_category[line.destination.service_categ_id.display_name][
                                'activity_qty'] += line.qty
                            activity_product_category[line.destination.service_categ_id.display_name][
                                'activity_discount'] += round(((line.qty * line.unit_price * line.discount) / 100), 2)
                            activity_product_category[line.destination.service_categ_id.display_name][
                                'activity_sub_lst'] += round(line.price_subtotal, 2)
                            activity_product_category[line.destination.service_categ_id.display_name][
                                'activity_tax'] += round(((line.price_subtotal * order.vat_value) / 100), 2)
                            activity_product_category[line.destination.service_categ_id.display_name][
                                'activity_total_price'] += round(
                                (line.price_subtotal + ((line.price_subtotal * order.vat_value) / 100)), 2)
                        else:
                            activity_product_category.update({
                                line.destination.service_categ_id.display_name: {
                                    'activity_name': line.destination.service_categ_id.display_name,
                                    'activity_qty': line.qty,
                                    'activity_discount': round(((line.qty * line.unit_price * line.discount) / 100), 2),
                                    'activity_sub_lst': round(line.price_subtotal, 2),
                                    'activity_tax': round(((line.price_subtotal * order.vat_value) / 100), 2),
                                    'activity_total_price': round(
                                        (line.price_subtotal + ((line.price_subtotal * order.vat_value) / 100)), 2)
                                }
                            })

                for key in activity_dict:
                    if activity_dict[key]['activity_receipt_ref'] == activity_order_date_list['activity_order_number']:
                        activity_order_date_list['activity_discount_lst'] = "$ " + "%.2f" % round(
                            sum(activity_dict[key]['activity_discount_lst']), 2)
                        activity_total_column_discount.append(
                            round(sum(activity_dict[key]['activity_discount_lst']), 2))
                        activity_column_lst.append(activity_order_date_list)

        data['activity_product_category'] = []
        for item in activity_product_category.items():
            data['activity_product_category'].append(item[1])
        # end activity ----------------------------------

        # sort column list array by pos_reference
        column_lst = sorted(column_lst, key=lambda k: k['pos_reference'])

        # Calculate Total Summary
        total_sum_subtotal = sum(sub_total_lst + hotel_sale_total + activity_sale_total)
        total_sum_tax = sum(tax_lst + hotel_total_tax + activity_total_tax)
        total_sum_qty = product_qty + hotel_total_qty + activity_total_qty
        total_sum_discount = sum(total_column_discount + hotel_total_column_discount + activity_total_column_discount)
        amount_total_order = sum(
            amount_total_order_lst + hotel_sale_total + hotel_total_tax + activity_sale_total + activity_total_tax) + total_sum_discount

        location_name = (', '.join(location))
        data['No_customer'] = number_customer
        data['location'] = location_name
        data['print_date'] = print_date
        data['count'] = len(lst_receipt)
        data['product_total_quantity'] = "%.1f" % round(product_qty, 1)
        data['column_lst'] = column_lst
        data['payment_summary'] = sum_payment_method
        data['sum_tax'] = "$ " + "%.2f" % round(sum(tax_lst), 2)
        data['sum_discount'] = '$ ' + "%.2f" % round(sum(total_column_discount), 2)
        data['sum_subtotal'] = '$ ' + "%.2f" % round(sum(sub_total_lst), 2)
        data['amount_total_order'] = "$ " + "%.2f" % round(sum(amount_total_order_lst), 2)

        # Morning, Afternoon, Evening
        data['total_morning'] = '$ ' + "%.2f" % round(total_morning, 2)
        data['receipt_morning'] = r_morning
        data['no_customer_morning'] = n_morning
        data['total_afternoon'] = '$ ' + "%.2f" % round(total_afternoon, 2)
        data['receipt_afternoon'] = r_afternoon
        data['no_customer_afternoon'] = n_afternoon
        data['total_evening'] = '$ ' + "%.2f" % round(total_evening, 2)
        data['receipt_evening'] = r_evening
        data['no_customer_evening'] = n_evening

        # Hotel Card Restaurant
        data['is_restaurant'] = is_restaurant
        data['hotel_card_order'] = hotel_column_lst
        data['hotel_vat'] = '$ ' + "%.2f" % round(sum(hotel_total_tax), 2)
        data['hotel_subtotal'] = '$ ' + "%.2f" % round(sum(hotel_sale_total), 2)
        data['hotel_total_discount'] = '$ ' + "%.2f" % sum(hotel_total_column_discount)
        data['hotel_total_quantity'] = "%.1f" % round(hotel_total_qty, 1)

        # Hotel Card Activity
        data['is_activity'] = is_activity
        data['activity_card_order'] = activity_column_lst
        data['activity_vat'] = '$ ' + "%.2f" % round(sum(activity_total_tax), 2)
        data['activity_subtotal'] = '$ ' + "%.2f" % round(sum(activity_sale_total), 2)
        data['activity_total_discount'] = '$ ' + "%.2f" % sum(activity_total_column_discount)
        data['activity_total_quantity'] = "%.1f" % round(activity_total_qty, 1)

        # Total Summary
        data['total_sum_subtotal'] = '$ ' + "%.2f" % round(total_sum_subtotal, 2)
        data['total_sum_tax'] = '$' + "%.2f" % round(total_sum_tax, 2)
        data['total_sum_discount'] = '$ ' + "%.2f" % total_sum_discount
        data['total_sum_qty'] = total_sum_qty
        data['total_amount_tax_total_order'] = "$ " + "%.2f" % round(amount_total_order, 2)

        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids))
        return data
