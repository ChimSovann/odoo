import json

from odoo import api, models
from collections import OrderedDict, defaultdict
from datetime import date


class PurchasePaymentReport(models.AbstractModel):
    _name = 'report.market_list_odoo13.supplier_payment_voucher_form'
    _description = 'Custom functions for payment voucher in market list'

    def _get_supplier_payment_details(self, form):
        order_line_obj = self.env['kr.purchase.order.line']
        rate = form.get('exchange_rate')
        supplier_id = form.get('supplier_id')[0]
        supplier_tel = self.env['kirirom.supplier'].search([('id', '=', supplier_id)]).tel

        filtered_date_obj_supplier = order_line_obj.search(['&', ('date_order', '>=', form['date_start'] + \
                                                                  ' 00:00:00'), ('date_order', '<=', form['date_end'] + \
                                                                                 ' 23:59:59'), ('state', '=', 'done'),
                                                            ('supplier_id.name', '=', form.get('supplier_id'))])

        vkr_records = []
        a2a_records = []

        for rec in filtered_date_obj_supplier:
            if rec.order_id.is_a2a:
                a2a_records.append(rec)
            else:
                vkr_records.append(rec)

        def khr_to_usd(current_price, currency_name):
            return round(current_price / rate, 2) if currency_name == 'KHR' else current_price

        data = defaultdict(list)
        if form['type'] == 'A2A':
            for record in a2a_records:
                key = record.order_id.date_order.strftime("%Y-%m-%d")

                order_line = {
                    'invoice_no': record.invoice_number,
                    'inv_line': [record.currency_id.name, record.sub_total, record.order_id.name]
                }
                data[key].append(order_line)
            format_data = {}
            total_amount_khr = 0
            total_amount_usd = 0
            total_amount = 0
            for key, value in data.items():
                invoice_dict = defaultdict(list)
                for order_line in value:
                    invoice_dict[order_line['invoice_no']].append(order_line['inv_line'])
                invoice_data = {}
                for inv_key, inv_val in invoice_dict.items():
                    po_num = inv_val[0][2]
                    amount_khr = sum([inv_line[1] for inv_line in inv_val if inv_line[0] == 'KHR'])
                    amount_usd = sum([inv_line[1] for inv_line in inv_val if inv_line[0] == 'USD'])
                    total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                    invoice_data[inv_key] = [po_num, amount_khr, amount_usd, total]
                    total_amount_khr += amount_khr
                    total_amount_usd += amount_usd
                    total_amount += total
                format_data[key] = invoice_data
        elif form['type'] == 'vKirirom':
            for record in vkr_records:
                key = record.order_id.date_order.strftime("%Y-%m-%d")

                order_line = {
                    'invoice_no': record.invoice_number,
                    'inv_line': [record.currency_id.name, record.sub_total, record.order_id.name]
                }
                data[key].append(order_line)
            format_data = {}
            total_amount_khr = 0
            total_amount_usd = 0
            total_amount = 0
            for key, value in data.items():
                invoice_dict = defaultdict(list)
                for order_line in value:
                    invoice_dict[order_line['invoice_no']].append(order_line['inv_line'])
                invoice_data = {}
                for inv_key, inv_val in invoice_dict.items():
                    po_num = inv_val[0][2]
                    amount_khr = sum([inv_line[1] for inv_line in inv_val if inv_line[0] == 'KHR'])
                    amount_usd = sum([inv_line[1] for inv_line in inv_val if inv_line[0] == 'USD'])
                    total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                    invoice_data[inv_key] = [po_num, amount_khr, amount_usd, total]
                    total_amount_khr += amount_khr
                    total_amount_usd += amount_usd
                    total_amount += total
                format_data[key] = invoice_data
        else:
            for record in filtered_date_obj_supplier:
                key = record.order_id.date_order.strftime("%Y-%m-%d")

                order_line = {
                    'invoice_no': record.invoice_number,
                    'inv_line': [record.currency_id.name, record.sub_total, record.order_id.name]
                }
                data[key].append(order_line)
            format_data = {}
            total_amount_khr = 0
            total_amount_usd = 0
            total_amount = 0
            for key, value in data.items():
                invoice_dict = defaultdict(list)
                for order_line in value:
                    invoice_dict[order_line['invoice_no']].append(order_line['inv_line'])
                invoice_data = {}
                for inv_key, inv_val in invoice_dict.items():
                    po_num = inv_val[0][2]
                    amount_khr = sum([inv_line[1] for inv_line in inv_val if inv_line[0] == 'KHR'])
                    amount_usd = sum([inv_line[1] for inv_line in inv_val if inv_line[0] == 'USD'])
                    total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                    invoice_data[inv_key] = [po_num, amount_khr, amount_usd, total]
                    total_amount_khr += amount_khr
                    total_amount_usd += amount_usd
                    total_amount += total
                format_data[key] = invoice_data
        return [format_data, total_amount_khr, total_amount_usd, total_amount, supplier_tel]

    @api.model
    def _get_report_values(self, docids, data):
        if data is None:
            data = {}
        if not docids:
            docids = data["context"].get("active_ids")
        docs = self.env['kr.purchase.order.line'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'docs': docs,
            'data': data,
            'get_supplier_payment_details': self._get_supplier_payment_details
        }
        return docargs


class ReportPurchasePayment(models.AbstractModel):
    _name = 'report.market_list_odoo13.report_purchase_payment'
    _description = "Custom function for Detail Payment Report"

    def _get_details(self, form):

        order_line_obj = self.env['kr.purchase.order.line']
        purchase_order_obj = self.env['kr.purchase.order']
        analytic_acc_config_obj = self.env['analytic.account.for.report']

        rate = form.get('exchange_rate')
        location_ids = form['location'][0] if form['location'] else []

        analytic_acc_config_ids = analytic_acc_config_obj.browse(location_ids).analytic_account_ids

        # Get all lines of the records from purchase order line based on the input date in wizard form

        filtered_date_obj = order_line_obj.search(['&', ('date_order', '>=', form['date_start'] + \
                                                         ' 00:00:00'), ('date_order', '<=', form['date_end'] + \
                                                                        ' 23:59:59'), ('state', '=', 'done')])

        # Get all records from purchase order based on the input date in wizard form

        filtered_date_purchase_order_obj = purchase_order_obj.search(['&', ('date_order', '>=', form['date_start'] + \
                                                                            ' 00:00:00'),
                                                                      ('date_order', '<=', form['date_end'] + \
                                                                       ' 23:59:59'), ('state', '=', 'done')])
        vkr_records = []
        a2a_records = []
        custom_location_records = []

        # Separate records based on type

        for rec in filtered_date_obj:
            if rec.order_id.is_a2a:
                a2a_records.append(rec)
            else:
                vkr_records.append(rec)

        # Separate records based selected location

        for rec_po in filtered_date_purchase_order_obj:
            if rec_po.analytic_account_id in analytic_acc_config_ids:
                for rec in rec_po.order_line:
                    custom_location_records.append(rec)

        # Method to convert currency from KHR to USD if it is KHR else return
        def khr_to_usd(current_price, currency_id):
            return round(current_price / rate, 2) if currency_id == 66 else current_price

        data = defaultdict(list)

        if form['location']:
            for record in custom_location_records:
                key = record.order_id.date_order.strftime("%Y-%m-%d")

                order_line = {
                    'amount': [record.supplier_id.name,
                               khr_to_usd(record.sub_total, record.currency_id.id)],
                    'journal_id': [record.order_id.journal_id.name,
                                   khr_to_usd(record.sub_total, record.currency_id.id)],
                }

                data[key].append(order_line)
            format_data = {}
            for key, value in data.items():
                amounts = defaultdict(float)
                journal_ids = defaultdict(float)
                total_amount = 0
                for order_line in value:
                    amounts[order_line['amount'][0]] += order_line['amount'][1]
                    journal_ids[order_line['journal_id'][0]] += order_line['journal_id'][1]
                    total_amount += order_line['amount'][1]
                format_data[key] = [amounts, journal_ids, total_amount]

            return format_data
        else:
            if form['type'] == 'A2A':
                for record in a2a_records:
                    # Formatting the date_order to "YYYY-MM-DD"
                    key = record.order_id.date_order.strftime("%Y-%m-%d")

                    order_line = {
                        'amount': [record.supplier_id.name,
                                   khr_to_usd(record.sub_total, record.currency_id.id)],
                        'journal_id': [record.order_id.journal_id.name,
                                       khr_to_usd(record.sub_total, record.currency_id.id)],
                    }

                    data[key].append(order_line)
                format_data = {}
                for key, value in data.items():
                    amounts = defaultdict(float)
                    journal_ids = defaultdict(float)
                    total_amount = 0
                    for order_line in value:
                        amounts[order_line['amount'][0]] += order_line['amount'][1]
                        journal_ids[order_line['journal_id'][0]] += order_line['journal_id'][1]
                        total_amount += order_line['amount'][1]
                    format_data[key] = [amounts, journal_ids, total_amount]
            elif form['type'] == 'vKirirom':
                for record in vkr_records:
                    key = record.order_id.date_order.strftime("%Y-%m-%d")

                    order_line = {
                        'amount': [record.supplier_id.name,
                                   khr_to_usd(record.sub_total, record.currency_id.id)],
                        'journal_id': [record.order_id.journal_id.name,
                                       khr_to_usd(record.sub_total, record.currency_id.id)],
                    }

                    data[key].append(order_line)
                format_data = {}
                for key, value in data.items():
                    amounts = defaultdict(float)
                    journal_ids = defaultdict(float)
                    total_amount = 0
                    for order_line in value:
                        amounts[order_line['amount'][0]] += order_line['amount'][1]
                        journal_ids[order_line['journal_id'][0]] += order_line['journal_id'][1]
                        total_amount += order_line['amount'][1]
                    format_data[key] = [amounts, journal_ids, total_amount]
            else:
                for record in filtered_date_obj:
                    key = record.order_id.date_order.strftime("%Y-%m-%d")

                    order_line = {
                        'amount': [record.supplier_id.name,
                                   khr_to_usd(record.sub_total, record.currency_id.id)],
                        'journal_id': [record.order_id.journal_id.name,
                                       khr_to_usd(record.sub_total, record.currency_id.id)],
                    }

                    data[key].append(order_line)
                format_data = {}
                for key, value in data.items():
                    amounts = defaultdict(float)
                    journal_ids = defaultdict(float)
                    total_amount = 0
                    for order_line in value:
                        amounts[order_line['amount'][0]] += order_line['amount'][1]
                        journal_ids[order_line['journal_id'][0]] += order_line['journal_id'][1]
                        total_amount += order_line['amount'][1]
                    format_data[key] = [amounts, journal_ids, total_amount]

            return format_data

    @api.model
    def _get_report_values(self, docids, data):
        if data is None:
            data = {}
        if not docids:
            docids = data["context"].get("active_ids")
        docs = self.env['kr.purchase.order.line'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'docs': docs,
            'data': data,
            'get_details': self._get_details
        }

        return docargs


class ReportPurchasePaymentAccount(models.AbstractModel):
    _name = 'report.market_list_odoo13.report_payment_for_account'
    _description = "Custom function for Accounting in Detail Payment Report"

    def _get_accounting_details(self, form):

        order_line_obj = self.env['kr.purchase.order.line']
        purchase_order_obj = self.env['kr.purchase.order']
        analytic_acc_config_obj = self.env['analytic.account.for.report']

        rate = form.get('exchange_rate')
        location_ids = form['location'][0] if form['location'] else []

        analytic_acc_config_ids = analytic_acc_config_obj.browse(location_ids).analytic_account_ids

        filtered_date_obj = order_line_obj.search(['&', ('date_order', '>=', form['date_start'] + \
                                                         ' 00:00:00'), ('date_order', '<=', form['date_end'] + \
                                                                        ' 23:59:59'), ('state', '=', 'done')])

        # Get all records from purchase order based on the input date in wizard form

        filtered_date_purchase_order_obj = purchase_order_obj.search(['&', ('date_order', '>=', form['date_start'] + \
                                                                            ' 00:00:00'),
                                                                      ('date_order', '<=', form['date_end'] + \
                                                                       ' 23:59:59'), ('state', '=', 'done')])

        vkr_records = []
        a2a_records = []
        custom_location_records = []

        for rec in filtered_date_obj:
            if rec.order_id.is_a2a:
                a2a_records.append(rec)
            else:
                vkr_records.append(rec)

        # Separate records based selected location

        for rec_po in filtered_date_purchase_order_obj:
            if rec_po.analytic_account_id in analytic_acc_config_ids:
                for rec in rec_po.order_line:
                    custom_location_records.append(rec)

        def khr_to_usd(current_price, currency_name):
            return round(current_price / rate, 2) if currency_name == 'KHR' else current_price

        data = defaultdict(list)
        if form['location']:
            for record in custom_location_records:
                key = record.order_id.date_order.strftime("%Y-%m-%d")

                order_line = {
                    'journal_acc': record.order_id.journal_id.name,
                    'amount': [record.currency_id.name, record.sub_total]
                }

                data[key].append(order_line)
            format_data = {}
            total_amount_khr = 0
            total_amount_usd = 0
            total_amount = 0
            for key, value in data.items():
                journals = defaultdict(list)
                for order_line in value:
                    journals[order_line['journal_acc']].append(order_line['amount'])

                journal_data = {}
                for journal_key, journal_val in journals.items():
                    amount_khr = sum([amount[1] for amount in journal_val if amount[0] == 'KHR'])
                    amount_usd = sum([amount[1] for amount in journal_val if amount[0] == 'USD'])
                    total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                    journal_data[journal_key] = [amount_khr, amount_usd, total]
                    total_amount_khr += amount_khr
                    total_amount_usd += amount_usd
                    total_amount += total

                format_data[key] = journal_data

            for key, val in format_data.items():
                today_amount_list = list(format_data[key].values())
                total_per_day = [sum(i) for i in zip(*today_amount_list)]
                format_data[key] = [val, total_per_day]
        else:
            if form['type'] == 'A2A':
                for record in a2a_records:
                    key = record.order_id.date_order.strftime("%Y-%m-%d")

                    order_line = {
                        'journal_acc': record.order_id.journal_id.name,
                        'amount': [record.currency_id.name, record.sub_total]
                    }

                    data[key].append(order_line)
                format_data = {}
                total_amount_khr = 0
                total_amount_usd = 0
                total_amount = 0
                for key, value in data.items():
                    journals = defaultdict(list)
                    for order_line in value:
                        journals[order_line['journal_acc']].append(order_line['amount'])

                    journal_data = {}
                    for journal_key, journal_val in journals.items():
                        amount_khr = sum([amount[1] for amount in journal_val if amount[0] == 'KHR'])
                        amount_usd = sum([amount[1] for amount in journal_val if amount[0] == 'USD'])
                        total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                        journal_data[journal_key] = [amount_khr, amount_usd, total]
                        total_amount_khr += amount_khr
                        total_amount_usd += amount_usd
                        total_amount += total

                    format_data[key] = journal_data

                for key, val in format_data.items():
                    today_amount_list = list(format_data[key].values())
                    total_per_day = [sum(i) for i in zip(*today_amount_list)]
                    format_data[key] = [val, total_per_day]

            elif form['type'] == 'vKirirom':
                for record in vkr_records:
                    key = record.order_id.date_order.strftime("%Y-%m-%d")

                    order_line = {
                        'journal_acc': record.order_id.journal_id.name,
                        'amount': [record.currency_id.name, record.sub_total]
                    }

                    data[key].append(order_line)
                format_data = {}
                total_amount_khr = 0
                total_amount_usd = 0
                total_amount = 0
                for key, value in data.items():
                    journals = defaultdict(list)
                    for order_line in value:
                        journals[order_line['journal_acc']].append(order_line['amount'])

                    journal_data = {}
                    for journal_key, journal_val in journals.items():
                        amount_khr = sum([amount[1] for amount in journal_val if amount[0] == 'KHR'])
                        amount_usd = sum([amount[1] for amount in journal_val if amount[0] == 'USD'])
                        total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                        journal_data[journal_key] = [amount_khr, amount_usd, total]
                        total_amount_khr += amount_khr
                        total_amount_usd += amount_usd
                        total_amount += total

                    format_data[key] = journal_data

                for key, val in format_data.items():
                    today_amount_list = list(format_data[key].values())
                    total_per_day = [sum(i) for i in zip(*today_amount_list)]
                    format_data[key] = [val, total_per_day]
            else:
                for record in filtered_date_obj:
                    key = record.order_id.date_order.strftime("%Y-%m-%d")

                    order_line = {
                        'journal_acc': record.order_id.journal_id.name,
                        'amount': [record.currency_id.name, record.sub_total]
                    }

                    data[key].append(order_line)
                format_data = {}
                total_amount_khr = 0
                total_amount_usd = 0
                total_amount = 0
                for key, value in data.items():
                    journals = defaultdict(list)
                    for order_line in value:
                        journals[order_line['journal_acc']].append(order_line['amount'])

                    journal_data = {}
                    for journal_key, journal_val in journals.items():
                        amount_khr = sum([amount[1] for amount in journal_val if amount[0] == 'KHR'])
                        amount_usd = sum([amount[1] for amount in journal_val if amount[0] == 'USD'])
                        total = khr_to_usd(amount_khr, 'KHR') + amount_usd
                        journal_data[journal_key] = [amount_khr, amount_usd, total]
                        total_amount_khr += amount_khr
                        total_amount_usd += amount_usd
                        total_amount += total

                    format_data[key] = journal_data

                for key, val in format_data.items():
                    today_amount_list = list(format_data[key].values())
                    total_per_day = [sum(i) for i in zip(*today_amount_list)]

                    format_data[key] = [val, total_per_day]

        return [format_data, total_amount_khr, total_amount_usd, total_amount]

    @api.model
    def _get_report_values(self, docids, data):
        if data is None:
            data = {}
        if not docids:
            docids = data["context"].get("active_ids")
        docs = self.env['kr.purchase.order.line'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'docs': docs,
            'data': data,
            'get_accounting_details': self._get_accounting_details
        }

        return docargs
