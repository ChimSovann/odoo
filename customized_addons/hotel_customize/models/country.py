from odoo import _, api, fields, models


class CountryType(models.Model):
    _name = "hotel.country.type"

    name = fields.Char(required=True, string='Name')
    country_types = fields.Many2one('hotel.country.type', string='Country')
