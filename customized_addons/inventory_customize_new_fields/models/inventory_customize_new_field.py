from datetime import timedelta

from odoo import models, fields, api, _
from odoo.tools import float_round
from ast import literal_eval


class InventoryCustomizeNewFields(models.Model):
    _inherit = 'stock.picking'

    request_reference = fields.Char('Request Reference', index=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, help="Request Reference of the document")
    boolean_required = fields.Boolean("Required Field", default=False)
    boolean_hotel_required = fields.Boolean("Hotel Required", default=False)

    # required field based on source location
    def _check_warehouse_location(self):
        warehouse = ['vKirirom', 'A2A', 'KIT. Phnom Penh', 'KIT. A2A']
        if self.picking_type_id.name == "Stock Out" and self.picking_type_id.warehouse_id.name in warehouse:
            self.boolean_required = True
        else:
            self.boolean_required = False

    # for creation from hotel no need to required for field Project and Requester
    def _check_location_for_hotel(self):
        warehouse = ['vKirirom']
        if self.picking_type_id.name == "PoS Orders (Pine View Restaurant)" or self.picking_type_id.name == "PoS Orders (Big Party Tent)" and self.picking_type_id.warehouse_id.name in warehouse:
            self.boolean_hotel_required = False
        else:
            self.boolean_hotel_required = True

    # change default destination
    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        if self.picking_type_id:
            # check warehouse location
            self._check_warehouse_location()
            self._check_location_for_hotel()
            # ----------------
            if self.picking_type_id.default_location_src_id:
                location_id = self.picking_type_id.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
            # Adding more condition on destination location
            if self.picking_type_id.default_location_dest_id:
                if self.picking_type_code == "incoming":
                    location_dest_id = self.picking_type_id.default_location_dest_id.id
                else:
                    location_dest_id = self.env['stock.location'].search([('complete_name', '=', 'Virtual Locations/Transit to vK')])
            # ----------------------
            elif self.partner_id:
                location_dest_id = self.partner_id.property_stock_customer.id
            else:
                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

            if self.state == 'draft':
                self.location_id = location_id
                self.location_dest_id = location_dest_id

        # TDE CLEANME move into onchange_partner_id
        if self.partner_id and self.partner_id.picking_warn:
            if self.partner_id.picking_warn == 'no-message' and self.partner_id.parent_id:
                partner = self.partner_id.parent_id
            elif self.partner_id.picking_warn not in (
                    'no-message', 'block') and self.partner_id.parent_id.picking_warn == 'block':
                partner = self.partner_id.parent_id
            else:
                partner = self.partner_id
            if partner.picking_warn != 'no-message':
                if partner.picking_warn == 'block':
                    self.partner_id = False
                return {'warning': {
                    'title': ("Warning for %s") % partner.name,
                    'message': partner.picking_warn_msg
                }}


class MarketListPurchaseOrderLine(models.Model):
    _inherit = 'kr.purchase.order.line'

    # Related to name from kr.purchase.order
    name = fields.Char(related="order_id.name", string='Order Reference')
    # Adding Total Quantity for use in Inventory Market List History
    product_uom_qty = fields.Float(string='Total Quantity', compute='_compute_market_list_product_uom_qty', store=True)
    entry_ref_invoice = fields.Many2one('account.move', string='Entry Reference', store=True, readonly=True)

    # Total Quantity
    @api.depends('product_uom_id', 'product_qty', 'product_id.uom_id')
    def _compute_market_list_product_uom_qty(self):
        for line in self:
            if line.product_id and line.product_id.uom_id != line.product_uom_id:
                line.product_uom_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
            else:
                line.product_uom_qty = line.product_qty


# Adding Market list purchase history (smart button)
class MarketListProductHistory(models.Model):
    _inherit = 'product.template'

    purchased_market_list_product_qty = fields.Float(compute='_compute_market_list_purchased_product_qty', string='Market List Purchased')

    def _compute_market_list_purchased_product_qty(self):
        for template in self:
            template.purchased_market_list_product_qty = float_round(
                sum([p.purchased_market_list_product_qty for p in template.product_variant_ids]),
                precision_rounding=template.uom_id.rounding)

    def action_view_market_list(self):
        self.ensure_one()
        action = self.env.ref('inventory_customize_new_fields.action_market_list_history').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action


class MarketListProductId(models.Model):
    _inherit = 'product.product'

    purchased_market_list_product_qty = fields.Float(compute='_compute_market_list_purchased_product_qty', string='Market List Purchased')

    def _compute_market_list_purchased_product_qty(self):
        date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
        domain = [
            ('state', '=', ['draft', 'progress', 'validate', 'done']),
            ('product_id', 'in', self.ids),
            ('date_order', '>', date_from)
        ]
        order_lines = self.env['kr.purchase.order.line'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])
        purchased_data = dict([(data['product_id'][0], data['product_uom_qty']) for data in order_lines])
        for product in self:
            if not product.id:
                product.purchased_market_list_product_qty = 0.0
                continue
            product.purchased_market_list_product_qty = float_round(purchased_data.get(product.id, 0),
                                                        precision_rounding=product.uom_id.rounding)

    def action_view_market_list(self):
        self.ensure_one()
        action = self.env.ref('inventory_customize_new_fields.action_market_list_history').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action


class InventoryAdjustment(models.Model):
    _inherit = "stock.inventory"

    ref_adjustment = fields.Char("Reference")


# changing overview flow must check availability before transfer
# class StockPickingTypeInherit(models.Model):
#     _inherit = "stock.picking.type"
#
#     # changing default_immediate_transfer to False
#     def _get_action(self, action_xmlid):
#         action = self.env.ref(action_xmlid).read()[0]
#         if self:
#             action['display_name'] = self.display_name
#
#         # change to false
#         default_immediate_tranfer = False
#         if self.env['ir.config_parameter'].sudo().get_param('stock.no_default_immediate_tranfer'):
#             default_immediate_tranfer = False
#
#         context = {
#             'search_default_picking_type_id': [self.id],
#             'default_picking_type_id': self.id,
#             'default_immediate_transfer': default_immediate_tranfer,
#             'default_company_id': self.company_id.id,
#         }
#
#         action_context = literal_eval(action['context'])
#         context = {**action_context, **context}
#         action['context'] = context
#         return action
