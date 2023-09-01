from odoo import models


class PosOrder(models.AbstractModel):
    _inherit = 'pos.order'

    def reprint_receipt(self):
        return self.env.ref('pos_order_receipt.action_reprint_receipt').report_action(self)
