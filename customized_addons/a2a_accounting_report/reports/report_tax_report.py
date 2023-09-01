from odoo import models


class TrailBalanceExcelTemplate(models.AbstractModel):
  _name = 'report.a2a_accounting_report.report_tax_report_xlsx'
  _inherit = ['report.odoo_report_xlsx.abstract', 'report.accounting_pdf_reports.report_tax']

  def generate_xlsx_report(self, workbook, data, line):
    account = self._get_report_values('', data=data)
    workbook.default_format_properties = {'font_name': 'Arial', 'font_size': 10}
    # Define Format
    header = workbook.add_format(
      {'font_size': 17, 'align': 'left', 'valign': 'vcenter', 'bold': True, 'indent': 1})
    sub_header = workbook.add_format(
      {'font_size': 13, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'indent': 1})
    title = workbook.add_format(
      {'font_size': 13, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'indent': 1, 'bold': True,
       'border': True})
    normal = workbook.add_format(
      {'font_size': 13, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'border': True, 'indent': 1})
    currency_format = workbook.add_format({'align': 'left', 'indent': 1, 'border': True, 'text_wrap': True, 'valign': 'vcenter',
                                           'num_format': '[' + self.env.company.currency_id.symbol + '$ -409]#,##0.00'})

    # Create a new sheet, and define sheet layout
    sheet = workbook.add_worksheet("Tax Report Excel")
    sheet.set_row(0, 40)
    sheet.set_row(1, 30)
    sheet.set_column('A:C', 35)

    # Header
    sheet.merge_range(0, 0, 0, 2, "Tax Report", header)

    # Company
    sheet.write(1, 0, f"Company: {account['data']['company_id'][1]}", sub_header)

    # Date from
    sheet.write(1, 1, f"Date from: {account['data']['date_from']}", sub_header)

    # Date to
    sheet.write(1, 2, f"Date to: {account['data']['date_to']}", sub_header)

    sheet.set_row(2, 20)
    sheet.write(2, 0, 'Sale', title)
    sheet.write(2, 1, 'Net', title)
    sheet.write(2, 2, 'Tax', title)

    current_row = 3
    # Loop through every sale line
    for line in account['lines']['sale']:
      sheet.set_row(current_row, 20)
      sheet.write(current_row, 0, line['name'], normal)
      sheet.write(current_row, 1, line['net'], currency_format)
      sheet.write(current_row, 2, line['tax'], currency_format)
      current_row += 1

    sheet.set_row(current_row, 20)
    sheet.merge_range(current_row, 0, current_row, 2, "Purchase", title)
    current_row += 1
    # Loop through every purchase line
    for line in account['lines']['purchase']:
      sheet.set_row(current_row, 20)
      sheet.write(current_row, 0, line['name'], normal)
      sheet.write(current_row, 1, line['net'], currency_format)
      sheet.write(current_row, 2, line['tax'], currency_format)
      current_row += 1
