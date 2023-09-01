from odoo import fields, api, models
import datetime
import time
from collections import defaultdict


class FolioReportWizardCustomize(models.TransientModel):
    _inherit = "folio.report.wizard"
    _rec_name = 'report_date'

    report_date = fields.Datetime('Report Date')

    def _defaults_checkin_date(self):
        checkin = datetime.datetime.now().strftime("%Y-%m-%d 07:00:00")
        return checkin

    _defaults = {
        'report_date': _defaults_checkin_date
    }

    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.folio',
            'form': self.read(['report_date'])[0]
        }
        return self.env.ref("hotel_report_customize.report_hotel_management_customize").with_context(
            landscape=True).report_action(
            self, data=data
        )


class FODailyReportData(models.AbstractModel):
    _name = 'report.hotel_report_customize.report_hotel_folio_customize'
    _description = "Hotel Folio Report"

    def _get_folio_data(self, report_date):
        total_amount = 0.0
        data_folio = []
        folio_obj = self.env["hotel.folio"]
        act_domain = [
            ("checkin_date", "<=", report_date),
            ("checkout_date", ">", report_date),
            ('state', '!=', 'cancel'),
        ]
        tids = folio_obj.search(act_domain)
        for data in tids:
            name, invoice_no = [], []
            checkin_lst, checkout_lst = [], []
            room_price_lst, discount_lst = [], []
            if data.state == "draft":
                states = "OnCheckin"
            else:
                states = "Checkout"
            for room_line in data.room_line_ids:
                name.append(room_line.product_id.name)
                checkin_lst.append(room_line.checkin_date)
                checkout_lst.append(room_line.checkout_date)
                room_price_lst.append(room_line.price_subtotal)
                discount_lst.append(room_line.product_uom_qty * room_line.price_unit * (room_line.discount / 100))

            for inv_id in data.hotel_invoice_id:
                invoice_no.append(inv_id.name)

            service_lines = []
            for service_line in data.service_line_ids:
                prod = dict()
                prod['categ'] = service_line.service_line_id.product_id.categ_id.name
                prod['qty'] = service_line.product_uom_qty
                prod['price'] = service_line.service_line_id.price_unit
                prod['discount'] = service_line.discount * service_line.price_unit / 100
                service_lines.append(prod)

            new_folio = {}
            payment_amount = defaultdict(float)
            payment_ids = data.hotel_invoice_id.payment_ids
            for payment in payment_ids:
                journal_name = payment.journal_id.name
                payment_amount[journal_name] += payment.credit

            new_folio.update({'payment_amount': dict(payment_amount)})

            data_folio.append(
                {
                    "name": data.name,
                    "partner": data.partner_id.name,
                    "checkin_lst": checkin_lst,
                    "checkout_lst": checkout_lst,
                    "amount": data.amount_total,
                    "room_lines": name,
                    "invoice_no": invoice_no,
                    "room_price_lst": room_price_lst,
                    "discount_lst": discount_lst,
                    "receipt_no": data.receipt_no,
                    "service_lines": service_lines,
                    "ref_booking": data.ref_booking,
                    "new_folio": new_folio,
                    "state": states
                }
            )
            total_amount += data.amount_total
        data_folio.append({"total_amount": total_amount})
        # print(data_folio, "--------------------")
        return data_folio

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.folio"].browse(docids)
        report_date = data["form"].get("report_date", fields.Date.today())
        act_domain = [
            ("checkin_date", "<=", report_date),
            ("checkout_date", ">", report_date),
            ('state', '!=', 'cancel'),
        ]
        folio_obj = self.env["hotel.folio"].search(act_domain)
        total_foreign = 0
        total_cambodian = 0
        total_camping = 0
        room, subtotal_lst = [], []

        for item in folio_obj:
            total_foreign += item.x_foreigner
            total_cambodian += item.x_cambodian
            for room_line in item.room_line_ids:
                subtotal_lst.append(room_line.price_subtotal)
                room.append(room_line.product_id.name)
                if "Camping" in room_line.product_id.name:
                    total_camping += 1
            total_room = len(room) - total_camping
            total_customer = total_foreign + total_cambodian
            data['total_customer'] = total_customer
            data['total_camping'] = total_camping
            data['total_room'] = total_room
            data['total_foreigner'] = total_foreign
            data['total_cambodian'] = total_cambodian
        data['subtotal'] = sum(subtotal_lst)
        # print(data)
        return {
            "doc_ids": docids,
            "doc_model": self.model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "folio_data": self._get_folio_data(report_date),
        }