from odoo import models, fields


class SupplierPaymentReport(models.TransientModel):
    _name = 'supplier.payment.report.wizard'

    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    supplier_id = fields.Many2one('kirirom.supplier', 'Supplier')
    type = fields.Selection(string="Type", default="A2A & vKirirom",
                            selection=[("A2A & vKirirom", "A2A & vKirirom"), ("A2A", "A2A"), ("vKirirom", "Vkirirom")],
                            help="The type of the Department")
    exchange_rate = fields.Float('Exchange Rate', default=4000, help="Exchange Rare for Khmer Riel to US Dollar")

    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'kr.purchase.order.line',
            'form': self.read(['date_start', 'date_end', 'supplier_id', 'exchange_rate', 'type'])[0]
        }

        return self.env.ref('market_list_odoo13.supplier_payment_voucher_report_form').report_action(self, data=data)
