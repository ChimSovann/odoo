# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountPrintJournal(models.TransientModel):
    _inherit = "account.print.journal"
    _description = "Account Print Journal In Excel(XLSX)"

    def _print_report_xlsx(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'sort_selection': self.sort_selection})
        return self.env.ref('a2a_accounting_report.action_report_journal_audit_xlsx').with_context(landscape=True).report_action(self, data=data)
