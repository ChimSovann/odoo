from odoo import _, api, fields, models


class HotelRoomGoldDay(models.Model):
    _name = 'hotel.room.gold.day'
    _description = 'Hotel Room Gold Day'

    name = fields.Char("Name", required=True)
    start_date = fields.Date("Start Date", required=True)
    end_date = fields.Date("End Date")

    @api.model
    def create(self, vals):
        return super(HotelRoomGoldDay, self).create(vals)

    def write(self, vals):
        return super(HotelRoomGoldDay, self).write(vals)
