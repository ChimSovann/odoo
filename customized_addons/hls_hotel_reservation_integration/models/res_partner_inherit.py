from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = "Inherit res.partner model to add two more fields first_name and last_name"

    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")

