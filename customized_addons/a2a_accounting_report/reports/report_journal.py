from odoo import models


class ReportGeneralLedgerXLSX(models.AbstractModel):
    _name = "report.a2a_accounting_report.generate_journal_audit_xlsx"
    _inherit = ['report.odoo_report_xlsx.abstract', 'report.accounting_pdf_reports.report_journal']

    def generate_xlsx_report(self, workbook, data, partners):
        workbook.default_format_properties = {'font_name': 'Arial', 'font_size': 10}
        report = self._get_report_values('', data=data)
        data = report['data']
        docs = report['docs']
        lines = report['lines']
        sum_debit = report['sum_debit']
        sum_credit = report['sum_credit']
        get_taxes = report['get_taxes']
        # Style
        bold = workbook.add_format({'bold': True, 'valign': 'vcenter'})
        table_header = workbook.add_format({'bold': True, 'valign': 'vcenter', 'align': 'center', 'border': True, 'text_wrap': True})
        table_data =  workbook.add_format({'valign': 'vcenter', 'align': 'left', 'border': True})
        currency_format = workbook.add_format({'align': 'right', 'border': True, 'text_wrap': True, 'valign': 'vcenter',
                                               'num_format': '[' + self.env.company.currency_id.symbol + '$ -409]#,##0.00'})
        for o in docs:
            # Header Information
            sheet = workbook.add_worksheet(o.name)
            row = 0
            sheet.merge_range(row, 0, row, 7, o.name+" Journal",
                              workbook.add_format({'align': 'left', 'valign': 'vcenter', 'font_size': 24, 'bold': True}))
            sheet.set_row(row, 30)
            row += 2
            sheet.merge_range(row, 0, row, 1, 'Company:', bold)
            sheet.merge_range(row, 2, row, 3, 'Journal:', bold)
            sheet.merge_range(row, 4, row, 5, 'Entries Sorted By:', bold)
            sheet.merge_range(row, 6, row, 7, 'Target Moves:', bold)
            row += 1
            sheet.merge_range(row, 0, row, 1, self.env.company.name, workbook.add_format())
            sheet.merge_range(row, 2, row, 3, o.name, workbook.add_format())
            if data['form'].get('sort_selection') != 'l.date':
                sheet.merge_range(row, 4, row, 5, 'Journal Entry Number', workbook.add_format())
            else:
                sheet.merge_range(row, 4, row, 5, 'Date', workbook.add_format())
            if data['form']['target_move'] == 'all':
                sheet.merge_range(row, 6, row, 7, 'All Entries', workbook.add_format())
            elif data['form']['target_move'] == 'posted':
                sheet.merge_range(row, 6, row, 7, 'All Posted Entries', workbook.add_format())

            # Table of content
            row += 1
            sheet.set_column("A:E", 20)
            sheet.set_column("F:F", 50)
            sheet.set_column("G:H", 20)
            sheet.write(row, 0, "Move", table_header)
            sheet.write(row, 1, "Date", table_header)
            sheet.write(row, 2, "Account", table_header)
            sheet.write(row, 3, "Account Name", table_header)
            sheet.write(row, 4, "Partner", table_header)
            sheet.write(row, 5, "Label", table_header)
            sheet.write(row, 6, "Debit", table_header)
            sheet.write(row, 7, "Credit", table_header)
            if data['form']['amount_currency']:
                sheet.write(row, 8, "Currency", table_header)
            sheet.set_row(row, 25)

            for aml in lines[o.id]:
                row += 1
                sheet.set_row(row, 20)
                sheet.write(row, 0, aml.move_id.name != '/' and aml.move_id.name or ('*'+str(aml.move_id.id)), table_data)
                sheet.write(row, 1, str(aml.date), table_data)
                sheet.write(row, 2, aml.account_id.code, table_data)
                sheet.write(row, 3, aml.account_id.name, table_data)
                sheet.write(row, 4, aml.sudo().partner_id and aml.sudo().partner_id.name and aml.sudo().partner_id.name or '', table_data)
                sheet.write(row, 5, aml.name and aml.name, table_data)
                sheet.write(row, 6, aml.debit, currency_format)
                sheet.write(row, 7, aml.credit, currency_format)
                if data['form']['amount_currency'] and aml.amount_currency:
                    sheet.write(row, 8, aml.amount_currency, currency_format)
            # Total Calculation
            row += 2
            sheet.write(row, 0, "Total", table_header)
            sheet.write(row, 1, sum_debit(data, o), currency_format)
            sheet.write(row, 2, sum_credit(data, o), currency_format)
            row += 1
            sheet.merge_range(row, 0, row, 2, "Tax Declaration", table_header)
            row += 1
            sheet.write(row, 0, "Name", table_header)
            sheet.write(row, 1, "Base Amount", table_header)
            sheet.write(row, 2, "Tax Amount", table_header)
            taxes = get_taxes(data, o)
            for tax in taxes:
                row += 1
                sheet.write(row, 0, tax.name, table_data)
                sheet.write(row, 1, taxes[tax]['base_amount'], currency_format)
                sheet.write(row, 2, taxes[tax]['tax_amount'], currency_format)

