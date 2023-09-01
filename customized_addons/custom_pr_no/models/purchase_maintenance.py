from odoo import _, models, fields, api
from odoo.exceptions import UserError
from odoo.tools import datetime


# Duplicate Internal Reference
class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True)

    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (copy)") % self.name
            default['default_code'] = self.default_code
            print(default)
        return super(ProductTemplateInherit, self).copy(default=default)


class PurchaseRequestCustomInherit(models.Model):
    _inherit = 'purchase.request'

    assigned_to = fields.Many2one(
        comodel_name="res.users",
        string="Approver",
        track_visibility="onchange",
        domain=lambda self: [
            (
                "groups_id",
                "in",
                self.env.ref("purchase_request.group_purchase_request_manager").id,
            )
        ],
        index=True,
        required=True
    )

    description = fields.Text(string="Description", required=True)


class PurchaseRequestLineCustomInherit(models.Model):
    _inherit = "purchase.request.line"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        track_visibility="onchange",
        store=True,

    )
