# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ActivityFolio(models.Model):
    _inherit = 'hotel.folio'

    activity_order_id = fields.Many2many("activity", string="Activity Orders")


def get_tax_default():
    return 10


class Activity(models.Model):
    _name = 'activity'
    _description = 'activity'

    @api.depends('booking_items')
    def _compute_amount_all_total(self):
        for record in self:
            record.amount_subtotal = sum(
                line.price_subtotal for line in record.booking_items
            )

            record.amount_total = 0.0
            if record.amount_subtotal:
                record.amount_total = (
                        record.amount_subtotal
                        + (record.amount_subtotal * record.vat_value) / 100
                )

    @api.model
    def _get_tax_default(self):
        return 10

    @api.model
    def _default_pos_ids(self):
        return self.env['pos.config'].search([('name', '=', 'Activity')], limit=1)

    name = fields.Char(string='Reference No', readonly=True, required=True, copy=False, default=_('New'))
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True, required=True,
                                 states={'draft': [('readonly', False)]})
    date_order = fields.Datetime('Date Ordered', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: fields.Datetime.now())
    folio_id = fields.Many2one('hotel.folio', 'Folio No', readonly=True,
                               states={'draft': [('readonly', False)]}, required=True,
                               domain=[('state', '=', 'draft')])
    room_no = fields.Many2one('product.product', "Room Number", readonly=True, required=False,
                              states={'draft': [('readonly', False)]})
    booking_items = fields.One2many('activity.item', 'order_id', 'Items Line', readonly=True, required=True,
                                    states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('manual_invoice', 'Progress'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')],
                             "state",
                             required=True,
                             readonly=True,
                             default="draft",
                             )
    amount_subtotal = fields.Float(compute="_compute_amount_all_total", string="Subtotal")
    vat_value = fields.Float("VAT (%)", default=_get_tax_default)
    amount_total = fields.Float(compute="_compute_amount_all_total", string="Total")
    # var for get pos activity sequence
    pos_activity_ids = fields.Many2one("pos.config", "Activity", required=True, default=_default_pos_ids)

    def confirm(self):
        self.write({'state': 'confirm'})

        line_list = []
        for line in self.booking_items:
            line_dict = dict()
            line_dict.update({
                'reference': self.name,
                'name': self.partner_id.name,
                'email': self.partner_id.email,
                'phone': self.partner_id.phone,
                'destination_id': line.destination.product_id.id,
                'amount': int(line.qty),
                'status': self.state
            })
            line_list.append(line_dict)

    def generate_to_folio(self):
        hsl_obj = self.env['hotel.service.line']
        so_line_obj = self.env['sale.order.line']
        for order in self.booking_items:
            values = {'order_id': self.folio_id.order_id.id,
                      'activity_order_line': order.id,
                      'name': order.destination.name,
                      'product_id': order.destination.product_id.id,
                      'product_uom_qty': order.qty,
                      'price_unit': order.unit_price,
                      'discount': order.discount,
                      'price_subtotal': order.price_subtotal,
                      }
            sol_rec = so_line_obj.create(values)

            hsl_obj.create(
                {
                    "folio_id": self.folio_id.id,
                    "service_line_id": sol_rec.id,
                }
            )

            self.folio_id.write(
                {"activity_order_id": [(4, self.id)]}
            )

            self.write({'state': 'done'})
        return True

    def done_cancel(self):
        ids = []
        for line in self.booking_items:
            ids.append(line.id)

        for line in self.folio_id.service_line_ids:
            if line.activity_order_line in ids:
                line.unlink()
        self.write({'state': 'cancel'})
        return True

    def write(self, vals):
        res = super(Activity, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        # Get Sequence from pos activity
        sequence = self.env["pos.config"].browse([vals['pos_activity_ids']]).sequence_id
        ir_sequence_obj = self.env["ir.sequence"].search([('name', '=', 'Activity')])

        ir_sequence_obj.write({
            'prefix': sequence.prefix,
            'padding': sequence.padding,
            'number_increment': sequence.number_increment,
            'number_next_actual': sequence.number_next_actual,
        })

        vals["name"] = ir_sequence_obj.next_by_code('activity.sequence')
        sequence.write({'number_next_actual': ir_sequence_obj.number_next_actual + 1})
        return super(Activity, self).create(vals)

    @api.onchange('folio_id')
    def get_folio_partner_id(self):

        if self.folio_id:

            self.update(
                {
                    "partner_id": self.folio_id.partner_id.id,
                }
            )
            if self.folio_id.room_line_ids:
                self.update(
                    {
                        "room_no": self.folio_id.room_line_ids[0].product_id.id,
                    }
                )
            else:
                self.update(
                    {
                        "room_no": self.env['product.product'].search([('name', '=', 'Camping A022')])
                    }
                )


class ActivityItem(models.Model):
    _name = 'activity.item'

    @api.depends('unit_price', 'qty', 'discount')
    def _sub_total(self):
        for record in self:
            discount_amount = (record.unit_price * record.qty) * (record.discount / 100)
            record.price_subtotal = record.unit_price * record.qty - discount_amount

    name = fields.Char('Activity Line')
    # destination = fields.Many2one('hotel.services', 'Activity', domain=[('service_categ_id.name', '=', 'vK Services')],
    #                               required=True)
    destination = fields.Many2one('hotel.services', 'Activity', required=True)
    order_id = fields.Many2one('activity', 'Reference')
    customer = fields.Many2one('res.partner', 'Customer')
    date_of_booking = fields.Datetime('Date of Booking')
    qty = fields.Float('Quantity', required=True)
    unit_price = fields.Float('Unit Price', required=True)
    price_subtotal = fields.Float('Sub Total', compute='_sub_total', readonly=True)
    discount = fields.Float('Discount')


class SaleOrderLineCancelInherit(models.Model):
    _inherit = 'sale.order.line'

    activity_order_line = fields.Integer(string="Activity Order")
