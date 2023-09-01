from odoo import _, models, fields, api
from odoo.exceptions import UserError
import datetime
from werkzeug.routing import ValidationError



class PurchaseRequestLineUoM(models.Model):
    _inherit = 'purchase.request.line'

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        domain=[("purchase_ok", "=", True)],
        track_visibility="onchange",
    )
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Product Unit of Measure",
        track_visibility="onchange",
        domain="[('category_id', '=', product_uom_category_id)]",
    )


class PurchaseRequestInheritCustom(models.Model):
    _inherit = "purchase.request"


    @api.model
    def _default_route(self):
        obj = self.env["stock.location.route"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        route_default = obj.search(
            [("isRouteActive", "=", True), ("company_id", "=", company_id),
             '&', ("name", "like", "Transfer"), ("name", "!=", "Transfer to A2A")])
        return route_default

    READONLY_STATES = {
        'approved': [('readonly', True)],
        'done': [('readonly', True)],
        'rejected': [('readonly', True)],
    }
    new_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        track_visibility="onchange",
        required=True,
    )

    route_request_ids = fields.Many2many(
        'stock.location.route', 'stock_route_purchase_request_rel', 'request_id', 'route_id', 'Routes',
        domain=[('purchase_request_quot_selectable', '=', True)],
        required=True,
        store=True,
        default=_default_route,
    )
    approval_date = fields.Datetime('Approved Date', readonly=True)


    @api.onchange('new_analytic_account_id')
    def _onchange_analytic_account_id(self):
        for request in self:
            analytic_id = request.new_analytic_account_id
            for line in request.line_ids:
                line.update(
                    {
                        "analytic_account_id": analytic_id,
                    }
                )

#onchange when request approval
    def button_to_approve(self):
        self._onchange_analytic_account_id()
        self.to_approve_allowed_check()
        return self.write({"state": "to_approve"})

# # add approval date
    def button_approved(self):
        return self.write({"state": "approved", 'approval_date': fields.Datetime.now()})


#to check request and request line for double rfq creation
class PreventDuplicateRFQ(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    @api.model
    def _check_valid_request_line(self, request_line_ids):
        picking_type = False
        company_id = False
        for line in self.env["purchase.request.line"].browse(request_line_ids):
            if line.purchase_state is not False:
                raise UserError(_("The request has already create RFQ once."))
            if line.request_id.state == "done":
                raise UserError(_("The purchase has already been completed."))
            if line.request_id.state != "approved":
                raise UserError(
                    _("Purchase Request %s is not approved") % line.request_id.name
                )

            if line.purchase_state == "done":
                raise UserError(_("The purchase has already been completed."))

            line_company_id = line.company_id and line.company_id.id or False
            if company_id is not False and line_company_id != company_id:
                raise UserError(_("You have to select lines from the same company."))
            else:
                company_id = line_company_id

            line_picking_type = line.request_id.picking_type_id or False
            if not line_picking_type:
                raise UserError(_("You have to enter a Picking Type."))
            if picking_type is not False and line_picking_type != picking_type:
                raise UserError(
                    _("You have to select lines from the same Picking Type.")
                )
            else:
                picking_type = line_picking_type


class RouteCustomizedRequest(models.Model):
    _inherit = 'stock.location.route'

    purchase_request_quot_selectable = fields.Boolean(
        'Applicable on PR',
        default=True,
        help="When checked, the route will be selectable in the Purchase for Quotation form.")

    purchase_request_ids = fields.Many2many(
        'purchase.request', 'stock_route_purchase_request_rel', 'route_id', 'request_id',
        'Purchase For Quotation', copy=False, check_company=True)