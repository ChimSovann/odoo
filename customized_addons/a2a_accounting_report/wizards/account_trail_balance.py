from odoo import models, fields
from odoo.tools import get_lang, translate


class TrailBalanceExcelWizard(models.TransientModel):
  _inherit = "account.balance.report"

  def _print_report_xlsx(self, data):
    data = self.pre_print_report(data)
    records = self.env[data['model']].browse(data.get('ids', []))
    return self.env.ref('a2a_accounting_report.action_report_trial_balance_xlsx').report_action(records, data=data)
