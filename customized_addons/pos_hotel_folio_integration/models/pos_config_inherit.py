from odoo import fields, models


# inherit the class pos.config to add a new selection field
class PosConfig(models.Model):
    _inherit = "pos.config"

    iface_transfer_to_folio = fields.Boolean(
        string="Transfer to Folio",
        default=False,
        help="Allows to transfer orders to folio in the frontend",
    )
    # add a new selection field
    # the field is a selection field with the following options:
    # 1. 'restaurant' - transfer all lines to folio service lines and create table order
    # 2. 'activity' - transfer all lines to folio service lines and create activity
    transfer_type = fields.Selection(
        [
            ("restaurant", "Restaurant"),
            ("activity", "Activity"),
        ],
        string="Transfer Type",
        default="restaurant",
    )
