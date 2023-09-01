from odoo import api, fields, models, _


class RouteInPO(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    route_ids = fields.Many2many(
        'stock.location.route', 'stock_route_purchase_rel', 'order_id', 'route_id', 'Routes',
        domain=[('purchase_quot_selectable', '=', True)],
        track_visibility="onchange",
        required=True,
        store=True,
        states=READONLY_STATES,
        )

    #onchange the route inside product
    @api.onchange('route_ids')
    def _onchange_route_id(self):
        for order in self:
            ware_route = order.route_ids
            route_type = self.env['stock.location.route'].search(
                [('name', 'like', '%Buy')])
            product_route = [ware_route.id, route_type.id]
            if ware_route:
                for line in order.order_line:
                    for item in line.product_id:
                        item.update(
                            {
                                "route_ids": product_route,
                            }
                        )

#to make it onchange when confirm
    def button_confirm(self):
        for order in self:
            # if order.state in ['draft', 'sent']:
            order._onchange_analytic_account_id()
            order._onchange_route_id()
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    po_route = fields.Many2one('stock.location.route', 'Purchase Route')


class RouteCustomized(models.Model):
    _inherit = 'stock.location.route'

    purchase_quot_selectable = fields.Boolean(
        'Applicable on RFQ',
        default=True,
        help="When checked, the route will be selectable in the Purchase for Quotation form.")
    purchase_ids = fields.Many2many(
        'purchase.order', 'stock_route_purchase_rel', 'route_id', 'order_id',
        'Purchase For Quotation', copy=False, check_company=True)
    isRouteActive = fields.Boolean("IsRouteActive", default=False,
                                   help="Check it if you want it to appear when select route in RFQ")


