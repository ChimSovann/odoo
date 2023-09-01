import xlsxwriter
from odoo import api, models


class PineViewKitchenReportXlsx(models.AbstractModel):
    _name = "report.market_list_odoo13.report_pvk_request_xlsx"
    _inherit = "report.odoo_report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, current_record):
        for obj in current_record:
            report_name = obj.name
            requester = obj.requested_by.name
            analytic_acc = obj.analytic_account_id.name
            date_request = obj.creation_date
            date_approve = obj.approve_date

            sheet = workbook.add_worksheet(report_name[:30])

            # Style
            header = workbook.add_format(
                {"align": "center", "valign": "vcenter", "font_size": 24, "bold": True, "fg_color": "silver"})
            sub_title = workbook.add_format(
                {"bold": True, "align": "left", "text_wrap": True, "border": True, "fg_color": "silver"})
            normal_text = workbook.add_format({"align": "left", "text_wrap": True, "border": True})
            bold = workbook.add_format({"bold": True, "align": "left", "text_wrap": True, "border": True})
            date_format = workbook.add_format(
                {"align": "left", "text_wrap": True, "border": True, "num_format": "mm-dd-yyyy"})
            footer_tally = workbook.add_format(
                {"bold": True, "align": "right", "text_wrap": True, "border": True, "fg_color": "silver"})
            monetary_usd = workbook.add_format(
                {"bold": True, "align": "center", "text_wrap": True, "border": True, "num_format": "$#,##0.00"})
            note_text = workbook.add_format(
                {"bold": True, "font_size": 16, "valign": "vcenter", "align": "center", "text_wrap": True,
                 "border": True, "fg_color": "red"})

            item_no = 1
            row = 7

            veg_herb_ids = obj.veg_herb_line_ids
            fruit_ids = obj.fruit_line_ids
            poultry_ids = obj.poultry_line_ids
            sea_fish_ids = obj.sea_fish_line_ids
            beef_pork_ids = obj.beef_pork_line_ids
            other_ids = obj.other_line_ids

            # Header
            sheet.merge_range("B1:L4", "Pine View Kitchen Request", header)

            # Title
            sheet.merge_range("B5:C5", "Request Reference", bold)
            sheet.merge_range("B6:C6", "Analytic Account", bold)

            ### values ###
            sheet.merge_range("D5:G5", requester, normal_text)
            sheet.merge_range("D6:G6", analytic_acc, normal_text)

            sheet.merge_range("H5:I5", "Request Date", bold)
            sheet.merge_range("H6:I6", "Approve Date", bold)

            ### values ###
            sheet.merge_range("J5:L5", date_request, date_format)
            sheet.merge_range("J6:L6", date_approve, date_format)

            # Body
            # Subtitle
            sheet.write("B7", "No.", sub_title)
            sheet.merge_range("C7:D7", "Product", sub_title)
            sheet.write("E7", "Qty", sub_title)
            sheet.write("F7", "Unit", sub_title)
            sheet.write("G7", "Est. Price", sub_title)
            sheet.write("H7", "Est. Sub Total Price", sub_title)
            sheet.merge_range("I7:J7", "Description", sub_title)
            sheet.merge_range("K7:L7", "Supplier Name", sub_title)

            if len(veg_herb_ids) > 0:
                for line in veg_herb_ids:
                    sheet.write(f"B{row + 1}", item_no, normal_text)
                    sheet.merge_range(f"C{row + 1}:D{row + 1}", line.product_id.name, normal_text)
                    sheet.write(f"E{row + 1}", line.product_qty, normal_text)
                    sheet.write(f"F{row + 1}", line.product_uom_id.name, normal_text)
                    sheet.write(f"G{row + 1}", line.price_per_unit_est, normal_text)
                    sheet.write(f"H{row + 1}", line.total_price_est, normal_text)
                    sheet.merge_range(f"I{row + 1}:J{row + 1}", line.name, normal_text)
                    sheet.merge_range(f"K{row + 1}:L{row + 1}", line.supplier_id.name, normal_text)
                    item_no += 1
                    row += 1
            if len(fruit_ids) > 0:
                for line in fruit_ids:
                    sheet.write(f"B{row + 1}", item_no, normal_text)
                    sheet.merge_range(f"C{row + 1}:D{row + 1}", line.product_id.name, normal_text)
                    sheet.write(f"E{row + 1}", line.product_qty, normal_text)
                    sheet.write(f"F{row + 1}", line.product_uom_id.name, normal_text)
                    sheet.write(f"G{row + 1}", line.price_per_unit_est, normal_text)
                    sheet.write(f"H{row + 1}", line.total_price_est, normal_text)
                    sheet.merge_range(f"I{row + 1}:J{row + 1}", line.name, normal_text)
                    sheet.merge_range(f"K{row + 1}:L{row + 1}", line.supplier_id.name, normal_text)
                    item_no += 1
                    row += 1
            if len(poultry_ids) > 0:
                for line in poultry_ids:
                    sheet.write(f"B{row + 1}", item_no, normal_text)
                    sheet.merge_range(f"C{row + 1}:D{row + 1}", line.product_id.name, normal_text)
                    sheet.write(f"E{row + 1}", line.product_qty, normal_text)
                    sheet.write(f"F{row + 1}", line.product_uom_id.name, normal_text)
                    sheet.write(f"G{row + 1}", line.price_per_unit_est, normal_text)
                    sheet.write(f"H{row + 1}", line.total_price_est, normal_text)
                    sheet.merge_range(f"I{row + 1}:J{row + 1}", line.name, normal_text)
                    sheet.merge_range(f"K{row + 1}:L{row + 1}", line.supplier_id.name, normal_text)
                    item_no += 1
                    row += 1
            if len(sea_fish_ids) > 0:
                for line in sea_fish_ids:
                    sheet.write(f"B{row + 1}", item_no, normal_text)
                    sheet.merge_range(f"C{row + 1}:D{row + 1}", line.product_id.name, normal_text)
                    sheet.write(f"E{row + 1}", line.product_qty, normal_text)
                    sheet.write(f"F{row + 1}", line.product_uom_id.name, normal_text)
                    sheet.write(f"G{row + 1}", line.price_per_unit_est, normal_text)
                    sheet.write(f"H{row + 1}", line.total_price_est, normal_text)
                    sheet.merge_range(f"I{row + 1}:J{row + 1}", line.name, normal_text)
                    sheet.merge_range(f"K{row + 1}:L{row + 1}", line.supplier_id.name, normal_text)
                    item_no += 1
                    row += 1
            if len(beef_pork_ids) > 0:
                for line in beef_pork_ids:
                    sheet.write(f"B{row + 1}", item_no, normal_text)
                    sheet.merge_range(f"C{row + 1}:D{row + 1}", line.product_id.name, normal_text)
                    sheet.write(f"E{row + 1}", line.product_qty, normal_text)
                    sheet.write(f"F{row + 1}", line.product_uom_id.name, normal_text)
                    sheet.write(f"G{row + 1}", line.price_per_unit_est, normal_text)
                    sheet.write(f"H{row + 1}", line.total_price_est, normal_text)
                    sheet.merge_range(f"I{row + 1}:J{row + 1}", line.name, normal_text)
                    sheet.merge_range(f"K{row + 1}:L{row + 1}", line.supplier_id.name, normal_text)
                    item_no += 1
                    row += 1
            if len(other_ids) > 0:
                for line in other_ids:
                    sheet.write(f"B{row + 1}", item_no, normal_text)
                    sheet.merge_range(f"C{row + 1}:D{row + 1}", line.product_id.name, normal_text)
                    sheet.write(f"E{row + 1}", line.product_qty, normal_text)
                    sheet.write(f"F{row + 1}", line.product_uom_id.name, normal_text)
                    sheet.write(f"G{row + 1}", line.price_per_unit_est, normal_text)
                    sheet.write(f"H{row + 1}", line.total_price_est, normal_text)
                    sheet.merge_range(f"I{row + 1}:J{row + 1}", line.name, normal_text)
                    sheet.merge_range(f"K{row + 1}:L{row + 1}", line.supplier_id.name, normal_text)
                    item_no += 1
                    row += 1

            sheet.merge_range(f"B{row + 1}:L{row + 1}", " ", workbook.add_format({"fg_color": "silver", "border": True}))
