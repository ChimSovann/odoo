from odoo import models


class A2ASaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False):
        res = super(A2ASaleOrder, self)._create_invoices(grouped, final)
        if self._context.get("active_model") == "hotel.folio":
            for move in res:
                for line in move.invoice_line_ids:
                    line.account_id = line.product_id.categ_id.fb_account or line.account_id
        return res
