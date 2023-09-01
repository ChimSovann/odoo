import xlsxwriter
from odoo import api, models


class MarketListSingleReportXlsx(models.AbstractModel):
    _name = "report.market_list_odoo13.report_mkl_request_xlsx_single"
    _inherit = "report.odoo_report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, current_record):
        for obj in current_record:
            report_name = obj.name
            requester = obj.requested_by.name
            analytic_acc = obj.analytic_account_id.name
            purchase_for_day1 = obj.purchase_for_date_day1
            purchase_for_day2 = obj.purchase_for_date_day2
            date_request = obj.creation_date
            date_approve = obj.approve_date

            sheet = workbook.add_worksheet(report_name[:30])

            # Style
            header = workbook.add_format(
                {"align": "center", "valign": "vcenter", "font_size": 24, "bold": True, "fg_color": "silver"})
            sub_title = workbook.add_format(
                {"bold": True, "align": "left", "text_wrap": True, "border": True, "fg_color": "silver"})
            normal_text = workbook.add_format({"align": "left", "text_wrap": True, "border": True})
            centered_text = workbook.add_format({"align": "center", "text_wrap": True, "border": True})
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

            ###################################### DAY 1 ##########################################
            item_no = 1
            row = 8

            breakfast_day1_ids = obj.line_ids_day1_breakfast
            lunch_day1_ids = obj.line_ids_day1_lunch
            dinner_day1_ids = obj.line_ids_day1_dinner
            dry_store_day1_ids = obj.dry_store_line_day1

            breakfast_day2_ids = obj.line_ids_day2_breakfast
            lunch_day2_ids = obj.line_ids_day2_lunch
            dinner_day2_ids = obj.line_ids_day2_dinner
            dry_store_day2_ids = obj.dry_store_line_day2

            exp_grand_total = obj.grand_total_est_day1 + obj.grand_total_est_day2
            budget_pax = obj.budget_per_pax_day1 + obj.budget_per_pax_day2
            breakfast_pax = obj.breakfast_est_day1 + obj.breakfast_est_day2
            lunch_pax = obj.lunch_est_day1 + obj.lunch_est_day2
            dinner_pax = obj.dinner_est_day1 + obj.dinner_est_day2
            total_pax = breakfast_pax + dinner_pax + dinner_pax

            # Header
            sheet.merge_range("B1:L4", "Market List Request", header)

            # Title
            sheet.merge_range("B5:C5", "Request Reference", bold)
            sheet.merge_range("B6:C6", "Analytic Account", bold)
            sheet.merge_range("B7:C7", "Purchase For Date", bold)

            ### values ###
            sheet.merge_range("D5:G5", requester, normal_text)
            sheet.merge_range("D6:G6", analytic_acc, normal_text)
            sheet.merge_range("D7:E7", purchase_for_day1, date_format)
            sheet.write("F7", "&", centered_text)
            sheet.merge_range("G7:H7", purchase_for_day2, date_format)

            sheet.merge_range("H5:I5", "Request Date", bold)
            sheet.merge_range("H6:I6", "Approve Date", bold)
            sheet.merge_range("I7:L7", " ", normal_text)

            ### values ###
            sheet.merge_range("J5:L5", date_request, date_format)
            sheet.merge_range("J6:L6", date_approve, date_format)

            # Body
            # Subtitle
            sheet.write("B8", "No.", sub_title)
            sheet.merge_range("C8:D8", "Product", sub_title)
            sheet.write("E8", "Qty", sub_title)
            sheet.write("F8", "Unit", sub_title)
            sheet.write("G8", "Est. Price", sub_title)
            sheet.write("H8", "Est. Sub Total Price", sub_title)
            sheet.merge_range("I8:J8", "Description", sub_title)
            sheet.merge_range("K8:L8", "Supplier Name", sub_title)

            if len(breakfast_day1_ids) > 0:
                for line in breakfast_day1_ids:
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
            if len(lunch_day1_ids) > 0:
                for line in lunch_day1_ids:
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
            if len(dinner_day1_ids) > 0:
                for line in dinner_day1_ids:
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
            if len(dry_store_day1_ids) > 0:
                for line in dry_store_day1_ids:
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
            ###################################### DAY 2 ##########################################

            if len(breakfast_day2_ids) > 0:
                for line in breakfast_day2_ids:
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
            if len(lunch_day2_ids) > 0:
                for line in lunch_day2_ids:
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
            if len(dinner_day2_ids) > 0:
                for line in dinner_day2_ids:
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
            if len(dry_store_day2_ids) > 0:
                for line in dry_store_day2_ids:
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

            # Footer
            # Tally
            sheet.merge_range(f"B{row + 1}:J{row + 1}", "Expected Grand Total (USD):", footer_tally)
            sheet.merge_range(f"K{row + 1}:L{row + 1}", exp_grand_total, monetary_usd)
            row += 1

            sheet.merge_range(f"B{row + 1}:J{row + 1}", "Budget/Pax (USD):", footer_tally)
            sheet.merge_range(f"K{row + 1}:L{row + 1}", budget_pax, monetary_usd)
            row += 1

            # Pax
            sheet.merge_range(f"B{row + 1}:C{row + 1}", "1. Breakfast Exp.:", normal_text)
            sheet.write(f"D{row + 1}", breakfast_pax, normal_text)
            sheet.write(f"E{row + 1}", "Pax", normal_text)
            row += 1

            sheet.merge_range(f"B{row + 1}:C{row + 1}", "2. Lunch Exp.:", normal_text)
            sheet.write(f"D{row + 1}", lunch_pax, normal_text)
            sheet.write(f"E{row + 1}", "Pax", normal_text)
            row += 1

            sheet.merge_range(f"B{row + 1}:C{row + 1}", "3. Dinner Exp.:", normal_text)
            sheet.write(f"D{row + 1}", dinner_pax, normal_text)
            sheet.write(f"E{row + 1}", "Pax", normal_text)
            row += 1

            sheet.merge_range(f"B{row + 1}:C{row + 1}", "Total:", bold)
            sheet.write(f"D{row + 1}", total_pax, normal_text)
            sheet.write(f"E{row + 1}", "Pax", normal_text)
            row += 1
