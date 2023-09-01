from odoo import models, fields, api, _


# This is a Wizard class that pop-up before Validate operation
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare


class StockTransferDetails(models.TransientModel):
    _name = 'stock_transfer_details'
    _description = 'Picking wizard'

    picking_id = fields.Many2one('stock.picking', 'Product Move')
    picking_move_line_id = fields.Many2one('stock.move.line', 'Stock Move Line')
    item_ids = fields.One2many('stock_transfer_details_items', 'transfer_id', 'Items', domain=[('product_id', '!=', False)])
    picking_source_location_id = fields.Many2one('stock.location', store=False, readonly=True, required=True)
    picking_destination_location_id = fields.Many2one('stock.location', store=False, readonly=True, required=True)

    @api.model
    def default_get(self, fields):
        res = super(StockTransferDetails, self).default_get(fields)
        picking_ids = self.env.context.get('active_ids', [])
        picking = self.env['stock.picking'].browse(picking_ids)
        items, pack_id = [], []
        for op in picking.move_line_ids_without_package:
            item = {
                'packop_id': op.id,
                'product_id': op.product_id.id,
                'sourceloc_id': op.location_id.id,
                'destinationloc_id': op.location_dest_id.id,
                'owner_id': op.owner_id.id,
                'product_uom_qty': op.product_uom_qty,
                'qty_done': op.qty_done,
                'product_uom_id': op.product_uom_id.id,
                'result_package_id': op.result_package_id.id,
                'package_id': op.package_id.id,
                'lot_id': op.lot_id.id,
                'lot_name': op.lot_name,
                'is_initial_demand_editable': op.is_initial_demand_editable,
                'move_id': op.move_id.id,
                'company_id': op.company_id.id
            }
            items.append([0, 0, item])

        res['picking_source_location_id'] = picking.location_id.id
        res['picking_destination_location_id'] = picking.location_dest_id.id
        res['item_ids'] = items
        return res

    def do_detailed_transfer(self):
        stock_move_line_id = self.env['stock.move.line']
        picking_ids = self.env.context.get('active_ids', [])
        picking = self.env['stock.picking'].browse(picking_ids)
        processed_ids = []

        # Create new operations
        for listItems in [self.item_ids]:
            for prod in listItems:
                pack_data = {
                    'product_id': prod.product_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'owner_id': prod.owner_id.id,
                    'product_uom_qty': prod.product_uom_qty,
                    'qty_done': prod.qty_done,
                    'product_uom_id': prod.product_uom_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'lot_name': prod.lot_name,
                    'is_initial_demand_editable': prod.is_initial_demand_editable,
                    'move_id': prod.move_id.id,
                    'company_id': prod.company_id.id
                }
                if prod.packop_id:
                    self.env['stock.move.line'].search([
                        ('id', '=', prod.packop_id.id),
                        ('product_id', '=', prod.product_id.id),
                        ('product_uom_id', '=', prod.product_uom_id.id),
                        ('location_id', '=', prod.sourceloc_id.id)
                    ]).write({'qty_done': prod.qty_done})
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_data['picking_id'] = picking.id
                    packop_id = stock_move_line_id.create(pack_data)
                    processed_ids.append(packop_id.id)

        # Execute the transfer of the picking
        backorder_result = picking.button_validate()
        if backorder_result.get("no_quantity_done"):
            picking_obj = backorder_result["picking"]
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking_obj.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': picking_obj.env.context,
            }

        if backorder_result.get("skip_over_processed_check"):
            picking_obj = backorder_result["picking"]
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': picking_obj.id})
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': picking_obj.env.context,
            }

        if backorder_result.get("backorder"):
            picking_obj = backorder_result["picking"]
            view = self.env.ref('stock.view_backorder_confirmation')
            wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in picking_obj]})
            return {
                'name': _('Create Backorder?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.backorder.confirmation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': dict(picking_obj.env.context),
            }
        return True


# line items in wizard
class StockTransferDetailsItems(models.TransientModel):
    _name = 'stock_transfer_details_items'
    _description = 'Picking wizard items'

    transfer_id = fields.Many2one('stock_transfer_details', 'Transfer')
    packop_id = fields.Many2one('stock.move.line', "Detailed Operation")
    product_id = fields.Many2one('product.product', 'Product', required=True)
    sourceloc_id = fields.Many2one('stock.location', 'From', required=True)
    destinationloc_id = fields.Many2one('stock.location', 'To', required=True)
    owner_id = fields.Many2one('res.partner', 'From Owner')
    product_uom_qty = fields.Float('Reserved', default=0.0, digits='Product Unit of Measure', readonly=True,
                                   required=True, copy=False)
    qty_done = fields.Float('Done', default=0.0, digits='Product Unit of Measure', copy=False)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    result_package_id = fields.Many2one('stock.quant.package', 'Destination Package')
    package_id = fields.Many2one('stock.quant.package', 'Source Package')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    lot_name = fields.Char('Lot/Serial Number Name')
    is_initial_demand_editable = fields.Boolean(related='move_id.is_initial_demand_editable', readonly=False)

    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True,
                                 default=lambda s: s.env.company.id)
    move_id = fields.Many2one('stock.move', 'Stock Move', check_company=True, index=True)
    partner_id = fields.Many2one('res.partner', 'Destination Address ')

    picking_item_ids = fields.Many2one('stock.picking', 'Product Move')

    # get default product uom
    @api.onchange('product_id')
    def get_default_product_id(self):
        product = self.product_id.with_context(lang=self.partner_id.lang or self.env.user.lang)
        self.product_uom_id = product.uom_id.id


# Inherit stock picking
class PickingInherit(models.Model):
    _inherit = "stock.picking"

    # Override button_validate
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))
        # source and destination location cannot be the same!
        if self.location_id == self.location_dest_id:
            raise UserError(_('Source Location and Destination Location cannot be the same!'))
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # add user as a follower
        self.message_subscribe([self.env.user.partner_id.id])

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        # Propose to use the sms mechanism the first time a delivery
        # picking is validated. Whatever the user's decision (use it or not),
        # the method button_validate is called again (except if it's cancel),
        # so the checks are made twice in that case, but the flow is not broken
        sms_confirmation = self._check_sms_confirmation_popup()
        if sms_confirmation:
            return sms_confirmation

        # move return wizard
        if no_quantities_done:
            return {'picking': self, 'no_quantity_done': True}

        # move return wizard
        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            return {'picking': self, 'skip_over_processed_check': True}

        # Check backorder should check for other barcodes and move return wizard
        if self._check_backorder():
            return {'picking': self, 'backorder': True}

        self.action_done()
        return {'no_quantity_done': False, 'skip_over_processed_check': False, 'backorder': False}


# inherit to check vals['company_id'] that create from stock_transfer_details model
class StockMoveLineInherit(models.Model):
    _inherit = "stock.move.line"

    # inherit to add company.id
    @api.model_create_multi
    def create(self, vals_list):
        mls = super(StockMoveLineInherit, self).create(vals_list)
        for vals in vals_list:
            if vals.get('move_id'):
                vals['company_id'] = self.env['stock.move'].browse(vals['move_id']).company_id.id
            elif vals.get('picking_id'):
                vals['company_id'] = self.env['stock.picking'].browse(vals['picking_id']).company_id.id
            # adding this condition for stock_transfer_details model
            else:
                vals['company_id'] = self.env.company.id
            #######
            # If the move line is directly create on the picking view.
            # If this picking is already done we should generate an
            # associated done move.
            if 'picking_id' in vals and not vals.get('move_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.state == 'done':
                    product = self.env['product.product'].browse(vals['product_id'])
                    new_move = self.env['stock.move'].create({
                        'name': _('New Move:') + product.display_name,
                        'product_id': product.id,
                        'product_uom_qty': 'qty_done' in vals and vals['qty_done'] or 0,
                        'product_uom': vals['product_uom_id'],
                        'location_id': 'location_id' in vals and vals['location_id'] or picking.location_id.id,
                        'location_dest_id': 'location_dest_id' in vals and vals[
                            'location_dest_id'] or picking.location_dest_id.id,
                        'state': 'done',
                        'additional': True,
                        'picking_id': picking.id,
                    })
                    vals['move_id'] = new_move.id

        for ml, vals in zip(mls, vals_list):
            if ml.move_id and \
                    ml.move_id.picking_id and \
                    ml.move_id.picking_id.immediate_transfer and \
                    ml.move_id.state != 'done' and \
                    'qty_done' in vals:
                ml.move_id.product_uom_qty = ml.move_id.quantity_done
            if ml.state == 'done':
                if 'qty_done' in vals:
                    ml.move_id.product_uom_qty = ml.move_id.quantity_done
                if ml.product_id.type == 'product':
                    Quant = self.env['stock.quant']
                    quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                                   rounding_method='HALF-UP')
                    in_date = None
                    available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                              lot_id=ml.lot_id,
                                                                              package_id=ml.package_id,
                                                                              owner_id=ml.owner_id)
                    if available_qty < 0 and ml.lot_id:
                        # see if we can compensate the negative quants with some untracked quants
                        untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                      package_id=ml.package_id, owner_id=ml.owner_id,
                                                                      strict=True)
                        if untracked_qty:
                            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                            Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
                                                             lot_id=False, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                            Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                             lot_id=ml.lot_id, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                    Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                     package_id=ml.result_package_id, owner_id=ml.owner_id,
                                                     in_date=in_date)
                next_moves = ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
                next_moves._do_unreserve()
                next_moves._action_assign()
        return mls
