from odoo import _, models, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools import datetime
import datetime


class PurchaseOrderInheritCustom(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    new_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        track_visibility="onchange",
        required=True,
        states=READONLY_STATES,

    )

# add new analytic account inside RFQ form and put it onchange the acc line
    @api.onchange('new_analytic_account_id')
    def _onchange_analytic_account_id(self):
        for order in self:
            analytic_id = order.new_analytic_account_id
            for line in order.order_line:
                line.update(
                    {
                        "account_analytic_id": analytic_id,
                    }
                )


class PurchaseOrderAnalyticLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        readonly=True,
    )




