from odoo import models, _
from odoo.exceptions import UserError


class AccountGeneralLedgerXLSX(models.TransientModel):
  _inherit = "account.report.general.ledger"

  def _print_report_xlsx(self, data):
    data = self.pre_print_report(data)
    data['form'].update(self.read(['initial_balance', 'sortby'])[0])
    if data['form'].get('initial_balance') and not data['form'].get('date_from'):
      raise UserError(_("You must define a Start Date"))
    records = self.env[data['model']].browse(data.get('ids', []))

    report_action = self.env.ref('a2a_accounting_report.report_general_ledger_xlsx') \
      .report_action(records, data=data)
    report_action['close_on_report_download'] = True
    return report_action
