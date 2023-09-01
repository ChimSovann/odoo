from odoo import models


class TrailBalanceExcelWizard(models.TransientModel):
  _inherit = "account.tax.report"

  def _print_report_xlsx(self, data):
    return self.env.ref('a2a_accounting_report.action_report_tax_report_xlsx').report_action(self, data=data)
