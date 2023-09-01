from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round


class ScrapStock(models.Model):
    _inherit = 'stock.scrap'

    scrap_desc = fields.Char(string='Description', help='The reason why the product is broken')


class ProductFieldsUpdate(models.Model):
    _inherit = 'product.template'

    khmer_name = fields.Char("Khmer name", index=True)
    is_alcohol_or_cigarette = fields.Boolean(string='Is Alcohol or cigarette?', help='Is Alcohol or Cigarette?')
    vkpoint_ref = fields.Char(string='VKPoint Ref', help='The reference of VKPoint')
    menu_card_id = fields.Many2one("hotel.menucard", "Food Item")

    def write(self, vals):
        uom = self.env['uom.uom'].browse(vals.get('uom_id')) or self.uom_id
        uom_po = self.env['uom.uom'].browse(vals.get('uom_po_id')) or self.uom_po_id
        if uom and uom_po and uom.category_id != uom_po.category_id:
            vals['uom_po_id'] = uom.id
        if self.menu_card_id:
            if "khmer_name" in vals:
                self.menu_card_id.with_context(from_inventory=True).write({"khmer_name": vals["khmer_name"]})
        res = super(ProductFieldsUpdate, self).write(vals)
        if 'attribute_line_ids' in vals or (vals.get('active') and len(self.product_variant_ids) == 0):
            self._create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        if 'image_1920' in vals:
            self.env['product.product'].invalidate_cache(fnames=[
                'image_1920',
                'image_1024',
                'image_512',
                'image_256',
                'image_128',
                'can_image_1024_be_zoomed',
            ])
        return res


class PurchaseOrderPickingInherit(models.Model):
    _inherit = "purchase.order"

    # inherit function to update the value of requester and project in stock.picking, (fields: project_analytic_id,
    # new_requester_id were created in inventory_fields_customize
    # this function only pass the value to first move of stock.picking after comfirm order
    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id,
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'project_analytic_id': self.order_line.account_analytic_id.id,
            'new_requester_id': self.requester.id,
        }


class OperationFieldsUpdate(models.Model):
    _inherit = 'stock.picking'

    project_analytic_id = fields.Many2one('account.analytic.account', 'Project', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, required=True)
    new_requester_id = fields.Many2one('res.users', 'Requester', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, required=True)


# to pass the value to the next move of stock.picking
class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    project_analytic_id = fields.Many2one('account.analytic.account', 'Project')
    new_requester_id = fields.Many2one('res.users', 'Requester')

    # get new picking values in order to prepare_stock_moves
    def _get_new_picking_values(self):
        """ return create values for new picking that will be linked with group
        of moves in self.
        """
        origins = self.filtered(lambda m: m.origin).mapped('origin')
        origins = list(dict.fromkeys(origins))  # create a list of unique items
        # Will display source document if any, when multiple different origins
        # are found display a maximum of 5
        # requester_id = self.env['stock.picking'].search[('new_requester_id', '=', self.new_requester_id.id)]
        if len(origins) == 0:
            origin = False
        else:
            origin = ','.join(origins[:5])
            if len(origins) > 5:
                origin += "..."
        partners = self.mapped('partner_id')
        partner = len(partners) == 1 and partners.id or False
        return {
            'origin': origin,
            'company_id': self.mapped('company_id').id,
            'user_id': False,
            'move_type': self.mapped('group_id').move_type or 'direct',
            'partner_id': partner,
            'picking_type_id': self.mapped('picking_type_id').id,
            'location_id': self.mapped('location_id').id,
            'location_dest_id': self.mapped('location_dest_id').id,
            'project_analytic_id': self.mapped('project_analytic_id').id,
            'new_requester_id': self.mapped('new_requester_id').id,

        }


class PurchaseOrderLineStockMoveInherit(models.Model):
    _inherit = 'purchase.order.line'

    # prepare before create stock move then the function create_stock_moves will create the vals base on
    # the value in this function
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """

        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        description_picking = self.product_id.with_context(
            lang=self.order_id.dest_address_id.lang or self.env.user.lang)._get_description(
            self.order_id.picking_type_id)
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'description_picking': description_picking,
            'propagate_cancel': self.propagate_cancel,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'project_analytic_id': self.order_id.order_line.account_analytic_id.id,
            'new_requester_id': self.order_id.requester.id,

        }

        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            po_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
            res.append(template)
        return res
