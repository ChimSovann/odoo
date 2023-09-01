from odoo import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def transfer_to_folio(self, orderline_values, folio_id, pos_id, transfer_type, table_name):
        # define objects
        folio_obj = self.env['hotel.folio']
        hotel_restaurant_order_obj = self.env['hotel.restaurant.order']
        activity_obj = self.env['activity']
        menucard_obj = self.env['hotel.menucard']
        hotel_services_obj = self.env['hotel.services']
        hotel_restaurant_tables_obj = self.env['hotel.restaurant.tables']

        # get the folio, table
        folio = folio_obj.browse(folio_id)
        table = hotel_restaurant_tables_obj.search([('name', '=', table_name)])

        """
        Check the transfer type and create the order accordingly:
        1. transfer_type = 'restaurant' - transfer all lines to folio service lines and create table order
        2. transfer_type = 'activity' - transfer all lines to folio service lines and create activity
        """
        if transfer_type == 'restaurant':
            values = {
                'folio_id': folio_id,
                'pos_ids': pos_id,
                'room_id': folio.room_line_ids[0].product_id.id,
                'customer_id': folio.partner_id.id,
                'is_folio': True,
                'table_nos_ids': [(6, 0, [table.id])],
                'order_list_ids': [(0, 0, {
                    'menucard_id': menucard_obj.search([('product_id', '=', line["product_id"])]).id,
                    'item_rate': line["price_unit"],
                    'item_qty': line["product_uom_qty"],
                    'discount_lst': line["discount"],
                }) for line in orderline_values],
            }
            hotel_restaurant_order = hotel_restaurant_order_obj.create(values)
            hotel_restaurant_order.generate_kot()
            hotel_restaurant_order.done_order_kot()

        elif transfer_type == 'activity':
            values = {
                'folio_id': folio_id,
                'pos_activity_ids': pos_id,
                'room_no': folio.room_line_ids[0].product_id.id,
                'partner_id': folio.partner_id.id,
                'booking_items': [(0, 0, {
                    'destination': hotel_services_obj.search([('product_id', '=', line["product_id"])]).id,
                    'unit_price': line["price_unit"],
                    'qty': line["product_uom_qty"],
                    'discount': line["discount"],
                }) for line in orderline_values],
            }
            activity = activity_obj.create(values)
            activity.confirm()
            activity.generate_to_folio()

        return True


class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    def action_confirm(self):
        res = super(HotelFolio, self).action_confirm()
        self.notify_updates(self.ids, 'unlink')
        return res

    def action_cancel(self):
        res = super(HotelFolio, self).action_cancel()
        self.notify_updates(self.ids, 'unlink')
        return res

    def write(self, vals):
        pre_state = self.state
        res = super(HotelFolio, self).write(vals)
        if pre_state == 'draft' and self.state != 'draft':
            self.notify_updates(self.ids, 'unlink')
        elif pre_state != 'draft' and self.state == 'draft':
            self.notify_updates(self.ids, 'create', {'name': self.name,
                                                     'partner_id': [self.partner_id.id, self.partner_id.name]})
        elif pre_state == 'draft' and self.state == 'draft' and vals.get('partner_id'):
            self.notify_updates(self.ids, 'update', {'name': self.name,
                                                     'partner_id': [self.partner_id.id, self.partner_id.name]})
        return res

    @api.model
    def create(self, vals):
        res = super(HotelFolio, self).create(vals)
        self.notify_updates([res.id], 'create', {'name': res.name,
                                                 'partner_id': [res.partner_id.id, res.partner_id.name]})
        return res

    def unlink(self):
        for folio in self:
            if folio.state == 'draft':
                folio.notify_updates(folio.ids, 'unlink')
        return super(HotelFolio, self).unlink()

    def notify_updates(self, folio_ids, action='', vals=None):
        if vals is None:
            vals = {}
        channel_name = "hotel_folio_sync"
        data = {'message': 'update folio', 'folio_ids': folio_ids, 'action': action, 'vals': vals}
        self.env['pos.config'].send_to_all_poses(channel_name, data)
