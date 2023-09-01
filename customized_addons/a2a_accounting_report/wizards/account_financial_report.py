from odoo import models, fields
import datetime
import xlwt
from xlsxwriter.workbook import Workbook
from six import BytesIO
import base64
import copy


class AccountFinancialReport(models.TransientModel):
    _inherit = "accounting.report"
    financial_report_excel_file = fields.Binary('Report Financial Excel')

    def _print_report_xlsx(self, data):

        """
        Arguments: Data(Passed from get account line and check report function
        For print Excel report for Financial report
            Steps:
            + Grab the data for inserting into the excel
            + Create and Style the excel
            + Set condition for each filter
            + Return the url to download the excel file

        """

        data['form'].update(self.read(['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp',
                                       'account_report_id', 'enable_filter', 'label_filter', 'target_move'])[0])
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        account_line = self.env['report.accounting_pdf_reports.report_financial'].get_account_lines(data=data['form'])
        currency = self.env.company.currency_id

        # Create the worksheet
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet(data['form']['account_report_id'][1])
        worksheet.col(0).width = 256 * 40
        worksheet.col(1).width = 256 * 20
        worksheet.col(2).width = 256 * 20
        worksheet.col(3).width = 256 * 20
        worksheet.col(4).width = 256 * 20
        worksheet.row(1).height = 500
        # Styling
        header_style = xlwt.easyxf('font:height 200; align: horiz center, vert center;')
        title_style = xlwt.easyxf('font:height 400,  bold True; align: horiz left, vert center; ')
        sub_header_style = xlwt.easyxf('font:height 200, bold True;align: horiz left, vert center;')
        sub_header_input_style = xlwt.easyxf('font:height 200;align: horiz left, vert center;')
        data_header_name_style = xlwt.easyxf('font:height 200,  bold True; align: horiz left, vert center'
                                             '; borders: right_color black, left_color black,top_color black'
                                             ', bottom_color black, right thin, left thin, bottom thin, top thin;')
        data_header_style = xlwt.easyxf('font:height 200, bold True;align: vert top, horiz center, vert center; '
                                        'borders: right_color black, left_color black, top_color black'
                                        ',bottom_color black, right thin, left thin,bottom thin, top thin;')
        data_of_transaction_bold = copy.deepcopy(data_header_style)
        data_of_transaction_bold.alignment.horz = 3
        data_of_transaction_bold.num_format_str = currency.symbol + " 0.00"
        data_of_transaction_style = copy.deepcopy(data_of_transaction_bold)
        data_of_transaction_style.font.bold = False
        leaf_node = xlwt.easyxf('font:height 200; align: horiz left, vert center; '
                                'borders: right_color black, left_color black,top_color black,'
                                'bottom_color black, right thin, left thin, bottom thin, top thin;')

        # Header
        worksheet.write(0, 0, str(datetime.date.today()), sub_header_input_style)
        # Target Move
        worksheet.write(3, 0, 'Target Moves: ', sub_header_style)
        if data['form']['target_move'] == 'all':
            worksheet.write(4, 0, 'All Entries ', sub_header_input_style)
        elif data['form']['target_move'] == 'posted':
            worksheet.write(4, 0, 'All Posted Entries', sub_header_input_style)
            # Date From & To
        if data['form']['date_from'] is not False:
            worksheet.write(3, 1, 'Date From: ' + str(data['form']['date_from']),sub_header_input_style)
        if data['form']['date_to'] is not False:
            worksheet.write(4, 1, 'Date to: ' + str(data['form']['date_to']),sub_header_input_style)
        row = 5
        # condition for selected Debit_Credit check box
        if data['form']['debit_credit'] == 1:
            worksheet.write_merge(0, 0, 1, 3, data['form']['company_id'][1], header_style)
            worksheet.write_merge(1, 1, 0, 3, data['form']['account_report_id'][1], title_style)
            worksheet.write(row, 0, 'Name', data_header_name_style)
            worksheet.write(row, 1, 'Debit', data_header_style)
            worksheet.write(row, 2, 'Credit', data_header_style)
            worksheet.write(row, 3, 'Balance', data_header_style)
            for line in account_line:
                if line['level'] != 0:
                    row += 1
                    worksheet.write(row, 0, "  " * int(line.get("level")) + line.get('name'),
                                          leaf_node if line.get('type') == 'account' else data_header_name_style)

                    worksheet.write(row, 1, line.get('debit'), data_of_transaction_style if line.get('type') == 'account'
                                                                else data_of_transaction_bold)
                    worksheet.write(row, 2, line.get('credit'), data_of_transaction_style if line.get('type') == 'account'
                                                                else data_of_transaction_bold)
                    worksheet.write(row, 3, line.get('balance'), data_of_transaction_style if line.get('type') == 'account'
                                                                else data_of_transaction_bold)

        # condition without select any check box
        elif not data['form']['enable_filter'] and not data['form']['debit_credit']:
            worksheet.write_merge(0, 0, 1, 1, data['form']['company_id'][1], header_style)
            worksheet.write_merge(1, 1, 0, 1, data['form']['account_report_id'][1], title_style)
            worksheet.write(row, 0, 'Name', data_header_name_style)
            worksheet.write(row, 1, 'Balance', data_header_style)
            for line in account_line:
                if line['level'] != 0:
                    row += 1
                    worksheet.write(row, 0, "  " * int(line.get("level")) + line.get('name'),
                                          leaf_node if line.get('type') == 'account' else data_header_name_style)
                    worksheet.write(row, 1, line.get('balance'),data_of_transaction_style if line.get('type') == 'account'
                                                                else data_of_transaction_bold)

        # Condition for selected Enable Comparison
        elif data['form']['enable_filter'] and not data['form']['debit_credit']:
            worksheet.write_merge(0, 0, 1, 2, data['form']['company_id'][1], header_style)
            worksheet.write_merge(1, 1, 0, 2, data['form']['account_report_id'][1], title_style)
            worksheet.write(row, 0, 'Name', data_header_name_style)
            worksheet.write(row, 1, 'Balance', data_header_style)
            worksheet.write(row, 2, data['form']['label_filter'], data_header_style)
            for line in account_line:
                if line['level'] != 0:
                    row += 1
                    worksheet.write(row, 0, "  " * int(line.get("level")) + line.get('name'),
                                          leaf_node if line.get('type') == 'account' else data_header_name_style)

                    worksheet.write(row, 1, line.get('balance'), data_of_transaction_style if line.get('type') == 'account'
                                                                else data_of_transaction_bold)
                    worksheet.write(row, 2, line.get('balance_cmp'), data_of_transaction_style if line.get('type') == 'account'
                                                                else data_of_transaction_bold)

        fp = BytesIO()
        workbook.save(fp)
        self.financial_report_excel_file = base64.encodebytes(fp.getvalue())
        fp.close()

        # __________________________________________#
        #   Return the URL to download the report   #
        # __________________________________________#

        return {
            'type': 'ir.actions.act_url',
            'name': 'Financial Report',
            'url': '/web/content/accounting.report/%s/financial_report_excel_file/'
                   f'{data["form"]["account_report_id"][1]}.xls?download=true' % (
                       self.id),
        }