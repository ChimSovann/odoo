from odoo import _, api, fields, models


class CustomerType(models.Model):
    _name = "hotel.customer.type"

    name = fields.Char(required=True, string='Name')
