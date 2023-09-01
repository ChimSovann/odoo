import copy

from odoo import models, fields
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import datetime
import xlwt
from xlsxwriter.workbook import Workbook
from six import BytesIO
import base64


class AccountAgePartner(models.TransientModel):
    _inherit = "account.aged.trial.balance"
    aged_partner_report_excel_file = fields.Binary('Aged Partner Report Excel')

    def _print_report_xlsx(self, data):

        """
        Arguments: Data(Passed from get_partner_move_lines
        For print Excel report for Aged Partner report
            Steps:
            + Grab the data for inserting into the excel
            + Create and Style the excel
            + Return the url to download the excel file

        """

        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])

        period_length = data['form']['period_length']
        if period_length <= 0:
            raise ValidationError('You must set a period length greater than 0.')
        if not data['form']['date_from']:
            raise ValidationError('You must set a start date.')

        start = data['form']['date_from']
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5 - (i + 1)) * period_length) + '-' + str((5 - i) * period_length)) or (
                            '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']

        movelines, total, dummy = self.env['report.accounting_pdf_reports.report_agedpartnerbalance']._get_partner_move_lines(
                                                                                        account_type,
                                                                                        str(data['form']['date_from']),
                                                                                        data['form']['target_move'],
                                                                                        period_length)
        # Create the worksheet
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('Aged Partner Report')
        worksheet.col(0).width = 256 * 30
        worksheet.col(1).width = 256 * 20
        worksheet.col(2).width = 256 * 20
        worksheet.col(3).width = 256 * 20
        worksheet.col(4).width = 256 * 20
        worksheet.col(5).width = 256 * 20
        worksheet.col(6).width = 256 * 20
        worksheet.col(7).width = 256 * 20
        worksheet.row(1).height = 500
        # Styling
        header_style = xlwt.easyxf('font:height 200; align: horiz center;')
        title_style = xlwt.easyxf('font:height 400,  bold True; align: horiz left, vert center; ')
        sub_header_style = xlwt.easyxf('font:height 170, bold True;align: horiz left;')
        sub_header_input_style = xlwt.easyxf('font:height 170;align: horiz left;')
        data_header_name_style = xlwt.easyxf('font:height 200,  bold True; align: horiz left, vert center'
                                             '; borders: right_color black, left_color black,top_color black'
                                             ', bottom_color black, right thin, left thin, bottom thin, top thin;')
        data_header_style = xlwt.easyxf('font:height 200, bold True;align: vert top, horiz left; '
                                        'borders: right_color black, left_color black, top_color black'
                                        ',bottom_color black, right thin, left thin,bottom thin, top thin;')
        data_header1_style = xlwt.easyxf('font:height 200, bold True;align: vert top, horiz center; '
                                         'borders: right_color black, left_color black, top_color black'
                                         ',bottom_color black, right thin, left thin,bottom thin, top thin;')
        data_name_style = xlwt.easyxf('font:height 200; align: horiz left, vert center'
                                             '; borders: right_color black, left_color black,top_color black'
                                             ', bottom_color black, right thin, left thin, bottom thin, top thin;')
        data_style = xlwt.easyxf('font:height 200;align: vert top, horiz left;borders: right_color black'
                                 ', left_color black, top_color black,bottom_color black, right thin'
                                 ', left thin,bottom thin, top thin;')
        data_of_transaction_style = xlwt.easyxf('font:height 200;align: vert center, horiz center; '
                                                'borders: right_color black, left_color black, top_color black, '
                                                'bottom_color black, right thin, left thin, bottom thin, top thin;')
        currency_format = copy.deepcopy(data_of_transaction_style)
        currency_format.num_format_str = "$ 0.00"
        currency_format.alignment.horz = 3

        row = 0
        # Header
        worksheet.write(row, row, str(datetime.date.today()), sub_header_input_style)
        worksheet.write_merge(row, row, 1, 7, data['form']['company_id'][1], header_style)
        worksheet.write_merge(row + 1, row + 1, 0, 7, 'Aged Partner Balance', title_style)
        # Sub Header
        row = 2
        worksheet.write(row, 0, 'Start Date: ', sub_header_style)
        worksheet.write(row + 1, 0, str(data['form']['date_from']), sub_header_input_style)
        worksheet.write(row + 2, 0, "Partner's: ", sub_header_style)
        # Condition for Partner's
        if data['form']['result_selection'] == 'customer':
            worksheet.write(row + 3, 0, 'Receivable Accounts', sub_header_input_style)
        elif data['form']['result_selection'] == 'supplier':
            worksheet.write(row + 3, 0, 'Payable Accounts', sub_header_input_style)
        elif data['form']['result_selection'] == 'customer_supplier':
            worksheet.write(row + 3, 0, 'Receivable and Payable Accounts', sub_header_input_style)
        # body
        worksheet.write(row, 1, 'Period Length (days): ', sub_header_style)
        worksheet.write(row + 1, 1, period_length, sub_header_input_style)
        worksheet.write(row + 2, 1, "Target Moves: ", sub_header_style)
        # Condition for Target Moves
        if data['form']['target_move'] == 'all':
            worksheet.write(row + 3, 1, 'All Entries ', sub_header_input_style)
        elif data['form']['target_move'] == 'posted':
            worksheet.write(row + 3, 1, 'All Posted Entries', sub_header_input_style)
        # data header
        row = 6
        worksheet.write(row, 0, 'Partners', data_header_name_style)
        worksheet.write(row, 1, 'Not due', data_header1_style)
        worksheet.write(row, 2, data['form']['4']['name'], data_header1_style)
        worksheet.write(row, 3, data['form']['3']['name'], data_header1_style)
        worksheet.write(row, 4, data['form']['2']['name'], data_header1_style)
        worksheet.write(row, 5, data['form']['1']['name'], data_header1_style)
        worksheet.write(row, 6, data['form']['0']['name'], data_header1_style)
        worksheet.write(row, 7, 'Total', data_header1_style)
        # Account Total
        row += 1
        if len(total):
            data_name_style_bold = copy.deepcopy(data_name_style)
            currency_format_bold = copy.deepcopy(currency_format)
            data_name_style_bold.font.bold = currency_format_bold.font.bold = True
            worksheet.write(row, 0, 'Account Total', data_name_style_bold)
            worksheet.write(row, 1, total[6], currency_format_bold)
            worksheet.write(row, 2, total[4], currency_format_bold)
            worksheet.write(row, 3, total[3], currency_format_bold)
            worksheet.write(row, 4, total[2], currency_format_bold)
            worksheet.write(row, 5, total[1], currency_format_bold)
            worksheet.write(row, 6, total[0], currency_format_bold)
            worksheet.write(row, 7, total[5], currency_format_bold)
        # data
        current_row, next_row = 13, 14
        for partner in movelines:
            row += 1
            worksheet.write(row, 0, partner['name'], data_name_style)
            worksheet.write(row, 1, partner['direction'], currency_format)
            worksheet.write(row, 2, partner['4'], currency_format)
            worksheet.write(row, 3, partner['3'], currency_format)
            worksheet.write(row, 4, partner['2'], currency_format)
            worksheet.write(row, 5, partner['1'], currency_format)
            worksheet.write(row, 6, partner['0'], currency_format)
            worksheet.write(row, 7, partner['total'], currency_format)

        fp = BytesIO()
        workbook.save(fp)
        self.aged_partner_report_excel_file = base64.encodebytes(fp.getvalue())
        fp.close()

        # __________________________________________
        # | Return the URL to download the report  |
        # __________________________________________

        return {
            'type': 'ir.actions.act_url',
            'name': 'Aged Partner Report',
            'url': '/web/content/account.aged.trial.balance/%s/aged_partner_report_excel_file/'
                   'Aged Partner Report.xls?download=true' % (
                       self.id),
        }