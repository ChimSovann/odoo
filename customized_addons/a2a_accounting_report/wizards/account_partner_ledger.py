from odoo import models, fields
import datetime
import xlwt
from xlsxwriter.workbook import Workbook
from six import BytesIO
import base64
import copy

class AccountPartnerLedger(models.TransientModel):
  _inherit = "account.report.partner.ledger"
  partner_ledger_report_excel_file = fields.Binary('Partner Ledger')

  def _print_report_xlsx(self, data):
    """
    Arguments: Data (Passed from check report function)
    For print Excel report for Partner Ledger Account
        Steps:
        + Grab the data for inserting into the excel
        + Create and Style the excel
        + Return the url to download the excel file

    Function return: URL to download the binary excel file
    """

    # __________________________________________
    # | Generate the data for the excel report  |
    # __________________________________________

    data = self.pre_print_report(data)
    data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency})
    pl_data = self.get_context(data=data)

    # Call sum_partner function and line function to generate sum_partner and line data ( Partner Ledger concepts )
    sum_partner = pl_data['sum_partner']
    lines = pl_data['lines']

    # __________________________________________
    # | Create and Style the report            |
    # __________________________________________

    # Create the worksheet
    workbook = xlwt.Workbook(encoding="UTF-8")
    worksheet = workbook.add_sheet('Partner Ledger')
    worksheet.col(0).width = 256 * 15
    worksheet.col(1).width = 256 * 15
    worksheet.col(2).width = 256 * 15
    worksheet.col(3).width = 256 * 30
    worksheet.col(4).width = 256 * 15
    worksheet.col(5).width = 256 * 15
    worksheet.col(6).width = 256 * 15
    worksheet.row(1).height = 500
    # Styling

    header_style = xlwt.easyxf('font:height 200; align: horiz center;')
    title_style = xlwt.easyxf('font:height 400,  bold True; align: horiz left, vert center;')
    sub_header_style = xlwt.easyxf('font:height 200, bold True;align: horiz left;')
    sub_header_input_style = xlwt.easyxf('font:height 200;align: horiz left;')
    date_title_style = xlwt.easyxf('font:height 200,  bold True; align: horiz center, vert center; '
                                   'borders: right_color black, left_color black,top_color black,'
                                   'bottom_color black, right thin, left thin, bottom thin, top thin;')
    data_of_company_style = xlwt.easyxf('font:height 200, bold True;align: vert center; '
                                        'borders: right_color black, left_color black, top_color black, '
                                        'bottom_color black, right thin, left thin,bottom thin, top thin;')
    data_of_transaction_style = xlwt.easyxf('font:height 200;align: vert center; '
                                            'borders: right_color black, left_color black, top_color black, '
                                            'bottom_color black, right thin, left thin, bottom thin, top thin;')
    currency_format = copy.deepcopy(data_of_transaction_style)
    currency_format.num_format_str = "$ 0.00"
    currency_format.alignment.horz = 3
    # Header
    worksheet.write(0, 0, str(datetime.date.today()), sub_header_input_style)
    worksheet.write_merge(0, 0, 1, 6, pl_data['form']['company_id'][1], header_style)
    worksheet.write_merge(1, 1, 0, 6, 'Partner Ledger', title_style)
    # Insert Company, Target Move, Selected Date data to the the sheet
    worksheet.write_merge(2, 2, 0, 2, 'Company:', sub_header_style)

    if pl_data['data']['form']['date_from'] is not False:
      worksheet.write_merge(2, 2, 3, 4, 'Date from: ' + str(pl_data['data']['form']['date_from']), sub_header_style)

    if pl_data['data']['form']['date_to'] is not False:
      worksheet.write_merge(3, 3, 3, 4, 'Date to: ' + str(pl_data['data']['form']['date_to']), sub_header_style)

    worksheet.write_merge(2, 2, 5, 6, 'Target Moves:', sub_header_style)

    worksheet.write_merge(3, 3, 0, 2, pl_data['form']['company_id'][1], sub_header_input_style)

    if pl_data['form']['target_move'] == 'all':
      worksheet.write_merge(3, 3, 5, 6, 'All Entries', sub_header_input_style)
    elif pl_data['form']['target_move'] == 'posted':
      worksheet.write_merge(3, 3, 5, 6, 'All Posted Entries', sub_header_input_style)
    row = 4
    # Data title or column
    worksheet.write(row, 0, 'Date', date_title_style)
    worksheet.write(row, 1, 'JRNL', date_title_style)
    worksheet.write(row, 2, 'Account', date_title_style)
    worksheet.write(row, 3, 'Ref', date_title_style)
    worksheet.write(row, 4, 'Debit', date_title_style)
    worksheet.write(row, 5, 'Credit', date_title_style)
    worksheet.write(row, 6, 'Balance', date_title_style)

    # Partner Ledger Records

    current_row, next_row = 9, 10
    for record in pl_data['docs']:
      row += 1
      worksheet.write_merge(row, row, 0, 3, record['name'], data_of_company_style)
      worksheet.write(row, 4, sum_partner(pl_data['data'], record, 'debit'), currency_format)
      worksheet.write(row, 5, sum_partner(pl_data['data'], record, 'credit'), currency_format)
      worksheet.write(row, 6, sum_partner(pl_data['data'], record, 'debit - credit'), currency_format)
      current_row = next_row + 1
      next_row += 2

      for line in lines(pl_data['data'], record):
        row += 1
        worksheet.write(row, 0, str(line['date']), data_of_transaction_style)
        worksheet.write(row, 1, line['code'], data_of_transaction_style)
        worksheet.write(row, 2, line['a_code'], data_of_transaction_style)
        worksheet.write(row, 3, line['displayed_name'], data_of_transaction_style)
        worksheet.write(row, 4, line['debit'], currency_format)
        worksheet.write(row, 5, line['credit'], currency_format)
        worksheet.write(row, 6, line['progress'], currency_format)

    fp = BytesIO()
    workbook.save(fp)
    self.partner_ledger_report_excel_file = base64.encodebytes(fp.getvalue())
    fp.close()

    # __________________________________________
    # | Return the URL to download the report  |
    # __________________________________________

    return {
      'type': 'ir.actions.act_url',
      'name': 'Partner Ledger',
      'url': '/web/content/account.report.partner.ledger/%s/partner_ledger_report_excel_file/'
             'Partner Ledger Report Excel.xls?download=true' % (
               self.id),
    }

  def get_context(self, data):
    """"
        This function generate the data based on the given input from the wizard
    """
    return self.env.ref('accounting_pdf_reports.action_report_partnerledger')._get_rendering_context(self,
                                                                                                     data=data)
