from odoo import api, fields, models
from datetime import datetime, timedelta
import xlwt
from xlsxwriter.workbook import Workbook
from six import BytesIO
import base64

from werkzeug.routing import ValidationError


class StockMoveReport(models.TransientModel):
    """
    This model is for calculate the stock in, stock out, opening quantity and ending quantity of products in a
    specific location between a start date and an end date.
    ***Note:
    - Dummy fields are fields that need to set their Index property to False in order for the model to work due to
    the configuration from the parent model
    """

    _inherit = "stock.move"
    _name = "stock.move.report"

    # Start Dummy Field
    name = fields.Char("Dummy field", default=123)
    product_id = fields.Many2one(
        'product.product', 'Product', index=False, required=False)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=False)
    move_dest_ids = fields.Integer("Dummy field")
    move_orig_ids = fields.Integer("Dummy field")
    route_ids = fields.Integer("Dummy field")
    location_id = fields.Many2one(
        'stock.location', 'Source Location', index=False, required=False)
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location', index=False, required=False)

    # End Dummy Field

    stock_move_report_excel_file = fields.Binary('Stock Move Report')
    inventory_start_date = fields.Datetime("Inventory start at Date", required=True,
                                           default=datetime.now().replace(hour=23, minute=00,
                                                                          second=00) - timedelta(
                                               days=2))
    inventory_end_date = fields.Datetime("Inventory end at Date", required=True,
                                         default=datetime.now().replace(hour=16, minute=59,
                                                                        second=59) - timedelta(
                                             days=1))
    location = fields.Many2one(
        'stock.location', 'Location',
        index=False, required=True,
        help="Set a location to get the product report from")

    # if has conflict with mrp when printing stock move report uncomment this function
    # @api.depends('raw_material_production_id.name')
    # def _compute_reference(self):
    #     pass

    @api.constrains('inventory_end_date', 'inventory_start_date')
    def _check_date_domain(self):
        if self.inventory_end_date >= datetime.today():
            raise ValidationError('End date must not be greater than today!')
        if self.inventory_start_date >= datetime.today():
            raise ValidationError('Start date must not be greater than today!')
        if self.inventory_start_date > self.inventory_end_date:
            raise ValidationError('Start date can not be greater than end date!')

    def get_stock_report(self):
        """
        This function is dedicated to calculate the stock report for a specific location between a start date
             and end date using a certain formula. The required data is the stock in number, the stock out number, the
             opening quantity number and ending quantity number. The formula use the current quantity of a specific
             product and the stock move of that specific products from a start date to get the opening quantity of that
             product in the specified start date.
             ***Formula -- Note that -> ( from start date to end date) = *
             - Opening quantity* = current quantity + current stock out - current stock in
             - Ending quantity*  = Opening quantity* + stock in* - stock out*
             :return: a list containing objects which has details of each item
        """
        stock_move_earliest = self.env['stock.move'].search([('create_date', '<=', datetime.today())])
        stock_move_current = self.env['stock.move'].search([('create_date', '>=', self.inventory_start_date),
                                                            ('create_date', '<=', datetime.today())])
        stock_move = self.env['stock.move'].search([('create_date', '>=', self.inventory_start_date),
                                                    ('create_date', '<=', self.inventory_end_date)])
        stock_move_line = self.env['stock.move.line'].search([('date', '>=', self.inventory_start_date),
                                                    ('date', '<=', self.inventory_end_date)])
        stock_quan = self.env['stock.quant'].search([('location_id.complete_name', '=', self.location.complete_name)])
        product_quan = {}

        stock_move_line_product = self.env['stock.move.line'].search([('product_id.name', '=', '"IMAGE" A0-E007-058 : Output board')])

        for rec in stock_move_line_product:
            print(rec.location_id.complete_name, " + ", rec.qty_done)

        for rec in stock_quan:
            product_quan[rec.product_id] = {
                "ref": rec.product_id.default_code,
                "name": rec.product_id.name,
                "product_uom": rec.product_uom_id.name,
                "row_num": 10,
                "opening_qty": 0,
                "ending_qty": 0,
                "stock_in": 0,
                "stock_out": 0,
                "current_quantity": rec.quantity,
                "stock_in_current": 0,
                "stock_out_current": 0,
                "stock_in_current_adjustment": 0,
                "stock_out_current_adjustment": 0,
                "ending_adjustment_qty": 0,
                "stock_in_adjustment": 0,
                "stock_out_adjustment": 0,
            }

        for rec in stock_move_current:
            if rec.state == "done" and rec.product_id.type == "product":
                if self.location.complete_name == rec.location_id.complete_name:
                    if rec.product_id in product_quan:
                        product_quan[rec.product_id]["stock_out_current"] += rec.product_qty
                    else:
                        product_quan[rec.product_id] = {
                            "ref": rec.product_id.default_code,
                            "name": rec.product_id.name,
                            "product_uom": rec.product_uom.name,
                            "row_num": 10,
                            "opening_qty": 0,
                            "ending_qty": 0,
                            "stock_in": 0,
                            "stock_out": 0,
                            "current_quantity": 0,
                            "stock_in_current": 0,
                            "stock_out_current": 0,
                            "stock_in_current_adjustment": 0,
                            "stock_out_current_adjustment": 0,
                            "ending_adjustment_qty": 0,
                            "stock_in_adjustment": 0,
                            "stock_out_adjustment": 0,
                        }
                        product_quan[rec.product_id]["stock_out_current"] += rec.product_qty

                elif self.location.complete_name == rec.location_dest_id.complete_name:
                    if rec.product_id in product_quan:
                        product_quan[rec.product_id]["stock_in_current"] += rec.product_qty
                    else:
                        product_quan[rec.product_id] = {
                            "ref": rec.product_id.default_code,
                            "name": rec.product_id.name,
                            "product_uom": rec.product_uom.name,
                            "row_num": 10,
                            "opening_qty": 0,
                            "ending_qty": 0,
                            "stock_in": 0,
                            "stock_out": 0,
                            "current_quantity": 0,
                            "stock_in_current": 0,
                            "stock_out_current": 0,
                            "stock_in_current_adjustment": 0,
                            "stock_out_current_adjustment": 0,
                            "ending_adjustment_qty": 0,
                            "stock_in_adjustment": 0,
                            "stock_out_adjustment": 0,
                        }
                        product_quan[rec.product_id]["stock_in_current"] += rec.product_qty

        for rec in stock_move:
            if rec.state == "done" and rec.product_id.type == "product":
                if self.location.complete_name == rec.location_id.complete_name:
                    if rec.product_id in product_quan:
                        if rec.location_dest_id.complete_name == "Virtual Locations/A2A Town (Cambodia) Co., Ltd.: " \
                                                                 "Inventory adjustment":
                            product_quan[rec.product_id]["stock_out_adjustment"] += rec.product_qty
                        else:
                            product_quan[rec.product_id]["stock_out"] += rec.product_qty
                    else:
                        product_quan[rec.product_id] = {
                            "ref": rec.product_id.default_code,
                            "name": rec.product_id.name,
                            "product_uom": rec.product_uom.name,
                            "row_num": 10,
                            "opening_qty": 0,
                            "ending_qty": 0,
                            "stock_in": 0,
                            "stock_out": 0,
                            "current_quantity": 0,
                            "stock_in_current": 0,
                            "stock_out_current": 0,
                            "stock_in_current_adjustment": 0,
                            "stock_out_current_adjustment": 0,
                            "ending_adjustment_qty": 0,
                            "stock_in_adjustment": 0,
                            "stock_out_adjustment": 0,
                        }
                        product_quan[rec.product_id]["stock_out"] += rec.product_qty

                elif self.location.complete_name == rec.location_dest_id.complete_name:
                    if rec.product_id in product_quan:
                        if rec.location_id.complete_name == "Virtual Locations/A2A Town (Cambodia) Co., Ltd.: " \
                                                            "Inventory adjustment":
                            product_quan[rec.product_id]["stock_in_adjustment"] += rec.product_qty
                        else:
                            product_quan[rec.product_id]["stock_in"] += rec.product_qty
                    else:
                        product_quan[rec.product_id] = {
                            "ref": rec.product_id.default_code,
                            "name": rec.product_id.name,
                            "product_uom": rec.product_uom.name,
                            "row_num": 10,
                            "opening_qty": 0,
                            "ending_qty": 0,
                            "stock_in": 0,
                            "stock_out": 0,
                            "current_quantity": 0,
                            "stock_in_current": 0,
                            "stock_out_current": 0,
                            "stock_in_current_adjustment": 0,
                            "stock_out_current_adjustment": 0,
                            "ending_adjustment_qty": 0,
                            "stock_in_adjustment": 0,
                            "stock_out_adjustment": 0,
                        }
                        product_quan[rec.product_id]["stock_in"] += rec.product_qty

        for rec in stock_move_earliest:
            if rec.state == "done" and rec.product_id.type == "product":
                if self.location.complete_name == rec.location_id.complete_name or \
                        self.location.complete_name == rec.location_dest_id.complete_name:
                    if rec.product_id not in product_quan:
                        product_quan[rec.product_id] = {
                            "ref": rec.product_id.default_code,
                            "name": rec.product_id.name,
                            "product_uom": rec.product_uom.name,
                            "row_num": 10,
                            "opening_qty": 0,
                            "ending_qty": 0,
                            "stock_in": 0,
                            "stock_out": 0,
                            "current_quantity": 0,
                            "stock_in_current": 0,
                            "stock_out_current": 0,
                            "stock_in_current_adjustment": 0,
                            "stock_out_current_adjustment": 0,
                            "ending_adjustment_qty": 0,
                            "stock_in_adjustment": 0,
                            "stock_out_adjustment": 0,
                        }
        vals = []
        i = 1
        for product in product_quan:
            product_quan[product]["opening_qty"] = product_quan[product]["current_quantity"] \
                                                   + product_quan[product]["stock_out_current"] \
                                                   - product_quan[product]["stock_in_current"]
            product_quan[product]["ending_qty"] = product_quan[product]["opening_qty"] \
                                                  + product_quan[product]["stock_in"] \
                                                  - product_quan[product]["stock_out"]
            product_quan[product]["ending_adjustment_qty"] = product_quan[product]["opening_qty"] \
                                                             + product_quan[product]["stock_in_adjustment"] \
                                                             - product_quan[product]["stock_out_adjustment"] \
                                                             + product_quan[product]["stock_in"] \
                                                             - product_quan[product]["stock_out"]
            product_quan[product]["row_num"] = i
            i += 1
            vals.append(product_quan[product])

        for obj in vals:
            if str(obj['ref']) == "False":
                obj['ref'] = " "

        data = {
            'ids': self.ids,
            'models': self._name,
            'date_start': self.inventory_start_date + timedelta(hours=7),
            # added 7h to start date inorder to adjust the correct date
            'date_end': self.inventory_end_date,
            'location': self.location.complete_name,  # location complete name(including id and name)
            'location_name': self.location.name,  # location name
            'vals': vals
        }
        return data

    def generate_excel_report(self):
        """
        This function will generate an excel report when the user click confirm.
        The excel is created using xlwt module.
        :return: a url that leads to the download of the excel file
        """
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('Sheet 1')
        title_style = xlwt.easyxf(
            'font:height 360,bold True;align: horiz center;')
        worksheet.write_merge(1, 2, 1, 10, 'Report Inventory', title_style)
        dateAndtime_style = xlwt.easyxf(
            'font:height 220;align: horiz center;')
        header_style = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour white;align: horiz center;'
            ' borders: top_color black, bottom_color black, right_color black, left_color black,\
            left thin, right thin, top thin, bottom thin;'
        )
        body_style_align_left = xlwt.easyxf(
            'font:height 220; pattern: pattern solid, fore_colour white;align: horiz left;'
            ' borders: top_color black, bottom_color black, right_color black, left_color black,\
            left thin, right thin, top thin, bottom thin;'
        )
        body_style = xlwt.easyxf(
            'font:height 220; pattern: pattern solid, fore_colour white;align: horiz center;'
            ' borders: top_color black, bottom_color black, right_color black, left_color black,\
            left thin, right thin, top thin, bottom thin;'
        )
        # column width
        worksheet.col(0).width = 1500  # no
        worksheet.col(1).width = 4200  # code
        worksheet.col(2).width = 9000  # name
        worksheet.col(3).width = 2500  # unit of measure
        worksheet.col(4).width = 4000  # opening quantity
        worksheet.col(5).width = 4000  # in
        worksheet.col(6).width = 4000  # out
        worksheet.col(7).width = 4000  # ending quantity
        worksheet.col(8).width = 4000  # adjustment in
        worksheet.col(9).width = 4000  # adjustment out
        worksheet.col(10).width = 6500  # adjustment ending quantity

        # start and end date
        worksheet.write_merge(3, 3, 9, 9, f"{'From: '}" + self.get_stock_report()['date_start'].strftime("%d-%b-%Y"),
                              dateAndtime_style)
        worksheet.write_merge(3, 3, 10, 10, f"{'To: '}" + self.get_stock_report()['date_end'].strftime("%d-%b-%Y"),
                              dateAndtime_style)
        # location
        worksheet.write_merge(4, 4, 9, 9, 'Location:', dateAndtime_style)
        worksheet.write_merge(4, 4, 10, 10, self.get_stock_report()['location_name'], dateAndtime_style)
        # body
        worksheet.write_merge(5, 5, 0, 0, 'No', header_style)
        worksheet.write_merge(5, 5, 1, 1, 'Code', header_style)
        worksheet.write_merge(5, 5, 2, 2, 'Product Name', header_style)
        worksheet.write_merge(5, 5, 3, 3, 'UoM', header_style)
        worksheet.write_merge(5, 5, 4, 4, 'Opening Quantity', header_style)
        worksheet.write_merge(5, 5, 5, 5, 'In', header_style)
        worksheet.write_merge(5, 5, 6, 6, 'Out', header_style)
        worksheet.write_merge(5, 5, 7, 7, 'Ending Quantity', header_style)
        worksheet.write_merge(5, 5, 8, 8, 'Adjustment In', header_style)
        worksheet.write_merge(5, 5, 9, 9, 'Adjustment Out', header_style)
        worksheet.write_merge(5, 5, 10, 10, 'Adjustment Ending Quantity', header_style)

        top_row = 6
        bot_row = 6
        data = self.get_stock_report()['vals']
        sum_qty = 0
        sum_stock_in = 0
        sum_stock_out = 0
        sum_ending_qty = 0
        sum_stock_in_adjustment = 0
        sum_stock_out_adjustment = 0
        sum_ending_qty_adjustment = 0
        for item in data:
            worksheet.write_merge(top_row, bot_row, 0, 0, item['row_num'], body_style_align_left)
            worksheet.write_merge(top_row, bot_row, 1, 1, item['ref'], body_style_align_left)
            worksheet.write_merge(top_row, bot_row, 2, 2, item['name'], body_style_align_left)
            worksheet.write_merge(top_row, bot_row, 3, 3, item['product_uom'], body_style)
            worksheet.write_merge(top_row, bot_row, 4, 4, item['opening_qty'], body_style)
            worksheet.write_merge(top_row, bot_row, 5, 5, item['stock_in'], body_style)
            worksheet.write_merge(top_row, bot_row, 6, 6, item['stock_out'], body_style)
            worksheet.write_merge(top_row, bot_row, 7, 7, item['ending_qty'], body_style)
            worksheet.write_merge(top_row, bot_row, 8, 8, item['stock_in_adjustment'], body_style)
            worksheet.write_merge(top_row, bot_row, 9, 9, item['stock_out_adjustment'], body_style)
            worksheet.write_merge(top_row, bot_row, 10, 10, item['ending_adjustment_qty'], body_style)

            top_row = bot_row + 1
            bot_row += 1
            # calculation of the sum of all qty, stock in, stock out, ending qty
            sum_qty = sum_qty + item['opening_qty']
            sum_stock_in = sum_stock_in + item['stock_in']
            sum_stock_out = sum_stock_out + item['stock_out']
            sum_ending_qty = sum_ending_qty + item['ending_qty']
            # adding adjustment qty
            sum_stock_in_adjustment = sum_stock_in_adjustment + item['stock_in_adjustment']
            sum_stock_out_adjustment = sum_stock_out_adjustment + item['stock_out_adjustment']
            sum_ending_qty_adjustment = sum_ending_qty_adjustment + item['ending_adjustment_qty']

        # Total column
        worksheet.write_merge(top_row, bot_row, 0, 3, 'Total', header_style)
        # calculation of the sum of all qty, stock in, stock out, ending qty
        worksheet.write_merge(top_row, bot_row, 4, 4, sum_qty, header_style)
        worksheet.write_merge(top_row, bot_row, 5, 5, sum_stock_in, header_style)
        worksheet.write_merge(top_row, bot_row, 6, 6, sum_stock_out, header_style)
        worksheet.write_merge(top_row, bot_row, 7, 7, sum_ending_qty, header_style)
        # adjustment
        worksheet.write_merge(top_row, bot_row, 8, 8, sum_stock_in_adjustment, header_style)
        worksheet.write_merge(top_row, bot_row, 9, 9, sum_stock_out_adjustment, header_style)
        worksheet.write_merge(top_row, bot_row, 10, 10, sum_ending_qty_adjustment, header_style)

        fp = BytesIO()
        workbook.save(fp)
        self.stock_move_report_excel_file = base64.encodebytes(fp.getvalue())
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'name': 'Stock move report',
            'url': '/web/content/stock.move.report/%s/stock_move_report_excel_file/stock_move_report_excel_file.xls?download=true' % (
                self.id),
        }
