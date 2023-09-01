from datetime import datetime, timedelta
from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from odoo.exceptions import UserError, ValidationError, except_orm
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt


class HotelInherit(models.Model):
    _inherit = "hotel.reservation"

    booking = fields.Char(related='create_uid.name',
                          inherit=True, readonly=False)
    ref_booking = fields.Char('Ref Booking')
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Datetime.now(),
    )
    checkin = fields.Datetime(
        "Expected-Date-Arrival",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=datetime.now().strftime("%Y-%m-%d 07:00:00")
    )
    checkout = fields.Datetime(
        "Expected-Date-Departure",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=(datetime.now() + timedelta(days=1)
                 ).strftime("%Y-%m-%d 05:00:00")
    )
    check_bool = fields.Boolean("Check Existing Room", default=False)

    customer_types = fields.Many2one(
        'hotel.customer.type',
        string='Customer Type',
    )
    
    country_types = fields.Many2one(
        'hotel.country.type',
        string='Country',
    )

    city_types = fields.Many2one(
        'hotel.city.type',
        string='City',
    )


    # checking date range in order to separate date based on red/blue day
    def date_range(self, start_date, end_date):
        for n in range(int((end_date - start_date).days) + 1):
            yield start_date + timedelta(n)

    # checking room line in case there is editing on check-in or check-out date in state confirm
    # so update room line if not occupied yet else pop up message
    def check_room_line_availability(self):
        reservation_line_obj = self.env["hotel.reservation"]
        current_room_line = []
        self.check_bool = False
        for reservation in self:
            if len(reservation.reservation_line_ids) != 0 and reservation.state == "confirm" and reservation.checkin < reservation.checkout:
                # add room line of current reservation
                for reser_line in reservation.reservation_line_ids:
                    for room_id in reser_line.reserve:
                        if room_id.room_reservation_line_ids:
                            current_room_line.append(room_id.name)

                act_domain = [
                    ("checkin", ">=", self.checkin),
                    ("state", "in", ("confirm", "done")),
                ]
                res = reservation_line_obj.search(act_domain)

                for reserv in res:
                    # except self reservation
                    if self.partner_id.name != reserv.partner_id.name and self.reservation_no != reserv.reservation_no:
                        # take only reservation between check in and check out
                        if self.checkin <= reserv.checkin <= self.checkout or self.checkin <= reserv.checkout <= self.checkout:

                            for line_id in reserv.reservation_line_ids:
                                for room in line_id.reserve:
                                    if room.room_reservation_line_ids:

                                        # check if room is already exit
                                        if room.name in current_room_line:
                                            self.check_bool = reserv.check_bool = True
                                            r_checkin = reservation.checkin.date()
                                            r_checkout = reservation.checkout.date()
                                            check_intm = reserv.checkin.date()
                                            check_outtm = reserv.checkout.date()
                                            range1 = [r_checkin, r_checkout]
                                            range2 = [check_intm, check_outtm]
                                            overlap_dates = self.check_overlap(
                                                *range2
                                            ) & self.check_overlap(*range1)
                                            if reserv.check_bool:
                                                raise ValidationError(
                                                    _(
                                                        "You tried to Confirm "
                                                        "Reservation with room"
                                                        " those already "
                                                        "reserved in this "
                                                        "Reservation Period. "
                                                        "Overlap Dates are "
                                                        "%s"
                                                        "\n - Reservation no: "
                                                        "%s"
                                                        "\n - Duplicate room: "
                                                        "%s"
                                                    )
                                                    % (overlap_dates, reserv.reservation_no, room.name)
                                                )
                                        else:
                                            self.check_bool = reserv.check_bool = False
        return self.check_bool

    # update ref_booking into folio and separate room line based on Red/Blue/Gold day
    # The way of separate Red/Blue/Gold day is First store all the gold day in one list
    # Loop date range between check in and check out date
    # if date exist in gold day add to gold day else check based on day of date
    # Red day (Sunday until Thursday), Blue day (Friday and Saturday)
     
    def create_folio(self):
        hotel_folio_obj = self.env["hotel.folio"]
        folio_line_obj = self.env["folio.room.line"]
        room_reservation_line_obj = self.env['hotel.room.reservation.line']
        self.check_room_line_availability()
        if not self.check_bool:
            for reservation in self:
                folio_lines = []
                checkin_date = reservation["checkin"]
                checkout_date = reservation["checkout"]
                duration_vals = self._onchange_check_dates(
                    checkin_date=checkin_date,
                    checkout_date=checkout_date,
                    duration=False,
                )
                duration = duration_vals.get("duration") or 0.0
                folio_vals = {
                    "date_order": reservation.date_order,
                    "warehouse_id": reservation.warehouse_id.id,
                    "partner_id": reservation.partner_id.id,
                    "pricelist_id": reservation.pricelist_id.id,
                    "partner_invoice_id": reservation.partner_invoice_id.id,
                    "partner_shipping_id": reservation.partner_shipping_id.id,
                    "checkin_date": reservation.checkin,
                    "checkout_date": reservation.checkout,
                    "duration": duration,
                    "reservation_id": reservation.id,
                    "ref_booking": reservation.ref_booking,
                    "customer_types": reservation.customer_types.id,
                    "country_types": reservation.country_types.id,
                    "city_types": reservation.city_types.id,

                }

                # get gold day date
                hotel_gold_day = self.env['hotel.room.gold.day'].search([])
                ls_gold_day_date = []

                for date in hotel_gold_day:
                    if not date.end_date:
                        ls_gold_day_date.append(date.start_date.strftime('%Y-%m-%d'))

                    else:
                        for day in self.date_range(date.start_date, date.end_date):
                            ls_gold_day_date.append(day.strftime('%Y-%m-%d'))
                ###################

                # mapping date based on red day and blue day and gold day
                red_day_date = ["Friday", "Saturday"]
                blue_day_date = ["Monday", "Tuesday", "Wednesday", "Thursday", "Sunday"]
                booking_date = []
                custom_check_in_date = checkin_date
                custom_check_out_date = checkout_date
                count_day, count_len = 0, 0
                price = ""
                check = True
                total_duration = (int((checkout_date - checkin_date).days) + 1)

                for date in self.date_range(checkin_date, checkout_date):
                    count_len += 1
                    check_gold_day = date.strftime("%Y-%m-%d")

                    if check_gold_day in ls_gold_day_date:
                        count_day += 1
                        custom_check_out_date = date.strftime("%Y-%m-%d 05:00:00")
                        next_day = date + timedelta(days=1)

                        if next_day.strftime("%Y-%m-%d") not in ls_gold_day_date:
                            custom_check_out_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 05:00:00")
                            check = False
                            price = "Gold Day"
                        else:
                            if count_len == total_duration:
                                custom_check_out_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 05:00:00")
                                check = False
                                price = "Gold Day"

                        if not check:
                            booking_date.append(
                                (
                                    {
                                        "checkin_date": custom_check_in_date,
                                        "checkout_date": custom_check_out_date,
                                        "price_unit": price,
                                        "product_uom_qty": count_day,
                                    }
                                )
                            )
                            count_day = 0
                            check = True
                            custom_check_in_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 07:00:00")

                    else:
                        if date.strftime('%A') in red_day_date:
                            count_day += 1
                            custom_check_out_date = date.strftime("%Y-%m-%d 05:00:00")
                            next_day = date + timedelta(days=1)

                            if next_day.strftime('%A') in blue_day_date or next_day.strftime("%Y-%m-%d") in ls_gold_day_date:
                                custom_check_out_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 05:00:00")
                                check = False
                                price = "Red"
                            else:
                                if count_len == total_duration:
                                    custom_check_out_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 05:00:00")
                                    check = False
                                    price = "Red"

                        if date.strftime('%A') in blue_day_date:
                            count_day += 1
                            custom_check_out_date = date.strftime("%Y-%m-%d 05:00:00")
                            next_day = date + timedelta(days=1)

                            if next_day.strftime('%A') in red_day_date or next_day.strftime("%Y-%m-%d") in ls_gold_day_date:
                                custom_check_out_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 05:00:00")
                                check = False
                                price = "Blue"
                            else:
                                if count_len == total_duration:
                                    custom_check_out_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 05:00:00")
                                    check = False
                                    price = "Blue"

                        if not check:
                            booking_date.append(
                                (
                                    {
                                        "checkin_date": custom_check_in_date,
                                        "checkout_date": custom_check_out_date,
                                        "price_unit": price,
                                        "product_uom_qty": count_day,
                                    }
                                )
                            )
                            count_day = 0
                            check = True
                            custom_check_in_date = (date + timedelta(days=1)).strftime("%Y-%m-%d 07:00:00")
                #############################

                # loop reservation room line separate based on Gold, Red and Blue day
                for line in reservation.reservation_line_ids:
                    for r in line.reserve:
                        # start separate based on date here
                        for item in booking_date:
                            if item['price_unit'] == "Gold Day":
                                folio_lines.append(
                                    (
                                        0,
                                        0,
                                        {
                                            "checkin_date": item['checkin_date'],
                                            "checkout_date": item['checkout_date'],
                                            "product_id": r.product_id and r.product_id.id,
                                            "name": reservation["reservation_no"],
                                            "price_unit": r.list_gold_day_price,
                                            "product_uom_qty": item['product_uom_qty'],
                                            "is_reserved": True,
                                        },
                                    )
                                )
                                r.write({"status": "occupied", "isroom": False})

                            if item['price_unit'] == "Red":
                                folio_lines.append(
                                    (
                                        0,
                                        0,
                                        {
                                            "checkin_date": item['checkin_date'],
                                            "checkout_date": item['checkout_date'],
                                            "product_id": r.product_id and r.product_id.id,
                                            "name": reservation["reservation_no"],
                                            "price_unit": r.list_red_day_price,
                                            "product_uom_qty": item['product_uom_qty'],
                                            "is_reserved": True,
                                        },
                                    )
                                )
                                r.write({"status": "occupied", "isroom": False})

                            if item['price_unit'] == "Blue":
                                folio_lines.append(
                                    (
                                        0,
                                        0,
                                        {
                                            "checkin_date": item['checkin_date'],
                                            "checkout_date": item['checkout_date'],
                                            "product_id": r.product_id and r.product_id.id,
                                            "name": reservation["reservation_no"],
                                            "price_unit": r.list_blue_day_price,
                                            "product_uom_qty": item['product_uom_qty'],
                                            "is_reserved": True,
                                        },
                                    )
                                )
                                r.write({"status": "occupied", "isroom": False})
                ###############

                folio_vals.update({"room_line_ids": folio_lines})
                folio = hotel_folio_obj.create(folio_vals)
                for rm_line in folio.room_line_ids:
                    rm_line.product_id_change()

                # Create folio.room.line
                vals = {}
                for line_id in reservation.reservation_line_ids:
                    for room in line_id.reserve:
                        vals = {
                            "room_id": room.id,
                            "check_in": reservation.checkin,
                            "check_out": reservation.checkout,
                            "folio_id": folio.id,
                        }
                        folio_line_obj.create(vals)

                line_ids = room_reservation_line_obj.search(
                    [('reservation_id.id', '=', self.id)])
                for line in line_ids:
                    line.unlink()

                self.write({"folios_ids": [(6, 0, folio.ids)], "state": "done"})
        return True


# Hotel Reservation RoomType
class HotelReservationLineInherit(models.Model):
    _inherit = "hotel_reservation.line"

    categ_id = fields.Many2one("hotel.room.type", "Room Type",
                               domain=[('complete_name', 'ilike', 'vK Services / Accommodation /')])


class ServiceLine(models.Model):
    _inherit = 'hotel.service.line'
    line_payment = fields.Selection([('cash', 'Cash'),
                                     ('credit_card', 'Credit Card'),
                                     ('cityledger', 'City Ledger'),
                                     ('foc', 'FOC')],
                                    'Payment Method', default='cityledger')


class FolioLine(models.Model):
    _inherit = 'hotel.folio.line'
    line_payment = fields.Selection([('cash', 'Cash'),
                                     ('credit_card', 'Credit Card'),
                                     ('cityledger', 'City Ledger'),
                                     ('foc', 'FOC')],
                                    'Payment Method', default='cityledger')

    # add condition when create from reservation auto generate price based on Red/Blue Day
    @api.onchange("product_id")
    def product_id_change(self):
        """
 -        @param self: object pointer
 -        """

        if not self.product_id:
            return {"domain": {"product_uom": []}}
        vals = {}
        domain = {
            "product_uom": [
                ("category_id", "=", self.product_id.uom_id.category_id.id)
            ]
        }
        if not self.product_uom or (
                self.product_id.uom_id.id != self.product_uom.id
        ):
            vals["product_uom"] = self.product_id.uom_id
        product = self.product_id.with_context(
            lang=self.folio_id.partner_id.lang,
            partner=self.folio_id.partner_id.id,
            quantity=vals.get("product_uom_qty") or self.product_uom_qty,
            date=self.folio_id.date_order,
            pricelist=self.folio_id.pricelist_id.id,
            uom=self.product_uom.id,
        )

        result = {"domain": domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != "no-message":
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning["title"] = title
            warning["message"] = message
            result = {"warning": warning}
            if product.sale_line_warn == "block":
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += "\n" + product.description_sale
        vals["name"] = name

        self._compute_tax_id()

        # if create from reservation price is based on red/blue day price
        if not self.folio_id.reservation_id.id:
            if self.folio_id.pricelist_id and self.folio_id.partner_id:
                vals["price_unit"] = self.env["account.tax"]._fix_tax_included_price_company(
                    self._get_display_price(product),
                    product.taxes_id,
                    self.tax_id,
                    self.company_id,
                )

        self.update(vals)
        return result


# Hotel Reservation Summary
class RoomReservationSummary(models.Model):
    _inherit = 'room.reservation.summary'

    date_from = fields.Datetime(
        "Date From", default=lambda self: fields.Date.today().strftime("%Y-%m-%d 16:00:00")
    )
    date_to = fields.Datetime(
        "Date To",
        default=lambda self: (
                fields.Date.today() + relativedelta(days=30)).strftime("%Y-%m-%d 16:00:00"),
    )
    room_type_summary = fields.Many2one('product.category', string="Room type",
                                        domain=[('complete_name', 'ilike', 'vK Services / Accommodation /')])

    @api.onchange(
        "date_from", "date_to"
    )  # noqa C901 (function is too complex)
    def get_room_summary(self):
        """
        @param self: object pointer
        """
        res = {}
        all_detail = []
        room_obj = self.env["hotel.room"]
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        folio_room_line_obj = self.env["folio.room.line"]
        date_range_list = []
        main_header = []
        summary_header_list = ["Rooms"]
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise UserError(
                    _("Checkout date should be greater than Checkin date.")
                )
            d_frm_obj = (datetime.strptime(str(self.date_from), dt))
            d_to_obj = (datetime.strptime(str(self.date_to), dt))
            temp_date = d_frm_obj
            while temp_date <= d_to_obj:
                val = ""
                val = (str(temp_date.strftime("%a")) + ' ' +
                       str(temp_date.strftime("%b")) + ' ' +
                       str(temp_date.strftime("%d")))
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime(dt))
                temp_date = temp_date + timedelta(days=1)
            all_detail.append(summary_header_list)

            # For Sorting By Room Type
            if not self.room_type_summary.id:
                room_ids = room_obj.search(
                    [('categ_id', 'not in', [10, 883]), ('name', 'not like', '%Camping')])
            else:
                room_ids = room_obj.search(
                    [('room_categ_id.name', 'ilike', self.room_type_summary.name)])

            all_room_detail = []
            for room in room_ids:
                room_detail = {}
                room_list_stats = []
                room_detail.update({"name": room.name or ""})
                if (
                        not room.room_reservation_line_ids
                        and not room.room_line_ids
                ):
                    for chk_date in date_range_list:
                        room_list_stats.append(
                            {
                                "state": "Free",
                                "date": chk_date,
                                "room_id": room.id,
                            }
                        )
                else:
                    for chk_date in date_range_list:
                        reserline_ids = room.room_reservation_line_ids.ids
                        reservline_ids = reservation_line_obj.search(
                            [
                                ("id", "in", reserline_ids),
                                ("check_in", "<=", chk_date),
                                ("check_out", ">=", chk_date),
                                ("state", "!=", "unassigned"),
                            ]
                        )
                        fol_room_line_ids = room.room_line_ids.ids
                        chk_state = ["draft", "cancel"]
                        folio_resrv_ids = folio_room_line_obj.search(
                            [
                                ("id", "in", fol_room_line_ids),
                                ("check_in", "<=", chk_date),
                                ("check_out", ">=", chk_date),
                            ]
                        )

                        if reservline_ids or folio_resrv_ids:
                            name = ""
                            room_name = ""
                            check_in = ""
                            check_out = ""
                            reservation = []

                            try:
                                if reserline_ids:
                                    name = reservline_ids.reservation_id.partner_id.name
                                if folio_resrv_ids:
                                    name = folio_resrv_ids.folio_id.partner_id.name
                            except Exception as e:
                                arr = []
                                id = ""
                                for i in e.value:
                                    if i.isdigit():
                                        id = id + i
                                    if i == ',':
                                        arr.append(int(id))
                                        id = ""
                                if int(id) not in arr and int(id) != "":
                                    arr.append(int(id))
                                if "hotel.room.reservation.line" in e.value:
                                    obj = folio_room_line_obj.browse(arr)
                                    for line in obj:
                                        check_in = parse(line.check_in).date()
                                        check_out = parse(
                                            line.check_out).date()
                                        room_name = line.room_id.name
                                        reservation.append(
                                            line.reservation_id.reservation_no)
                                raise except_orm(_('Error'), _(
                                    'There is duplicated reservations \n Room: %s \n Check In: %s \n Check Out: %s \n Reservation: %s , %s' % (
                                        room_name, str(check_in), str(check_out), reservation[0], reservation[1])))

                            room_list_stats.append(
                                {
                                    "state": reservline_ids.reservation_id.partner_id.name or folio_resrv_ids.folio_id.partner_id.name,
                                    "date": chk_date,
                                    "room_id": room.id,
                                    "is_draft": "No",
                                    "data_model": "",
                                    "data_id": 0,
                                }
                            )
                        else:
                            room_list_stats.append(
                                {
                                    "state": "Free",
                                    "date": chk_date,
                                    "room_id": room.id,
                                }
                            )

                room_detail.update({"value": room_list_stats})
                all_room_detail.append(room_detail)
            main_header.append({"header": summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res


# Add field Red/Blue day price for hotel room
class ProductTemplateHotel(models.Model):
    _inherit = "product.template"

    # user defined
    list_red_day_price = fields.Float(
        'Red Day Price', default=1.0,
        digits='Product Price',
        help="Price at which the product is sold to customers on Red Day.")
    list_blue_day_price = fields.Float(
        'Blue Day Price', default=1.0,
        digits='Product Price',
        help="Price at which the product is sold to customers on Blue Day.")
    list_gold_day_price = fields.Float(
        'Gold Day Price', default=1.0,
        digits='Product Price',
        help="Price at which the product is sold to customers on Gold Day.")
