# Copyright 2019 Elico Corp, Dominique K. <dominique.k@elico-corp.com.sg>
# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default["order_line"] = [
            (0, 0, line.copy_data()[0])
            for line in self.order_line.filtered(lambda l: not l.is_deposit)
        ]
        return super(PurchaseOrder, self).copy_data(default)


class PurchaseOrderLineDeposit(models.Model):
    _inherit = "purchase.order.line"

    is_deposit = fields.Boolean(
        string="Is a deposit payment",
        help="Deposit payments are made when creating invoices from a purhcase"
        " order. They are not copied when duplicating a purchase order.",
    )

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLineDeposit, self)._prepare_account_move_line(move)
        print(self.is_deposit, ' -------------------------------------')
        if self.is_deposit:
            res["quantity"] = -1 * self.qty_invoiced
            print('============================================================')
        print(self.is_deposit, '++++++++++++++++++++++++++++++++++++++')
        return res
