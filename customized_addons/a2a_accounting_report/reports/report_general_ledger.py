from odoo import models


class ReportGeneralLedgerXLSX(models.AbstractModel):
  _name = "report.a2a_accounting_report.generate_general_ledger_xlsx"
  _inherit = ['report.odoo_report_xlsx.abstract', 'report.accounting_pdf_reports.report_general_ledger']

  def generate_xlsx_report(self, workbook, data, partners):
    display_account = ''
    target_move = ''
    sortby = ''
    data = self._get_report_values('', data=data)

    # Rename the filtering string
    if data['data']['display_account'] == 'all':
      display_account = 'All accounts'
    elif data['data']['display_account'] == 'movement':
      display_account = 'With movements'
    elif data['data']['display_account'] == 'not_zero':
      display_account = 'With balance not equal zero'

    if data['data']['target_move'] == 'all':
      target_move = 'All Entries'
    elif data['data']['target_move'] == 'posted':
      target_move = 'All Posted Entries'

    if data['data']['sortby'] == 'sort_date':
      sortby = 'Date'
    elif data['data']['sortby'] == 'sort_journal_partner':
      sortby = 'Journal and Partner'

    # Style
    bold = workbook.add_format({'bold': True, 'border': True, 'align': 'center', 'text_wrap': True,
                                'valign': 'vcenter'})
    border = workbook.add_format({'align': 'center', 'border': True, 'text_wrap': True, 'valign': 'vcenter'})
    currency_format = workbook.add_format({'align': 'right', 'border': True, 'text_wrap': True, 'valign': 'vcenter',
                                           'num_format': '[' + self.env.company.currency_id.symbol + '$-409]#,##0.00'})
    account_type = workbook.add_format({'bold': True, 'align': 'left', 'text_wrap': True, 'border': True,
                                        'valign': 'vcenter'})
    lname = workbook.add_format({'align': 'center', 'text_wrap': True, 'border': True})
    header = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'font_size': 24, 'bold': True})

    # Header Information
    sheet = workbook.add_worksheet("Report Sheet")
    row = 0
    sheet.merge_range(row, 0, row, 8, self.env.company.name + ": General Ledger", header)
    sheet.set_row(row, 30)
    row += 1
    sheet.merge_range(row, 0, row, 2, 'Journal:', workbook.add_format({'bold': True}))
    sheet.merge_range(row, 3, row, 5, 'Display Account', workbook.add_format({'bold': True}))
    sheet.merge_range(row, 6, row, 8, 'Target Moves:', workbook.add_format({'bold': True}))
    row += 1
    sheet.merge_range(row, 0, row, 2, ', '.join([lt or '' for lt in data['print_journal']]))
    sheet.merge_range(row, 3, row, 5, display_account)
    sheet.merge_range(row, 6, row, 8, target_move)
    row += 1
    sheet.merge_range(row, 0, row, 2, 'Sorted By: ', workbook.add_format({'bold': True}))
    row += 1
    sheet.merge_range(row, 0, row, 2, sortby)

    # Table of content
    row += 2
    sheet.set_column("A:I", 20)
    sheet.write(row, 0, "Date", bold)
    sheet.write(row, 1, "JRNL", bold)
    sheet.write(row, 2, "Partner", bold)
    sheet.write(row, 3, "Ref", bold)
    sheet.write(row, 4, "Move", bold)
    sheet.write(row, 5, "Entry Label", bold)
    sheet.write(row, 6, "Debit", bold)
    sheet.write(row, 7, "Credit", bold)
    sheet.write(row, 8, "Balance", bold)
    sheet.set_row(row, 25)

    for account in data['Accounts']:
      row += 1
      sheet.set_row(row, 20)
      sheet.merge_range(row, 0, row, 5, account['code'] + " " + account['name'], account_type)
      sheet.write(row, 6, account['debit'], currency_format)
      sheet.write(row, 7, account['credit'], currency_format)
      sheet.write(row, 8, account['balance'], currency_format)
      for line in account['move_lines']:
        row += 1
        sheet.write(row, 0, str(line['ldate']), border)
        sheet.write(row, 1, line['lcode'], border)
        sheet.write(row, 2, line['partner_name'], border)
        sheet.write(row, 3, line['lref'], border)
        sheet.write(row, 4, line['move_name'], border)
        sheet.write(row, 5, line['lname'], lname)
        sheet.write(row, 6, line['debit'], currency_format)
        sheet.write(row, 7, line['credit'], currency_format)
        sheet.write(row, 8, line['balance'], currency_format)
