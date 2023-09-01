from odoo import models, fields, api
from datetime import date


class PaymentReport(models.TransientModel):
    _name = 'mk.payment.report.wizard'

    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    type = fields.Selection(string="Type", default="A2A & vKirirom",
                            selection=[("A2A & vKirirom", "A2A & vKirirom"), ("A2A", "A2A"), ("vKirirom", "vKirirom")],
                            help="The type of the Department")
    exchange_rate = fields.Float('Exchange Rate', default=4000, help="Exchange Rare for Khmer Riel to US Dollar")
    location = fields.Many2one('analytic.account.for.report', 'Location', tracking=True)
    accounting = fields.Boolean(string="For Account? ")

    def print_report(self):
        report_date = date.today().strftime("%d/%m/%y")
        data = {
            'ids': self.ids,
            'model': 'kr.purchase.order.line',
            'form': self.read(['date_start', 'date_end', 'exchange_rate', 'type', 'location'])[0],
            'report_date': report_date
        }
        if self.accounting:
            return self.env.ref('market_list_odoo13.report_kr_payment_for_account').report_action(self, data=data)

        else:
            return self.env.ref('market_list_odoo13.report_kr_purchase_payment').report_action(self, data=data)
