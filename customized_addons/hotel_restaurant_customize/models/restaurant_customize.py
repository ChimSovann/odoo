from datetime import timedelta, datetime
from xml import etree
from lxml import etree
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import time


class ProductCategoryName(models.Model):
    _inherit = "product.category"

    name = fields.Char('Name', index=True, required=False)


class RestaurantCustomize(models.Model):
    _inherit = 'hotel.restaurant.order'

    folio_id = fields.Many2one("hotel.folio", "Folio No", domain=[('state', '=', 'draft')])



    def _get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hotel.group_hotel_user'):
            return True
        elif res_user.has_group('hotel.group_hotel_manager'):
            return False
    readonly_field = fields.Boolean(string="check field", default=_get_user)

    @api.model
    def _get_tax_default(self):
        return 10

    tax = fields.Float("VAT (%)", default=_get_tax_default)
    date_action = fields.Datetime('Created on', required=False, readonly=False, select=True
                                  , default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), )
    last_update_date = fields.Datetime('Last Modified on', readonly=False, required=False)
    pos_ids = fields.Many2one(
        "pos.config", "Restaurant", required=True, domain=[('name', '=', ['Big Party Tent', 'Pine View Restaurant'])]
    )

    # new_order_no = fields.Char(string='Table Order', readonly=True)

    # Customized when Folio no room_no add default room in order to make order in Table Order
    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        """
        When you change folio_id, based on that it will update
        the customer_id and room_number as well
        ---------------------------------------------------------
        @param self: object pointer
        """
        if self.folio_id:
            self.update(
                {
                    "customer_id": self.folio_id.partner_id.id,
                }
            )
            if self.folio_id.room_line_ids:
                self.update(
                    {
                        "room_id": self.folio_id.room_line_ids[0].product_id.id,
                    }
                )
            else:
                self.update(
                    {
                        "room_id": self.env['product.product'].search([('name', '=', 'Camping A022')])
                    }
                )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        # sequence = self.env["pos.config"].browse([vals['pos_ids']]).name
        # if sequence == 'Pine View Restaurant':
        #     vals["new_order_no"] = self.env["ir.sequence"].next_by_code('pvk.sequence') or _('New')
        # elif sequence == 'Big Party Tent':
        #     vals["new_order_no"] = self.env["ir.sequence"].next_by_code('bpt.sequence') or _('New')

        # Sequence of hotel order but prefix and padding from pos restaurant
        sequence = self.env["pos.config"].browse([vals['pos_ids']]).sequence_id
        ir_sequence_obj = self.env["ir.sequence"].search([('name', '=', 'Hotel Order')])
        ir_sequence_obj.write({
            'prefix': sequence.prefix,
            'padding': sequence.padding,
            'number_increment': sequence.number_increment,
            'number_next_actual': sequence.number_next_actual,
        })

        sequence.write({'number_next_actual': ir_sequence_obj.number_next_actual + 1})
        return super(RestaurantCustomize, self).create(vals)

    def generate_kot(self):
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        restaurant_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if not order.order_list_ids:
                raise ValidationError(_("Please Give an Order"))
            if not order.table_nos_ids:
                raise ValidationError(_("Please Assign a Table"))
            table_ids = order.table_nos_ids.ids
            kot_data = order_tickets_obj.create(
                {
                    "orderno": order.order_no,
                    "kot_date": order.o_date,
                    "room_no": order.room_id.name,
                    "w_name": order.waiter_id.name,
                    "table_nos_ids": [(6, 0, table_ids)],
                }
            )

            for order_line in order.order_list_ids:
                o_line = {
                    "kot_order_id": kot_data.id,
                    "menucard_id": order_line.menucard_id.id,
                    "item_qty": order_line.item_qty,
                    "item_rate": order_line.item_rate,
                }
                restaurant_order_list_obj.create(o_line)
                res.append(order_line.id)
            order.update(
                {
                    "kitchen": kot_data.id,
                    "rest_item_id": [(6, 0, res)],
                    "state": "order",
                    "last_update_date": fields.Datetime.now(),
                }
            )
        return True

    def generate_kot_update(self):
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            line_data = {
                "orderno": order.order_no,
                "kot_date": fields.Datetime.to_string(fields.datetime.now()),
                "room_no": order.room_id.name,
                "w_name": order.waiter_id.name,
                "table_nos_ids": [(6, 0, order.table_nos_ids.ids)],
            }
            kot_id = order_tickets_obj.browse(self.kitchen)
            kot_id.write(line_data)
            for order_line in order.order_list_ids:
                if order_line.id not in order.rest_item_id.ids:
                    kot_data = order_tickets_obj.create(line_data)
                    order.kitchen = kot_data.id
                    o_line = {
                        "kot_order_id": kot_data.id,
                        "menucard_id": order_line.menucard_id.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    order.rest_item_id = [(4, order_line.id)]
                    rest_order_list_obj.create(o_line)
                    order.update(
                        {
                            "last_update_date": fields.Datetime.now(),
                        }
                    )
        return True

    def done_order_kot(self):
        hsl_obj = self.env["hotel.service.line"]
        so_line_obj = self.env["sale.order.line"]
        for order_obj in self:
            for order in order_obj.order_list_ids:
                if order_obj.folio_id:
                    values = {
                        "order_line": order.id,
                        "order_id": order_obj.folio_id.order_id.id,
                        "name": order.menucard_id.name,
                        "product_id": order.menucard_id.product_id.id,
                        "product_uom": order.menucard_id.uom_id.id,
                        "product_uom_qty": order.item_qty,
                        "price_unit": order.item_rate,
                        "discount": order.discount_lst,
                        "price_subtotal": order.price_subtotal,
                    }
                    sol_rec = so_line_obj.create(values)
                    hsl_obj.create(
                        {
                            "folio_id": order_obj.folio_id.id,
                            "service_line_id": sol_rec.id,
                        }
                    )
                    order_obj.folio_id.write(
                        {"hotel_restaurant_orders_ids": [(4, order_obj.id)]}
                    )
            self.write({"state": "done"})
        return True

    def done_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant order
        and service line from Folio
        ----------------------------------------
        @param self: object pointer
        """
        ids = []
        for line in self.order_list_ids:
            ids.append(line.id)

        for line in self.folio_id.service_line_ids:
            if line.order_line in ids:
                line.unlink()
        self.write({"state": "cancel"})
        return True

    # Delete Table Order
    def unlink(self):
        for rec in self:
            raise ValidationError(_('You can not delete Table Order in %s\
                                state.') % (rec.state))
        return super(RestaurantCustomize, self).unlink()


class RestaurantCustomizeOrderList(models.Model):
    _inherit = 'hotel.restaurant.order.list'

    discount_lst = fields.Float(string="Discount", readonly=False)

    @api.depends("item_qty", "item_rate")
    def _compute_price_subtotal(self):
        for line in self:
            discount = (line.item_rate * line.item_qty) * (line.discount_lst / 100)
            line.price_subtotal = (line.item_rate * int(line.item_qty)) - discount


class SaleOrderLineCancelInherit(models.Model):
    _inherit = 'sale.order.line'

    order_line = fields.Integer(string="No")


class HotelMenucardTypeInherit(models.Model):
    _inherit = 'hotel.menucard.type'

    product_categ_id = fields.Many2one(
        "product.category", "Product Category", delegate=True
    )

    @api.model
    def create(self, vals):
        if "menu_id" in vals:
            menu_categ = self.env["hotel.menucard.type"].browse(
                vals.get("menu_id")
            )
            vals.update({"parent_id": menu_categ.product_categ_id.id})
            res = super(HotelMenucardTypeInherit, self).create(vals)
            for value in res:
                value.product_categ_id.update({'name': value.name})
        return res

    def write(self, vals):
        if "menu_id" in vals:
            menu_categ = self.env["hotel.menucard.type"].browse(
                vals.get("menu_id")
            )
            vals.update({"parent_id": menu_categ.product_categ_id.id})
        self.product_categ_id.update({'name': vals.get("name")})
        return super(HotelMenucardTypeInherit, self).write(vals)


class HotelMenucardInherit(models.Model):
    _inherit = 'hotel.menucard'

    khmer_name = fields.Char("Khmer name")

    @api.model
    def create(self, vals):
        product_categ_id = 1
        if "categ_id" in vals:
            menu_categ = self.env["hotel.menucard.type"].browse(
                vals.get("categ_id")
            )
        product_categ_id = menu_categ.product_categ_id
        res = super(HotelMenucardInherit, self).create(vals)
        for menucard in res:
            menucard.product_id.product_tmpl_id.update(
                {"categ_id": product_categ_id, "khmer_name": menucard.khmer_name, "menu_card_id": menucard})
        return res

    def write(self, vals):
        if not self._context.get("from_inventory"):
            if "khmer_name" in vals:
                self.product_id.product_tmpl_id.update({"khmer_name": vals["khmer_name"]})
            if "categ_id" in vals:
                menu_categ = self.env["hotel.menucard.type"].browse(
                    vals.get("categ_id")
                )
                product_categ_id = menu_categ.product_categ_id
                self.product_id.product_tmpl_id.update({"categ_id": product_categ_id})

        return super(HotelMenucardInherit, self).write(vals)


class HotelServiceTypeInherit(models.Model):
    _inherit = "hotel.service.type"

    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.service_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]


class HotelRoomAmenitiesType(models.Model):
    _inherit = "hotel.room.amenities.type"

    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.amenity_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]


