import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import logging
_logger = logging.getLogger(__name__)

# Authorization of SmartLock API
api_token = "c93838ad-0080-4eee-b051-674e83b68298"
headers = {
    "Authorization": "Bearer {}".format(api_token)
}


# Inherit hotel_folio to send qr code via email or phone number in each line
class HotelApi(models.Model):
    _inherit = 'hotel.folio'

    hide_button = fields.Boolean(default=True)

    # This function is to call the SmartLock API of send QR code to emails or phone numbers
    def send_qr(self):
        items = []
        for rec in self:
            for room_rec in rec.room_line_ids:
                data = dict()
                prod = room_rec.product_id.name.split('-')
                # TODO: This is will only work for pipe rooms as of the implementation
                if 'Pipe' in prod[0] and room_rec.qr_status != 'sent':
                    prod = str(prod[0]).split(' ')[-1]
                    if not room_rec.customer_email:
                        if not room_rec.customer_phone_number:
                            raise ValidationError(_("Please input email or phone number of each line before Send QR!"))
                        validate_number = "+855" + room_rec.customer_phone_number[1:]
                        data["phoneNumber"] = validate_number
                    else:
                        data["email"] = room_rec.customer_email
                    data["startedAt"] = room_rec.checkin_date.astimezone(datetime.timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S%z")
                    data["endedAt"] = room_rec.checkout_date.astimezone(datetime.timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S%z")
                    data["room"] = prod

                    room_rec.qr_status = 'sent'
                    self.hide_button = False
                    items.append(data)

        body = {
            "items": items
        }

        try:
            requests.post("http://192.168.0.40:3000/api/bookings", json=body, verify=False, headers=headers)
            # notification after send qr
            msg = "Already Sent QR Code! Please Check Email or Phone Number."

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': msg,
                    'type': 'success',
                    'sticky': False
                }
            }
        except requests.exceptions.ConnectionError as e:
            _logger.info(e)
            print(e, 'error')

        return self


# Inherit hotel_room to perform Lock and Unlock room from the front desk team
class HotelAdminUrgent(models.Model):
    _inherit = "hotel.room"

    is_lock = fields.Boolean(default=False)
    is_lock_all = fields.Boolean(default=False)

    def action_lock_room(self):
        for rec in self:
            room_no = rec.name
            room_no = room_no.replace(' ', '-')

        req = requests.patch("http://192.168.0.40:3000/api/room/lock/" + room_no, headers=headers)

        if req.status_code == 200:
            self.is_lock = True
        return req

    def action_unlock_room(self):
        for rec in self:
            room_no = rec.name
            room_no = room_no.replace(' ', '-')

        req = requests.patch("http://192.168.0.40:3000/api/room/unlock/" + room_no, headers=headers)

        if req.status_code == 200:
            self.is_lock = False

        return req


class HotelFolioLineInherit(models.Model):
    _inherit = "hotel.folio.line"

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        res = super(HotelFolioLineInherit, self).create(vals)
        if "folio_id" in vals:
            folio = self.env["hotel.folio"].browse(vals["folio_id"])
            res["customer_email"] = folio.partner_id.email
            res["customer_phone_number"] = folio.partner_id.phone

        return res

    # This function is to prevent user delete line without cancel the qr code of the room
    def unlink(self):
        for line in self:
            if line.qr_status == 'sent':
                raise ValidationError(_("Please CANCEL the QR Code before delete this room line!"))

        return super(HotelFolioLineInherit, self).unlink()

    def cancel_qr(self):
        for line in self:
            rooms = self.env["hotel.room"].search(
                [("product_id", "=", line.order_line_id.product_id.id)]
            )

            body = {
                "startedAt": str(line.checkin_date),
                "endedAt": str(line.checkout_date),
                "room": rooms.name
            }

            try:
                requests.post("http://192.168.0.40:3000/api/room/checkOut", json=body, verify=False, headers=headers)
                line.qr_status = 'draft'
            except requests.exceptions.ConnectionError as e:
                _logger.info(e)
                print(e, 'error')

        return self

    customer_email = fields.Char(string="Email")
    customer_phone_number = fields.Char(string="Phone")
    qr_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent')
    ], string="QR_Status", default='draft', readonly=True)


class SmartLockModel(models.Model):
    _name = "smartlock"
    _description = "Smart Lock API Integration"

    is_lock_all = fields.Boolean(default=False)

    rooms = fields.Many2many(
        "hotel.room",
        "room_id",
        domain="[('isroom','=',True),\
                                       ('room_categ_id','=',categ_id)]",
    )
    categ_id = fields.Many2one("hotel.room.type", "Room Type")
    product_categ_id = fields.Many2one(
        "product.category", "Product Category", delegate=True
    )

    @api.model
    def create(self, vals):
        if "categ_id" in vals:
            room_categ = self.env["hotel.room.type"].browse(
                vals.get("categ_id")
            )
            vals.update({"parent_id": room_categ.product_categ_id.id})
        return super(SmartLockModel, self).create(vals)

    def action_lock_all_rooms(self):
        req = requests.patch("http://192.168.0.40:3000/api/room/lockAll", headers=headers)

        if req.status_code == 200:
            self.is_lock_all = True
            for rec in self:
                for room_name in rec.rooms:
                    room_name.is_lock = True

        return req

    def action_unlock_all_rooms(self):
        req = requests.patch("http://192.168.0.40:3000/api/room/unlockAll", headers=headers)

        if req.status_code == 200:
            self.is_lock_all = False
            for rec in self:
                for room_name in rec.rooms:
                    room_name.is_lock = False

        return req
