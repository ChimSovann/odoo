import json
import logging
from collections import defaultdict
import datetime

import pytz
import requests
import xml.etree.cElementTree as ET

import xmltodict
import yaml
from dateutil.parser import parse

from odoo import models, fields, api, _
from odoo import tools as tl
from odoo.exceptions import except_orm, ValidationError

_logger = logging.getLogger(__name__)

# HLS Credentials
cli_commands = tl.config.options
channel_manager_username = cli_commands.get("channel_manager_username")
channel_manager_password = cli_commands.get("channel_manager_password")
hotel_id = cli_commands.get("hotel_id")
hotel_authentication_channel_key = cli_commands.get("hotel_authentication_channel_key")


class HotelGetBookingHls(models.Model):
    _name = "hotel.get.booking.hls"
    _description = "Model for handle bookings data from HLS"

    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.context_today,
                             help="Start Date for request to GetBookings from HLS")
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.context_today,
                           help="End Date for request to GetBookings from HLS")
    booking_id = fields.Char(string='HLS Reference')
    type = fields.Selection(selection=[('LastModifiedDate', 'Last Modified Date'),
                                       ('BookingDate', 'Booking Date'),
                                       ('CheckIn', 'Check In'),
                                       ('CheckOut', 'Check Out')],
                            string='Date Filter',
                            required=True,
                            default='LastModifiedDate', help="Type for request to GetBookings from HLS")
    reservation_lines = fields.One2many('hotel.reservation', 'hls_config_id', string="Reservation",
                                        help="Reservation Lines that have created")
    response = fields.Text(string="Response", help="Response get from GetBookings from HLS")
    reservation_error = fields.Text(string="Reservation Not Created",
                                    help="List of HLS BookingIds those haven't created")

    # function to auto checkin reservation everyday
    def _auto_checking_reservation(self):
        company_id = self.env['res.company'].search([('name', '=', 'A2A Town (Cambodia) Co., Ltd.')]).id
        self = self.with_context(allowed_company_ids=[company_id])
        reservation_obj = self.env['hotel.reservation']
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        for reservation in reservation_obj.search([('state', '=', 'confirm'), ('booking_id', 'not ilike', 'PM%')]):
            if reservation.booking_id and today == reservation.checkin.strftime('%Y-%m-%d') \
                    and reservation.state == "confirm":
                reservation.force_create_folio()

    # function to create reservations those haven't created
    def create_missed_reservation(self):
        # check whether if there is missing reservation or not
        if not self.reservation_error:
            return False
        # get booking data from HLS by calling get_booking_hls_request function
        data = self.get_booking_hls_request()

        # initialize validation_errors
        validation_errors = ""
        for hls_id in self.reservation_error.split("\n"):
            if hls_id:
                # create missing reservation by calling create_reservation function
                result = self.create_reservation(data, hls_id)

                # Check if result's type is list mean there are some validation errors
                if type(result) == list:
                    validation_errors += "Reservation " + result[0] + " cannot be created! " + result[1] + "\n"

        # if there are some validations errors, we show validation error on a Wizard
        # NOTE: we use wizard to show validations error message to prevent from cutting off create reservation process
        # of other reservation that haven't had any validation error
        if validation_errors:
            message_id = self.env['message.wizard'].create({'message': _(validation_errors)})
            return {
                'name': _('Something went wrong !'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }

    # function for getting bookings from HLS by request to GetBookings method
    # which is return a list of bookings based on some filter criteria.
    def get_booking_hls_request(self, start_date=None, end_date=None):
        reservation_obj = self.env['hotel.reservation']
        for record in self:
            record.response = ""
            record.reservation_error = ""
        get_booking = """
                        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://hbe-api.whl-staging.com/services/booking/soap">
                        <soapenv:Header/>
                        <soapenv:Body>
                        <soap:GetBookings>
                        <Request>
                        <StartDate></StartDate>
                        <EndDate></EndDate>
                        <DateFilter>LastModifiedDate</DateFilter>
                        <BookingStatus></BookingStatus>
                        <BookingId></BookingId>
                        <ExtBookingRef></ExtBookingRef>
                        <NumberBookings></NumberBookings>
                        <Credential>
                        <ChannelManagerUsername>{}</ChannelManagerUsername>
                        <ChannelManagerPassword>{}</ChannelManagerPassword>
                        <HotelId>{}</HotelId>
                        <HotelAuthenticationChannelKey>{}</HotelAuthenticationChannelKey>
                        </Credential>
                        <Language>en</Language>
                        </Request>
                        </soap:GetBookings>
                        </soapenv:Body>
                        </soapenv:Envelope>
                    """.format(channel_manager_username, channel_manager_password, hotel_id,
                               hotel_authentication_channel_key)

        body_req = ET.fromstring(get_booking)
        for DateFilter in body_req.iter('DateFilter'):
            if self.type:
                DateFilter.text = self.type
        if (not type(start_date) == str) and self.booking_id:
            for BookingId in body_req.iter('BookingId'):
                BookingId.text = self.booking_id
        else:
            for statDate in body_req.iter('StartDate'):
                statDate.text = start_date if type(start_date) == str else str(self.date_start)
            for endDate in body_req.iter('EndDate'):
                endDate.text = end_date if type(end_date) == str else str(self.date_end)

        xml_str = ET.tostring(body_req, encoding='utf8', method='xml')
        headers = {"Content-Type": "application/xml"}
        # initial hls_booking to handle booking data
        hls_booking = {}

        try:
            response = requests.post("http://hbe-api.whl-staging.com/services/booking/soap", data=xml_str,
                                     headers=headers)
            # Convert response.content to dictionary
            booking_hls = yaml.safe_load(json.dumps(xmltodict.parse(response.content)))

            # Check whether if there is any Booking Transaction or not
            if booking_hls['SOAP-ENV:Envelope']['SOAP-ENV:Body']['ns1:GetBookingsResponse']['GetBookingsResult'][
                'Bookings'] is None:
                _logger.info("No Booking Transaction")
                self.response = "No Booking Transaction"

            else:
                booking_resp = booking_hls['SOAP-ENV:Envelope']['SOAP-ENV:Body']['ns1:GetBookingsResponse'][
                    'GetBookingsResult']['Bookings']['ns1:Booking']
                # check whether if booking_resp is dict type
                # if it is dict type mean there is only one booking transaction, so we need to convert it to a list
                # to get the same list type when there are more than one booking transaction
                if type(booking_resp) == dict:
                    booking_resp = [booking_resp]
                for booking in booking_resp:
                    booking_id = booking['BookingId']
                    booking.pop('BookingId', None)
                    hls_booking.update({booking_id: booking})
                for record in self:
                    record.response = " \n\n ".join(str(hls) + " :\n" + str(hls_booking[hls]) for hls in hls_booking)
                    for hls_id in hls_booking:
                        hotel_reservation_id = reservation_obj.search([('booking_id', '=', hls_id)])

                        if hotel_reservation_id:
                            hotel_reservation_id.hls_config_id = record
                        # if not created we add to reservation that haven't created list which is reservation_error field
                        else:
                            record.reservation_error = str(hls_id) + "\n" + record.reservation_error
            print(hls_booking)
            return hls_booking

        except requests.exceptions.ConnectionError as e:
            _logger.info(e)

    # function for getting booking from HLS, then update exist reservation and create new reservation
    # this function run when Get Booking HLS crone job calling it 2 minutes once
    def _get_hls_booking(self):
        now = datetime.datetime.now()
        # get current date base on timezone
        tz = pytz.timezone("Asia/Phnom_Penh")
        date_today = pytz.utc.localize(now).astimezone(tz)
        date_tmr = date_today + datetime.timedelta(days=1)
        start_date = date_today.strftime("%Y-%m-%d")
        end_date = date_tmr.strftime("%Y-%m-%d")
        # get booking data from HLS by calling get_booking_hls_request function
        hls_booking = self.get_booking_hls_request(start_date, end_date)

        # check whether there is any booking data or not
        if not hls_booking:
            return False

        for hls_id in hls_booking:
            if "PM" not in hls_id:
                booking_status = ""
                if hls_booking[hls_id]['BookingStatus'] == "Confirmed":
                    booking_status = "confirm"
                elif hls_booking[hls_id]['BookingStatus'] == "Operational":
                    booking_status = "done"
                elif hls_booking[hls_id]['BookingStatus'] == "Cancelled":
                    booking_status = "cancel"
                elif hls_booking[hls_id]['BookingStatus'] == "Completed":
                    _logger.info("HLS COMPLETED")
                    continue

                hotel_reservation_id = self.env['hotel.reservation'].search([('booking_id', '=', hls_id)])
                # check whether if hls_id have created reservation or not
                # if created we update that reservation by calling update_reservation function
                if hotel_reservation_id:
                    self.update_reservation(booking_status, hotel_reservation_id, hls_booking, hls_id)

                    # Delete empty room lines
                    for line in hotel_reservation_id.reservation_line_ids:
                        for reservation_line in line:
                            if not reservation_line.reserve:
                                reservation_line.unlink()
                # if not created we create new reservation by calling create_reservation function
                else:
                    self.create_reservation(hls_booking, hls_id)

        # Call read_notification to inform HLS so that they won’t resend them to you for next call if there is no change
        # self.read_notification(hls_booking)

        return True

    # This function run after reading bookings successfully from HLS system by using GetBookings, we need to call this
    # function to inform HLS so that we won’t resend them to you for next call if there is no change.
    @staticmethod
    def read_notification(hls_booking):
        read_notification = """
                                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://hbe-api.whl-staging.com/services/booking/soap">
                                <soapenv:Header/>
                                <soapenv:Body>
                                <soap:ReadNotification>
                                <Request>
                                <Bookings>
                                </Bookings>
                                <Credential>
                                <ChannelManagerUsername>{}</ChannelManagerUsername>
                                <ChannelManagerPassword>{}</ChannelManagerPassword>
                                <HotelId>{}</HotelId>{}7fd41009bbaa5c0464720b07f531d721</HotelAuthenticationChannelKey>
                                </Credential>
                                <Language>en</Language>
                                </Request>
                                </soap:ReadNotification>
                                </soapenv:Body>
                                </soapenv:Envelope>
                            """.format(channel_manager_username, channel_manager_password, hotel_id,
                                       hotel_authentication_channel_key)

        element_notification = ET.fromstring(read_notification)
        for hls_id in hls_booking:
            if "PM" not in hls_id:
                for request in element_notification.iter('Request'):
                    for data in request:
                        if data.tag == "Bookings":
                            item_element = ET.fromstring("<item></item>")
                            data.append(item_element)
                            for item in data:
                                if item.text is None:
                                    item.text = hls_id
                            break
        notification_str = ET.tostring(element_notification)

        headers = {"Content-Type": "application/xml"}
        try:
            requests.post("http://hbe-api.whl-staging.com/services/booking/soap", data=notification_str,
                          headers=headers)

        except requests.exceptions.ConnectionError as e:
            _logger.info(e)

    # function for update exist reservation if there is any change for update from HLS Booking
    def update_reservation(self, booking_status, hotel_reservation_id, hls_booking, hls_id):
        hotel_room_obj = self.env['hotel.room']
        room_reservation_line_obj = self.env['hotel.room.reservation.line']
        hotel_reservation_line_obj = self.env['hotel_reservation.line']

        if hotel_reservation_id.state != booking_status:
            # if booking_status is cancel we call cancel_reservation_ota function to cancel that reservation
            if booking_status == "cancel":
                hotel_reservation_id.cancel_reservation_ota()
            # if booking_status is done we call force_create_folio function to create reservation
            elif booking_status == "done":
                hotel_reservation_id.force_create_folio()
        else:
            # if booking_status is confirm first we need to update guest data and then update reservation
            if booking_status == "confirm":
                firstname = hls_booking[hls_id]['Guests']['FirstName']
                lastname = hls_booking[hls_id]['Guests']['LastName']
                guest_name = firstname + " " + lastname
                guest = {
                    'name': guest_name,
                    'firstname': firstname,
                    'lastname': lastname,
                    'email': hls_booking[hls_id]['Guests']['Email'],
                    'phone': hls_booking[hls_id]['Guests']['Phone'],
                    'city': hls_booking[hls_id]['Guests']['City'],
                    'zip': hls_booking[hls_id]['Guests']['PostalCode'],
                }
                hotel_reservation_id.partner_id.write(guest)

                hls_checkin = parse(hls_booking[hls_id]["CheckIn"] + "T07:00:00")
                hls_checkout = parse(hls_booking[hls_id]["CheckOut"] + "T05:00:00")

                # Define needed data
                room_type_ids = []
                hls_room_id = []
                delete_room_id = []
                add_room_type_id = []

                # find room_type_ids and checked_room
                for reservation_line in hotel_reservation_id.reservation_line_ids:
                    for room in reservation_line.reserve:
                        room_type_ids.append(room.room_type_id)

                # find hls_room_id
                booking_items = hls_booking[hls_id]["Rooms"]["ns1:BookingItem"]
                # if there is only one booking item, we need to convert it into list
                # to get the same type when there are booking items
                if type(booking_items) == dict:
                    booking_items = [booking_items]
                for booking_item in booking_items:
                    if booking_item["BookingItemStatus"] != "Cancelled":
                        hls_room_id.append(booking_item["RoomId"])

                # find delete_room_id and add_room_line_id
                for reservation_line in hotel_reservation_id.reservation_line_ids:
                    for room in reservation_line.reserve:
                        room_type_id = room.room_type_id

                        # count room_type_id in room_type_ids and hls_room_id
                        room_type_id_count = room_type_ids.count(room_type_id)
                        hls_room_id_count = hls_room_id.count(room_type_id)

                        # calculate the range to get number of delete or add id
                        rang = room_type_id_count - hls_room_id_count

                        # if the rang > 0 mean there are some delete room id
                        # find delete_room_id
                        if rang > 0:
                            delete_room_id.append(room.id)
                            room_type_ids.remove(room_type_id)
                        # if the rang < 0 mean there are some add room type id
                        # find add_room_line_id
                        elif rang < 0:
                            add_room_type_id.append(room_type_id)
                            room_type_ids.append(room_type_id)

                # find new added room_type_ids
                new_room_type_ids = [room_type_id for room_type_id in hls_room_id if
                                     room_type_id not in room_type_ids]

                add_room_type_id.extend(new_room_type_ids)

                # delete room line based on delete_room_id
                # delete room line in hotel.room.reservation.line
                room_reservation_line_ids = room_reservation_line_obj.search(
                    [('reservation_id.id', '=', hotel_reservation_id.id)])

                for line in room_reservation_line_ids:
                    if line.room_id.id in delete_room_id:
                        line.unlink()

                # delete room line in hotel_reservation.line
                hotel_reservation_line_ids = hotel_reservation_line_obj.search(
                    [('line_id', '=', hotel_reservation_id.id)])
                for line_type in hotel_reservation_line_ids:
                    # we use raw query because we want to delete line many2many relationship
                    for room in line_type.reserve:
                        if room.id in delete_room_id:
                            reservation_line_id = line_type.id
                            room_id = room.id
                            self._cr.execute(
                                "delete from hotel_reservation_line_room_rel where (hotel_reservation_line_id=%s and room_id=%s)",
                                (reservation_line_id, room_id))

                # add room line based on add_room_line_id
                for room_type_id in add_room_type_id:
                    room_ids = hotel_room_obj.search([('room_type_id', '=', room_type_id)])
                    # check whether if room is available or not
                    for room in room_ids:
                        available = 1
                        for line in room.room_reservation_line_ids:
                            line_checkin = line.check_in
                            line_checkout = line.check_out
                            if line.status != "cancel":
                                if (
                                        line_checkin <= hls_checkin <= line_checkout) or (
                                        line_checkin <= hls_checkout <= line_checkout) or (
                                        hls_checkin < line_checkin and hls_checkout > line_checkout):
                                    available = 0
                                    break
                        for line in room.room_line_ids:
                            line_checkin = line.check_in
                            line_checkout = line.check_out
                            if line.status != "cancel":
                                if (
                                        line_checkin <= hls_checkin <= line_checkout) or (
                                        line_checkin <= hls_checkout <= line_checkout) or (
                                        hls_checkin < line_checkin and hls_checkout > line_checkout):
                                    available = 0
                                    break

                        # if room is available we add that room_line
                        if available == 1:
                            # add room line to hotel_reservation.line
                            vals = {
                                'line_id': hotel_reservation_id.id,
                                'categ_id': room.room_categ_id.id,
                                'name': False,
                                'reserve': [[6, False, [room.id]]]
                            }
                            hotel_reservation_line_obj.create(vals)

                            # add room line to hotel.room.reservation.line
                            vals = {
                                'room_id': room.id,
                                'reservation_id': hotel_reservation_id.id,
                                'check_in': hotel_reservation_id.checkin,
                                'check_out': hotel_reservation_id.checkout,
                                'state': 'assigned',
                            }
                            room.write({'isroom': False, 'status': 'occupied'})
                            room_reservation_line_obj.create(vals)
                            break
        return True

    # function for create new reservation if there is any booking from HLS Booking
    def create_reservation(self, hls_booking, hls_id):
        hotel_room_obj = self.env['hotel.room']
        hotel_room_type_obj = self.env['hotel.room.type']
        product_categ_obj = self.env['product.category']
        partner_obj = self.env['res.partner']
        hotel_room_reservation_line_obj = self.env['hotel.room.reservation.line']
        hotel_reservation_obj = self.env['hotel.reservation']

        booking_data = hls_booking[hls_id]
        # check whether if BookingStatus is Cancelled or not
        # if error we return a list of hls_id and validation message
        if booking_data['BookingStatus'] == "Cancelled":
            return [hls_id, "Booking Canceled."]
        else:
            date_ordered = parse(booking_data['BookingDate'])
            check_in = booking_data['CheckIn'] + "T07:00:00"
            check_out = booking_data['CheckOut'] + "T05:00:00"

            # get guest information
            firstname = hls_booking[hls_id]['Guests']['FirstName']
            lastname = hls_booking[hls_id]['Guests']['LastName']
            guest_name = firstname + " " + lastname
            guest = {
                'name': guest_name,
                'firstname': firstname,
                'lastname': lastname,
                'email': hls_booking[hls_id]['Guests']['Email'],
                'phone': hls_booking[hls_id]['Guests']['Phone'],
                'city': hls_booking[hls_id]['Guests']['City'],
                'zip': hls_booking[hls_id]['Guests']['PostalCode'],
                'customer_rank': 1,
            }

            # find room_type_ids_dict
            room_type_ids_dict = defaultdict(list)
            booking_items = hls_booking[hls_id]["Rooms"]["ns1:BookingItem"]
            # if there is only one booking item, we need to convert it into list
            # to get the same type when there are booking items
            if type(booking_items) == dict:
                booking_items = [booking_items]
            for booking_item in booking_items:
                room_type_id = product_categ_obj.search([('room_type_id', '=', booking_item["RoomId"])]).id
                room_type_ids_dict[room_type_id].append(room_type_id)

            hls_checkin = parse(check_in)
            hls_checkout = parse(check_out)
            reservation_line = []

            for room_type_id in room_type_ids_dict:
                room_ids = []
                hotel_room_ids = hotel_room_obj.search([('categ_id', '=', room_type_id)])
                number_hls_room = len(room_type_ids_dict[room_type_id])
                hotel_room_type_id = hotel_room_type_obj.search([('product_categ_id', '=', room_type_id)]).id

                # initial number_available_room
                number_available_room = 0

                # check whether if room is available or not
                for room in hotel_room_ids:
                    available = 1
                    for line in room.room_reservation_line_ids:
                        line_checkin = line.check_in
                        line_checkout = line.check_out
                        if line.status != "cancel":
                            if (
                                    line_checkin <= hls_checkin <= line_checkout) or (
                                    line_checkin <= hls_checkout <= line_checkout) or (
                                    hls_checkin < line_checkin and hls_checkout > line_checkout):
                                available = 0
                                break
                    for line in room.room_line_ids:
                        line_checkin = line.check_in
                        line_checkout = line.check_out
                        if line.status != "cancel":
                            if (
                                    line_checkin <= hls_checkin <= line_checkout) or (
                                    line_checkin <= hls_checkout <= line_checkout) or (
                                    hls_checkin < line_checkin and hls_checkout > line_checkout):
                                available = 0
                                break

                    # if room is available we add it to room_ids and increase  number_available_room value
                    if available == 1:
                        if number_available_room < number_hls_room:
                            room_ids.append(room.id)
                            number_available_room += 1
                        else:
                            break

                reservation_line.append(
                    [0, False, {'categ_id': hotel_room_type_id, 'name': False, 'reserve': [[6, False, room_ids]]}])

            # Define partner
            partner = self.env['res.partner']
            # check whether if guest data has email or not
            if guest['email']:
                partner = partner_obj.search([('email', '=', guest['email'])])

            # find partner_id
            # if partner data with that email exist
            # we take exist partner id
            if partner.id:
                partner_id = partner.id
            # if not we create a new partner record
            else:
                property_account_receivable_id = self.env['account.account'].search([('code', '=', '130001')])
                property_account_payable_id = self.env['account.account'].search([('code', '=', '200001')])
                guest['property_account_receivable_id'] = property_account_receivable_id
                guest['property_account_payable_id'] = property_account_payable_id
                partner_id = partner_obj.create(guest).id

            # validation data before create Reservation
            # validate the reservation_line_ids
            for rec in reservation_line:
                reserve = rec[2]["reserve"][0][2]
                if not reserve:
                    return [hls_id, "Rooms do not Available For Reservation."]

            # validate check_in_out_dates
            """
            When date_order is less then check-in date or
            Checkout date should be greater than the check-in date.
            """
            if hls_checkin and hls_checkin:
                if hls_checkout < hls_checkin:
                    return [hls_id, """Check-out date should be greater """
                                    """than Check-in date."""]

            vals = {'date_order': date_ordered, 'checkin': hls_checkin, 'checkout': hls_checkout,
                    'warehouse_id': self.env['stock.warehouse'].browse([1]).id, 'booking_id': hls_id,
                    'partner_id': partner_id, 'partner_shipping_id': partner_id, 'partner_order_id': partner_id,
                    'partner_invoice_id': partner_id, 'pricelist_id': 1, 'reservation_line_ids': reservation_line,
                    }

            reservation_id = hotel_reservation_obj.create(vals)
            if reservation_id and reservation_id.reservation_no == "New":
                company_id = self.env['res.company'].search([('name', '=', 'A2A Town (Cambodia) Co., Ltd.')]).id
                reservation_id.write({"reservation_no": self.env["ir.sequence"].with_context(force_company=company_id)
                                     .next_by_code("hotel.reservation") or "New"})

            self._cr.execute("select count(*) from hotel_reservation as hr "
                             "inner join hotel_reservation_line as hrl on \
                             hrl.line_id = hr.id "
                             "inner join hotel_reservation_line_room_rel as \
                             hrlrr on hrlrr.room_id = hrl.id "
                             "where (checkin,checkout) overlaps \
                             ( timestamp %s, timestamp %s ) "
                             "and hr.id <> cast(%s as integer) "
                             "and hr.state = 'confirm' "
                             "and hrlrr.hotel_reservation_line_id in ("
                             "select hrlrr.hotel_reservation_line_id \
                             from hotel_reservation as hr "
                             "inner join hotel_reservation_line as \
                             hrl on hrl.line_id = hr.id "
                             "inner join hotel_reservation_line_room_rel \
                             as hrlrr on hrlrr.room_id = hrl.id "
                             "where hr.id = cast(%s as integer) )",
                             (reservation_id.checkin, reservation_id.checkout,
                              str(reservation_id.id), str(reservation_id.id)))
            res = self._cr.fetchone()

            room_count = res and res[0] or 0.0
            if room_count:
                raise except_orm(_('Warning'), _('You tried to confirm \
                                                reservation with room those already reserved in this \
                                                reservation period'))
            else:
                reservation_id.write({'state': 'confirm'})
                for line_id in reservation_id.reservation_line_ids:
                    line_id = line_id.reserve
                    for room_id in line_id:
                        vals = {
                            'room_id': room_id.id,
                            'reservation_id': reservation_id.id,
                            'check_in': reservation_id.checkin,
                            'check_out': reservation_id.checkout,
                            'state': 'assigned',
                        }
                        hotel_room_reservation_line_obj.create(vals)
                vals.clear()
            return True


class SaveBooking(models.Model):
    _inherit = 'hotel.reservation'
    _description = "Inherit Hotel Reservation Model to add some new field and override some methods"

    reservation_line_ids = fields.One2many(
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
    )
    memo = fields.Text(string='Memo')
    booking_id = fields.Char(string='HLS Reference', help="Booking Id from HLS")
    hls_config_id = fields.Many2one('hotel.get.booking.hls', string="HLS Config Search")
    BookingFromOTA = fields.Boolean(string='Booking From OTA')

    # override check_reservation_rooms to make some change on default validation
    @api.constrains("reservation_line_ids", "adults", "children")
    def check_reservation_rooms(self):
        """
        This method is used to validate the reservation_line_ids.
        """
        for reservation in self:
            if not reservation.reservation_line_ids:
                raise ValidationError(
                    _("Please Select Rooms For Reservation.")
                )
            for rec in reservation.reservation_line_ids:
                if not rec.reserve:
                    raise ValidationError(
                        _("Please Select Rooms For Reservation.")
                    )

    # override check_in_out_dates function to delete some default validation of check_in and check_out
    @api.constrains("checkin", "checkout")
    def check_in_out_dates(self):
        """
        Checkout date should be greater than the check-in date.
        """
        if self.checkout and self.checkin:
            if self.checkout < self.checkin:
                raise ValidationError(
                    _(
                        """Check-out date should be greater """
                        """than Check-in date."""
                    )
                )

    # function for cancel reservation for ota
    def cancel_reservation_ota(self):
        super(SaveBooking, self).cancel_reservation()
        self.write({'BookingFromOTA': True})

    # function for create folio from button in hotel.get.booking.hls model
    # This function use in case a particular reservation didn't auto check in # Use the below line in view
    def force_create_folio(self):
        hotel_folio_obj = self.env["hotel.folio"]
        folio_line_obj = self.env["folio.room.line"]
        room_reservation_line_obj = self.env['hotel.room.reservation.line']
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
            }
            for line in reservation.reservation_line_ids:
                for r in line.reserve:
                    folio_lines.append(
                        (
                            0,
                            0,
                            {
                                "checkin_date": checkin_date,
                                "checkout_date": checkout_date,
                                "product_id": r.product_id and r.product_id.id,
                                "name": reservation["reservation_no"],
                                "price_unit": r.list_price,
                                "product_uom_qty": duration,
                                "is_reserved": True,
                            },
                        )
                    )
                    r.write({"status": "occupied", "isroom": False})
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
            self.write({"BookingFromOTA": True, "folios_ids": [(6, 0, folio.ids)], "state": "done"})
        return True

    # function add new, update or cancel bookings from hotel specified in Credential request
    def define_notify_booking(self):
        notify_booking = """
                            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://hbe-api.whl-staging.com/services/booking/soap"  xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
                            <soapenv:Header/>
                            <soapenv:Body>
                            <soap:NotifyBookings>
                            <Request>
                            <Bookings>
                                <Booking>
                                <NotificationType>New</NotificationType>
                                <BookingId></BookingId>
                                <ExtBookingRef>test-ext-ref</ExtBookingRef>
                                <Currency>USD</Currency>
                                <CheckIn></CheckIn>
                                <CheckOut></CheckOut>
                                <AdditionalComments></AdditionalComments>
                                <GuestDetail>
                                <Title>Mr</Title>
                                <FirstName></FirstName>
                                <LastName></LastName>
                                <Email></Email>
                                <Phone></Phone>
                                <Address></Address>
                                <City></City>
                                <State></State>
                                <Country></Country>
                                <PostalCode></PostalCode>
                                </GuestDetail>
                                <Rooms>
                                </Rooms>
                                <ServiceCharge></ServiceCharge>
                                <ServiceChargeArrival></ServiceChargeArrival>
                                </Booking>
                            </Bookings>
                            <Credential>
                            <ChannelManagerUsername>{}</ChannelManagerUsername>
                            <ChannelManagerPassword>{}</ChannelManagerPassword>
                            <HotelId>{}</HotelId>
                            <HotelAuthenticationChannelKey>{}</HotelAuthenticationChannelKey>
                            </Credential>
                            <Language>en</Language>
                            </Request>
                            </soap:NotifyBookings>
                            </soapenv:Body>
                            </soapenv:Envelope>
                        """.format(channel_manager_username, channel_manager_password, hotel_id,
                                   hotel_authentication_channel_key)

        xmlstr = ET.fromstring(notify_booking)

        price_list_items = self.pricelist_id.item_ids
        reservation_line = self.reservation_line_ids
        hotel_room_obj = self.env['hotel.room']
        sale_price = []
        array_room_id = []

        checkin = self.checkin
        checkout = self.checkout
        duration = checkout - checkin + datetime.timedelta(days=1)

        # find sale_price and array_room_id of reservation_line
        for lines in reservation_line:
            for room in lines.reserve:
                array_room_id.append(room.id)
                for items_id in price_list_items:
                    if items_id.categ_id == room.categ_id:
                        sale_price.append((1 + items_id.price_discount) * room.list_price + items_id.price_surcharge)
                        break
                else:
                    sale_price.append(room.list_price)

        booking_item_xml = """
                            <BookingItem>
                                <RatePlanId></RatePlanId>
                                <Adults></Adults>
                                <Children></Children>
                                <ExtraAdults></ExtraAdults>
                                <ExtraChildren></ExtraChildren>
                                <TaxFee></TaxFee>
                                <TaxFeeArrival></TaxFeeArrival>
                                <Discount></Discount>
                                <Deposit></Deposit>
                                <Amount></Amount>
                            </BookingItem>
                            """

        for booking in xmlstr.iter('Booking'):
            for booking_tag in booking:
                if booking_tag.tag == "Rooms":
                    for _ in range(len(array_room_id)):
                        element_tree = ET.fromstring(booking_item_xml)
                        booking_tag.append(element_tree)
                    break

        for booking in xmlstr.iter('Booking'):
            for booking_tag in booking:
                if booking_tag.tag == "CheckIn":
                    booking_tag.text = str(checkin).split()[0]
                elif booking_tag.tag == "CheckOut":
                    booking_tag.text = str(checkout).split()[0]
                elif booking_tag.tag == "GuestDetail":
                    for guest_info in booking_tag:
                        if guest_info.tag == "FirstName":
                            guest_info.text = self.partner_id.name if self.partner_id.company_type == "company" else self.partner_id.firstname
                        elif guest_info.tag == "LastName":
                            guest_info.text = " " if self.partner_id.company_type == "company" else self.partner_id.lastname or " "
                        elif guest_info.tag == "Email":
                            guest_info.text = self.partner_id.email or "N/A"
                        elif guest_info.tag == "Phone":
                            guest_info.text = self.partner_id.phone

                elif booking_tag.tag == "Rooms":
                    i = 0
                    for booking_item in booking_tag:
                        for room_info in booking_item:
                            rate_plan_id = ""
                            if room_info.tag == "Amount":
                                amount_str = str(sale_price[i] * 1.1 * duration.days)
                                room_info.text = amount_str
                            elif room_info.tag == "RatePlanId":
                                category = hotel_room_obj.browse([array_room_id[i]]).categ_id
                                for rate_plan_line in category.rate_plan_line:
                                    rate_plan_id = rate_plan_line.rate_plan_id
                                room_info.text = rate_plan_id
                            elif room_info.tag == "TaxFee":
                                vat_tax_included = sale_price[i] * 0.1
                                room_info.text = str(vat_tax_included * duration.days)
                        i = i + 1

        body_req = ET.tostring(xmlstr, encoding='utf8', method='xml')

        return body_req

    # function use for add new or update existing inventory, rate and related info of a particular hotel
    def define_inventory_form(self, delete_room_ids):
        hotel_room_obj = self.env['hotel.room']

        save_inventory = """
                            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://hbe-api.whl-staging.com/services/inventory/soap">
                            <soapenv:Header/>
                            <soapenv:Body>
                            <soap:SaveInventory>
                            <Request>
                            <Inventories>
                            </Inventories>
                            <Credential>
                            <ChannelManagerUsername>{}</ChannelManagerUsername>
                            <ChannelManagerPassword>{}</ChannelManagerPassword>
                            <HotelId>{}</HotelId>
                            <HotelAuthenticationChannelKey>{}</HotelAuthenticationChannelKey>
                            </Credential>
                            <Language>en</Language>
                            </Request>
                            </soap:SaveInventory>
                            </soapenv:Body>
                            </soapenv:Envelope>
                         """.format(channel_manager_username, channel_manager_password, hotel_id,
                                    hotel_authentication_channel_key)
        element_save_inventory = ET.fromstring(save_inventory)
        inventory = """
                    <Inventory>
                        <RoomId></RoomId>
                        <Availabilities>
                        </Availabilities>
                    </Inventory>
                    """
        room_qty = """
                    <Availability>
                        <DateRange>
                            <From></From>
                            <To></To>
                        </DateRange>
                        <Quantity></Quantity>
                        <Action>Set</Action>
                    </Availability>
                    """

        room_list = []
        availability = dict()

        # add room_type_id of deleted room to room_list
        for room_id in delete_room_ids:
            room = hotel_room_obj.browse([room_id])
            if room.room_type_id in room_list:
                continue
            else:
                room_list.append(room.room_type_id)

        # add room_type_id of reservation lines to room_list
        for lines in self.reservation_line_ids:
            for room in lines.reserve:
                if room.room_type_id in room_list:
                    continue
                else:
                    room_list.append(room.room_type_id)

        # loop through room_dict to check availability of each room_type_id
        for room_type in room_list:
            reservation_obj = self.env['hotel.reservation']
            check_in = self.checkin
            check_out = self.checkout
            date_qty = dict()
            while True:
                date_qty.update({check_in: 0})
                total_no_available_room = 0
                no_room_booking_from_ota = 0

                # Check all the availability of each room type
                room_ids = hotel_room_obj.search([('room_type_id', '=', room_type)])
                for room in room_ids:
                    available = 1
                    for line in room.room_reservation_line_ids:
                        line_check_in = line.check_in
                        line_check_out = line.check_out
                        if line.status != "cancel":
                            if line_check_in <= check_in <= line_check_out:
                                available = 0
                                break
                    for line in room.room_line_ids:
                        line_check_in = line.check_in
                        line_check_out = line.check_out
                        if line.status != "cancel":
                            if line_check_in <= check_in <= line_check_out:
                                available = 0
                                break
                    if available == 1:
                        total_no_available_room += 1

                # Check the reservation from online booking within checkin date
                reservation_from_ota = reservation_obj.search([('state', '=', 'confirm'),
                                                               ('booking_id', 'not ilike', 'PM%'),
                                                               ('checkin', '<=', check_in),
                                                               ('checkout', '>', check_in)])
                for reservation in reservation_from_ota:
                    for lines in reservation.reservation_line_ids:
                        for room in lines.reserve:
                            if room.room_type_id == room_type:
                                no_room_booking_from_ota += 1

                date_qty[check_in] = [total_no_available_room, no_room_booking_from_ota]

                check_in = check_in + datetime.timedelta(days=1)
                if check_in.date() == check_out.date():
                    break
            availability.update({room_type: date_qty})

        print(availability)

        # update availability based on room_id from HLS
        for room_id in availability:
            # Set available room that allow user booking from online (hls) by category
            # manually based on application user requirement
            no_available_room_hls = 0
            if room_id in ["97e01ea1-6bd9-1580952774-4d69-b5c3-5de52c0e5366", "d1b23adb-af10-1525920153-42f8-aa36-149313dd49d2",
                           "ce21b8da-45b1-1559116840-4d44-81b5-89990c2c826b"]:
                no_available_room_hls = 15
            elif room_id in ["91e8533d-6901-4984-bd96-c146b0beff67", "6781f3c9-93d2-1502181553-4450-9cae-41f26162d513",
                             "6ea0fe92-e3f0-464c-bf4a-03c799cd475c", "5a1f2a55-a2ce-1518606066-4b30-aecd-5d313914e2eb",
                             "8ceca99d-f593-400e-af47-ae56ba56aff6", "52292b22-259f-4257-ba1d-2f901502481c",
                             "a5190207-c2a4-47a0-af40-a1c027beeee7"]:
                no_available_room_hls = 2
            elif room_id in ["bd697e6c-912f-4a72-af73-c3a754da8677"]:
                no_available_room_hls = 3
            elif room_id in ["526ff61f-05a5-1516952564-44ec-b76d-49d4a16fb3a1"]:
                no_available_room_hls = 4
            elif room_id in ["2a224d81-c2a5-4b7a-91ab-d04a0e5a68b3"]:
                no_available_room_hls = 60
            elif room_id in ["07eeb2e2-4c62-1640154150-4efb-b50c-6c64fcf475ef"]:
                no_available_room_hls = 1
            elif room_id in ["9ce49877-f934-409f-9711-0a2806c89de4"]:
                no_available_room_hls = 20

            inventory_element = ET.fromstring(inventory)
            for room_id_tage in inventory_element.iter('RoomId'):
                room_id_tage.text = room_id
            for availabilities_tage in inventory_element.iter('Availabilities'):
                for date in availability[room_id]:
                    element = ET.fromstring(room_qty)
                    for fromm_tage in element.iter('From'):
                        fromm_tage.text = str(date).split()[0]
                    for to_tage in element.iter('To'):
                        to_tage.text = str(date).split()[0]
                    for quantity_tage in element.iter('Quantity'):
                        no_room_hls = no_available_room_hls - availability[room_id][date][1]
                        current_available_room_hls = no_room_hls if no_room_hls >= 0 else 0
                        total_no_available_room = availability[room_id][date][0]
                        # update inventory for online booking to the total_no_available_room if total_no_available_room
                        # less than current_available_room_hls
                        quantity_tage.text = str(min(current_available_room_hls, total_no_available_room))

                    availabilities_tage.append(element)

            for inventories_tage in element_save_inventory.iter('Inventories'):
                inventories_tage.append(inventory_element)

        inventory_body = ET.tostring(element_save_inventory, encoding='utf8', method='xml')
        print(inventory_body)
        return inventory_body

    # override confirm_reservation function to add new bookings from hotel to HLS if Guest available on HLs and
    # update existing inventory
    def confirm_reservation(self):
        create_booking = super(SaveBooking, self).confirm_reservation()

        headers = {"Content-Type": "application/xml"}
        notify_booking_request_body = self.define_notify_booking()
        try:
            notify_booking_response = requests.post("http://hbe-api.whl-staging.com/services/booking/soap",
                                                    data=notify_booking_request_body, headers=headers)
            booking_hls = yaml.safe_load(json.dumps(xmltodict.parse(notify_booking_response.content)))
            booking_resp = \
                booking_hls['SOAP-ENV:Envelope']['SOAP-ENV:Body']['ns1:NotifyBookingsResponse']['NotifyBookingsResult'][
                    'Bookings']['ns1:BookingResponse']
            is_success = booking_resp['Success'] if type(booking_resp) == dict else booking_resp[0]['Success']
            if is_success == "true":
                super(SaveBooking, self).write({'booking_id': booking_resp[0]['BookingId']})

                inventory_body = self.define_inventory_form(delete_room_ids=[])
                requests.post("http://hbe-api.whl-staging.com/services/inventory/soap",
                                                        data=inventory_body, headers=headers)
            return create_booking

        except requests.exceptions.ConnectionError:
            raise except_orm(_('Warning'), _('You tried to confirm reservation with no internet connection'))

    # override write function to add some condition related to HLS on default function
    def write(self, vals):
        headers = {"Content-Type": "application/xml"}
        write_con = ["BO", "AG", "MO", "OT", "BW"]

        booking_id_checking = "BookingFromOTA"
        # used for cases confirm or cancel booking from OTA
        if "BookingFromOTA" in vals or vals.get('state') == 'cancel':
            if "BookingFromOTA" in vals:
                del vals["BookingFromOTA"]
            res = super(SaveBooking, self).write(vals)
            return res

        if self.booking_id:
            booking_id_checking = self.booking_id[:2]
            if self.state == "draft":
                booking_id_checking = "BookingFromOTA"

        if (self.state == 'cancel') or (booking_id_checking in write_con):
            if list(vals.keys()) != ['hls_config_id']:
                raise except_orm(_('Warning'), _("You can't update this reservation!!!"))

        if self.state in ['confirm']:
            new_room_ids = []
            pre_room_ids = []
            add_ids = []
            delete_ids = []
            room_reservation_line_obj = self.env['hotel.room.reservation.line']

            # find pre_room_ids before update reservation
            for lines in self.reservation_line_ids:
                for room in lines.reserve:
                    pre_room_ids.append(room.id)

            res = super(SaveBooking, self).write(vals)

            # find new_room_ids, add_ids & delete_ids after update reservation
            if vals.get('reservation_line_ids'):
                for line in self.reservation_line_ids:
                    for room in line.reserve:
                        new_room_ids.append(room.id)
                for new_room_id in new_room_ids:
                    if new_room_id not in pre_room_ids:
                        add_ids.append(new_room_id)
                for pre_room_id in pre_room_ids:
                    if pre_room_id not in new_room_ids:
                        delete_ids.append(pre_room_id)
                line_ids = room_reservation_line_obj.search(
                    [('reservation_id.id', '=', self.id)])
                for line in line_ids:
                    if line.room_id.id in delete_ids:
                        line.unlink()

                for room in add_ids:
                    vals = {
                        'room_id': room,
                        'reservation_id': self.id,
                        'check_in': self.checkin,
                        'check_out': self.checkout,
                        'state': 'assigned',
                    }
                    room_reservation_line_obj.create(vals)

                #  update bookings from hotel to HLS
                notify_booking = self.define_notify_booking()
                notify_booking_request_body = ET.fromstring(notify_booking)
                for BookingId in notify_booking_request_body.iter('BookingId'):
                    BookingId.text = self.booking_id
                for NotificationType in notify_booking_request_body.iter('NotificationType'):
                    NotificationType.text = "Update"
                write_data = ET.tostring(notify_booking_request_body, encoding='utf8', method='xml')
                try:
                    requests.post("http://hbe-api.whl-staging.com/services/booking/soap",
                                  data=write_data, headers=headers)

                except requests.exceptions.ConnectionError:
                    raise except_orm(_('No Internet Connection'), _('Please Try again later'))

                # update existing inventory
                inventory_body = self.define_inventory_form(delete_room_ids=delete_ids)

                try:
                    requests.post("http://hbe-api.whl-staging.com/services/inventory/soap",
                                  data=inventory_body, headers=headers)

                except requests.exceptions.ConnectionError:
                    raise except_orm(_('No Internet Connection'), _('Please Try again later'))

            else:
                return res
        else:
            res = super(SaveBooking, self).write(vals)
            return res

    def cancel_reservation(self):
        cancel_con = ["BO", "AG", "MO", "OT"]
        headers = {"Content-Type": "application/xml"}
        if self.booking_id:
            if self.booking_id[:2] in cancel_con:
                raise except_orm(_('Warning'), _('You can not cancel Reservations which from OTA'))
            res = super(SaveBooking, self).cancel_reservation()
            cancel_booking_str = """
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://hbe-api.whl-staging.com/services/booking/soap">
                    <soapenv:Header/>
                    <soapenv:Body>
                    <soap:NotifyBookings>
                    <Request>
                    <Bookings>
                        <Booking>
                        <NotificationType>Cancel</NotificationType>
                        <BookingId></BookingId>
                        </Booking>
                    </Bookings>
                    <Credential>
                    <ChannelManagerUsername>{}</ChannelManagerUsername>
                    <ChannelManagerPassword>{}</ChannelManagerPassword>
                    <HotelId>{}</HotelId>
                    <HotelAuthenticationChannelKey>{}</HotelAuthenticationChannelKey>
                    </Credential>
                    <Language>en</Language>
                    <Language>en</Language>
                    </Request>
                    </soap:NotifyBookings>
                    </soapenv:Body>
                    </soapenv:Envelope>
                """.format(channel_manager_username, channel_manager_password, hotel_id,
                           hotel_authentication_channel_key)

            cancel_element = ET.fromstring(cancel_booking_str)
            for Id in cancel_element.iter('BookingId'):
                Id.text = self.booking_id
            body_req = ET.tostring(cancel_element, encoding='utf8', method='xml')
            try:
                response = requests.post("http://hbe-api.whl-staging.com/services/booking/soap",
                                         data=body_req, headers=headers)
                inventory_body = self.define_inventory_form(delete_room_ids=[])
                response = requests.post("http://hbe-api.whl-staging.com/services/inventory/soap",
                                         data=inventory_body, headers=headers)
            except requests.exceptions.ConnectionError:
                raise except_orm(_('Warning'), _('You tried to cancel reservation with No internet connection'))
            return res
        else:
            res = super(SaveBooking, self).cancel_reservation()
            return res


class HotelRoomType(models.Model):
    _inherit = 'product.category'
    _description = "Inherit product.category model to some customize fields"

    rate_plan_line = fields.One2many('room_type.rate_plan', 'hotel_room_type_id', string='Lines')
    room_type_id = fields.Char(string='Room Type ID')


class RatePlant(models.Model):
    _name = 'room_type.rate_plan'
    _description = "To store rate plan data of room from HLS"

    name = fields.Char('Name', select=True, required=True)
    rate_plan_id = fields.Char(string='Id', required=True)
    hotel_room_type_id = fields.Many2one('product.category', string='Product Category')


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    room_type_id = fields.Char(string='Type ID', related='categ_id.room_type_id')
