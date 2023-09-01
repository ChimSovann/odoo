# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.exceptions import UserError
from odoo.tools import datetime
from odoo.tools.float_utils import float_compare, float_round


# to set picking type as phnom penh: receipt by default in purchase request
class PurchaseRequestInherit(models.Model):
    _inherit = "purchase.request"

    @api.model
    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id),
             ("warehouse_id", "like", "%Phnom")]
        )

        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"),
                 ("warehouse_id", "=", False)]
            )
        return types[:1]

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        required=True,
        default=_default_picking_type,
    )


class PurchaseInherit(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id),
             ("warehouse_id", "like", "%Phnom")])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'),
                 ('warehouse_id', '=', False)])

        return picking_type[:1]

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',
                                      required=True, default=_default_picking_type,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment")


# Inheriting Purchase Order model to implement fields
class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    reference_id = fields.Char(string="ID", readonly=True, required=True, copy=False, default='New')
    approver = fields.Many2one(comodel_name="res.users", string="Approver", required=True,
                               tracking=True,
                               track_visibility="onchange",
                               index=True,
                               states=READONLY_STATES,
                               )
    requester = fields.Many2one(
        comodel_name="res.users",
        string="Requester",
        copy=False,
        track_visibility="onchange",
        index=True,
        states=READONLY_STATES
    )
    quotation = fields.Many2one(
        comodel_name="res.users",
        string="Find Quotation By",
        copy=False,
        track_visibility="onchange",
        index=True,
        states=READONLY_STATES
    )

    # on create method
    @api.model
    def create(self, vals):
        # po = self.env['purchase.order'].search([], order='id asc')
        # for ref in po:
        #     if ref.reference_id != 'New':
        #         ref.update({'reference_id': 'New'})
        #         # ref.update({'reference_id': self.env['ir.sequence'].next_by_code(
        #         # 'reference.id')})
        if vals.get('reference_id', 'New') == 'New':
            vals['reference_id'] = self.env['ir.sequence'].next_by_code(
                'reference.id') or 'New'
        result = super(PurchaseOrderInherit, self).create(vals)
        return result


# Inheriting Purchase Order line to implement Discount fields
class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount %')

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

#to update discount value in draft bill (account.move, when create bill)
    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLineInherit, self)._prepare_account_move_line(move)
        res["discount"] = self.discount
        return res


class CustomPrNo(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    request_no = fields.Char(string='Request No.', readonly=True)
    note = fields.Text(string='Note', required=True, states=READONLY_STATES,)


class PurchaseRequestNo(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    # Changing domain of Supplier ID in create RFQ inside Purchase Request
    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        domain=[("supplier_rank", ">=", 1)],
        context={"res_partner_search_mode": "supplier", "default_is_company": True},
    )

    @api.model
    def _prepare_purchase_order(self, description, route_request_ids, request_id, picking_type, group_id, company, origin, request, assigned_to, new_analytic_account_id):
        data = super(PurchaseRequestNo, self)._prepare_purchase_order(picking_type, group_id, company, origin)
        data.update({
            "new_analytic_account_id": new_analytic_account_id.id,   # adding the analytic_account_id in Purchase Order
            "note": description,   # adding the description in Purchase Order
            "route_ids": route_request_ids,
            "request_no": request_id.name,  # adding the PR number in Purchase Order
            "requester": request.id,
            "approver": assigned_to.id,

        })
        return data

    def make_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]
        pr_line_obj = self.env["purchase.request.line"]
        purchase = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise UserError(_("Enter a positive quantity."))
            if self.purchase_order_id:
                # (new_request_no) when creating rfq references with the old PO, it is for the cases that have multiple PR
                new_request_no = self.purchase_order_id.request_no + ", " + line.request_id.name
                self.purchase_order_id.update({
                    "request_no": new_request_no
                })
                purchase = self.purchase_order_id
            if not purchase:
                # update the request id value in PO
                po_data = self._prepare_purchase_order(
                    line.description,
                    line.request_id.route_request_ids,
                    line.request_id,
                    line.request_id.picking_type_id,
                    line.request_id.group_id,
                    line.company_id,
                    line.origin,
                    line.request_id.requested_by,
                    line.assigned_to,
                    line.request_id.new_analytic_account_id,

                )
                purchase = purchase_obj.create(po_data)

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True
            # If Unit of Measure is not set, update from wizard.
            if not line.product_uom_id:
                line.product_uom_id = item.product_uom_id
            # Allocation UoM has to be the same as PR line UoM
            alloc_uom = line.product_uom_id
            wizard_uom = item.product_uom_id
            if available_po_lines and not item.keep_description:
                new_pr_line = False
                po_line = available_po_lines[0]
                po_line.purchase_request_lines = [(4, line.id)]
                po_line.move_dest_ids |= line.move_dest_ids
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            else:
                po_line_data = self._prepare_purchase_order_line(purchase, item)
                if item.keep_description:
                    po_line_data["name"] = item.name
                po_line = po_line_obj.create(po_line_data)
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            # TODO: Check propagate_uom compatibility:
            new_qty = pr_line_obj._calc_new_qty(
                line, po_line=po_line, new_pr_line=new_pr_line
            )
            po_line.product_qty = new_qty
            po_line._onchange_quantity()
            # The onchange quantity is altering the scheduled date of the PO
            # lines. We do not want that:
            date_required = item.line_id.date_required
            po_line.date_planned = datetime(
                date_required.year, date_required.month, date_required.day
            )
            res.append(purchase.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }
