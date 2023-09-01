from odoo import _, api, fields, models


class CityType(models.Model):
    _name = "hotel.city.type"

    name = fields.Char(required=True, string='Name')
    city_types = fields.Many2one('hotel.city.type', string='City')
