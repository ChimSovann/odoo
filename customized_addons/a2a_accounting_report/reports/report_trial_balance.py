from odoo import models


class TrailBalanceExcelTemplate(models.AbstractModel):
  _name = 'report.a2a_accounting_report.report_trial_balance_xlsx'
  _inherit = ['report.odoo_report_xlsx.abstract', 'report.accounting_pdf_reports.report_trialbalance']

  def generate_xlsx_report(self, workbook, data, line):
    form_data = data['form']
    account_res = self._get_report_values('', data=data)
    row = 3
    max_account_name_length = 0
    if account_res['Accounts']:
      max_account_name_length = max([len(account['name']) for account in account_res["Accounts"]])
    workbook.default_format_properties = {'font_name': 'Arial', 'font_size': 10}

    # Define Format
    # /* Updated Format:
    # - Added new two bold format, normal_bold & account_format_bold, for parent account*/
    big_bold = workbook.add_format(
      {'font_size': 20, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': True})
    name = workbook.add_format(
      {'font_size': 13, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': True})
    account_name = workbook.add_format({'font_size': 13, 'text_wrap': True, 'indent': 1, 'border': True})
    entries_format = workbook.add_format(
      {'font_size': 13, 'align': 'right', 'valign': 'vcenter', 'text_wrap': True, 'border': True,
       'num_format': '[' + self.env.company.currency_id.symbol + '$ -409]#,##0.00'})
    entries_format_bold = workbook.add_format(
      {'font_size': 13, 'align': 'right', 'valign': 'vcenter','bold': True, 'text_wrap': True, 'border': True,
       'num_format': '[' + self.env.company.currency_id.symbol + '$ -409]#,##0.00'})
    name_bold = workbook.add_format(
      {'font_size': 13, 'align': 'center', 'valign': 'vcenter','bold': True, 'text_wrap': True, 'border': True})
    account_name_bold = workbook.add_format({'font_size': 13,'bold': True,'text_wrap': True, 'indent': 1, 'border': True})

    # Create a new sheet, and define sheet layout
    sheet = workbook.add_worksheet("Trail balance Excel")
    sheet.set_row(0, 50)
    sheet.set_column('A:A', 15)
    sheet.set_column('B:B', max_account_name_length + 20)
    sheet.set_column('C:E', 20)

    # Res Company, and Header
    sheet.merge_range(0, 0, 0, 4, f"{form_data['company_id'][1]}: Trail Balance", big_bold)

    # Display account
    display_acc = 'All accounts' if form_data['display_account'] == 'all' \
      else 'With Movement' if form_data['display_account'] == 'movement' \
      else 'With balance not equal to zero'
    # sheet.merge_range(1, 0, 1, 1, f'Display Account: {display_acc}', normal_bold)
    sheet.merge_range(1, 0, 1, 1, '', name_bold)
    sheet.write_rich_string(1, 0, "Display Account: ", name, display_acc, name_bold)

    # Date from
    if form_data["date_from"]:
      sheet.write_rich_string(1, 2, 'Date from: ', name, form_data["date_from"], name_bold)
    else:
      sheet.write(1, 2, 'Date from: ', name_bold)

    # Date to
    if form_data["date_to"]:
      sheet.write_rich_string(1, 3, 'Date to: ', name, form_data["date_to"], name_bold)
    else:
      sheet.write(1, 3, 'Date to: ', name_bold)

    # Target move
    sheet.write_rich_string(1, 4, 'Target Moves: ', name, f'\n{"All Entries" if form_data["target_move"] == "all" else "All Post Entries"}',
                name_bold)

    # Code account debit credit balance
    sheet.set_row(3, 20)
    sheet.write(2, 0, 'Code', name_bold)
    sheet.write(2, 1, 'Account', name_bold)
    sheet.write(2, 2, 'Debit', name_bold)
    sheet.write(2, 3, 'Credit', name_bold)
    sheet.write(2, 4, 'Balance', name_bold)

    # For Loop into each account,
    # /* Updated template:
    # - Added condition for account code and account name to get bold for 'is_parent'
    # - Added '  ' * (account['level']) to show hierarchy of parent and child account*/
    for account in account_res["Accounts"]:
      if account['is_parent'] == True:
        sheet.set_row(row, 20)
        sheet.write(row, 0, account['code'], name_bold)
        sheet.write(row, 1,  '  ' * (account['level'])  + account['name'], account_name_bold)
        sheet.write(row, 2, account['debit'], entries_format_bold)
        sheet.write(row, 3,  account['credit'] , entries_format_bold)
        sheet.write(row, 4,  account['balance'], entries_format_bold)
        row += 1
      elif account['is_parent'] != True:
        sheet.write(row, 0, account['code'], name)
        sheet.write(row, 1, '  ' * (account['level']) + account['name'], account_name)
        sheet.write(row, 2, account['debit'], entries_format)
        sheet.write(row, 3, account['credit'], entries_format)
        sheet.write(row, 4, account['balance'], entries_format)
        row += 1


