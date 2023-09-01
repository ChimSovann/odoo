odoo.define('pos_hotel_folio_integration.pos_screen_custom', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');

    // load hotel.folio model data to pos
    models.load_models({
        model: 'hotel.folio',
        fields: ['name', 'partner_id', 'checkin_date', 'checkout_date'],
        domain: function(self){ return [['state', '=', 'draft']]},
        loaded: function(self, folios){
            self.folios = folios;
        },
    });

    // subscribe to channel hotel_folio_sync
    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes) {
            PosModelSuper.prototype.initialize.apply(this, arguments);
            var self = this;
            this.bus.add_channel_callback("hotel_folio_sync", self.on_folio_update, self);
        },

        on_folio_update: function(data) {
            if (data.message == 'update folio')  {
                var self = this;
                if (data.action == 'update') {
                    var folio = self.folios.find(function(folio){
                        return folio.id == data.folio_ids[0];
                    });
                    if (folio) {
                        folio.partner_id = data.vals.partner_id;
                    }
                } else if (data.action == 'create') {
                    var folio = {
                        id: data.folio_ids[0],
                        name: data.vals.name,
                        partner_id: data.vals.partner_id,
                    }
                    self.folios.push(folio);
                } else if (data.action == 'unlink') {
                    var folio = self.folios.find(function(folio){
                        return folio.id == data.folio_ids[0];
                    });
                    if (folio) {
                        self.folios.splice(self.folios.indexOf(folio), 1);
                    }
                }
            }

            // check if opening hotel_folio popup
            if (this.gui.current_popup && this.gui.current_popup.options.title == 'Select Folio') {
                this.gui.current_popup.list = this.folios.map(function(folio){
                    return {label: folio.name + " - " + folio.partner_id[1], item: folio.id};
                });
                this.gui.current_popup.renderElement();
            }
        }
    });

    // New orders are now associated with the current table, if any.
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            _super_order.initialize.apply(this,arguments);
            if (!this.table) {
                this.table = this.pos.table;
            }
            this.folio_id = this.folio_id || null;
            this.save_to_db();
        },
        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.table     = this.table ? this.table.name : undefined;
            json.table_id  = this.table ? this.table.id : false;
            json.floor     = this.table ? this.table.floor.name : false;
            json.floor_id  = this.table ? this.table.floor.id : false;
            json.folio_id = this.folio_id;
            return json;
        },
        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this,arguments);
            this.table = this.pos.tables_by_id[json.table_id];
            this.floor = this.table ? this.pos.floors_by_id[json.floor_id] : undefined;
            this.folio_id = json.folio_id || null;
        },
        export_for_printing: function(){
            var json = _super_order.export_for_printing.apply(this,arguments);
            json.table = this.table ? this.table.name : undefined;
            json.floor = this.table ? this.table.floor.name : undefined;
            json.folio_id = this.get_folio_id();
            return json;
        },
        set_folio_id: function(folio_id){
            this.folio_id = folio_id;
            this.trigger('change');
        },
        get_folio_id: function(){
            return this.folio_id;
        },
    });

    var HotelFolioButton = screens.ActionButtonWidget.extend({
        template: 'HotelFolioButton',
        folio: function() {
            if (this.pos.get_order()) {
                if (this.pos.get_order().folio_id) {
                    return this.pos.folios.find(folio => folio.id === this.pos.get_order().folio_id).name;
                }
                return "Folio"
            } else {
                return "Folio";
            }
        },
        button_click: function(){
            var self = this;
            this.gui.show_popup('selection', {
                'title': 'Select Folio',
                'list': [].concat(self.pos.folios.map(function(folio){
                    return {label: folio.name + " - " + folio.partner_id[1], item: folio.id};
                }, this)),
                'is_selected': function(folio_id){
                    return self.pos.get_order().folio_id === folio_id;
                },
                'confirm': function(folio){
                    if (self.pos.get_order().folio_id !== folio) {
                        self.pos.get_order().set_folio_id(folio);
                    } else {
                        self.pos.get_order().set_folio_id(null);
                    }
                    self.renderElement();
                },
            });
        }
    });

    screens.OrderWidget.include({
        update_summary: function(){
            this._super();
            if (this.getParent().action_buttons &&
                this.getParent().action_buttons.hotel_folio) {
                this.getParent().action_buttons.hotel_folio.renderElement();
            }
        },
    });

    screens.define_action_button({
        'name': 'hotel_folio',
        'widget': HotelFolioButton,
        'condition': function(){
            return this.pos.config.iface_transfer_to_folio && this.pos.config.transfer_type;
        }
    });

    var TransferToFolioButton = screens.ActionButtonWidget.extend({
        template: 'TransferToFolioButton',
        button_click: function() {
            var order = this.pos.get_order();

            /* loop order line in order for check stock if available for sell */
            var has_available_product = _.every(order.orderlines.models, function(line){
                var product = line.get_product();
                if (product.qty_available < line.get_quantity() && product.type === 'product'){
                    return false
                }else{
                    return true
                }
            });

            if (!has_available_product){
                this.gui.show_popup('error',{
                       'title': _t('Quantity is not enough'),
                       'body':  _t('Cannot purchase product that not has enough in stock!'),
                });
            }
            ////
            else{
                if (this.pos.get_order().get_orderlines().length !== 0 && this.pos.get_order().folio_id) {
                    // Show popup to confirm transfer
                    console.log("Confirm")
                    this.gui.show_popup('confirm', {
                        'title': 'Transfer Order',
                        'body': 'Are you sure you want to transfer this order to folio ' + this.pos.folios.find(folio => folio.id === this.pos.get_order().folio_id).name + '?',
                        'confirm': function() {
                            var order = this.pos.get_order();
                            var orderlines = order.get_orderlines();
                            var orderline_ids = [];
                            for (var i = 0; i < orderlines.length; i++) {
                                orderline_ids.push(orderlines[i].id);
                            }
                            var paused = new $.Deferred();
                            var orderline_values = [];
                            for (var i = 0; i < orderlines.length; i++) {
                                var order_line = {
                                    'product_id': orderlines[i].product.id,
                                    'name': orderlines[i].product.display_name,
                                    'price_unit': orderlines[i].price,
                                    'product_uom_qty': orderlines[i].quantity,
                                    'discount': orderlines[i].discount,
                                    'tax_id': orderlines[i].product.taxes_id,
                                    'product_uom': orderlines[i].product.uom_id[0],
                                }
                                orderline_values.push(order_line);
                            }
                            // get transfer_type, pos_id, table_name
                            var transfer_type = this.pos.config.transfer_type;
                            var pos_id = this.pos.config.id;
                            var table_name = this.pos.get_order().table?.name;
                            var params = {
                                model: 'pos.order',
                                method: 'transfer_to_folio',
                                args: ['OID-' + order.uid.split("-").join(""), orderline_values, order.folio_id, pos_id, transfer_type, table_name],
                            }
                            rpc.query(params, {async: false}).then(function(result){
                                if (result) {
                                    order.destroy({'reason': 'abandon'});
                                }
                            });
                        }
                    });

                } else {
                    if (this.pos.get_order().get_orderlines().length === 0) {
                        this.gui.show_popup('error', {
                            'title': _t('Empty Order'),
                            'body': _t('There must be at least one product in your order before it can be sent to the hotel.'),
                        });
                    }
                    if (!this.pos.get_order().folio_id) {
                        this.gui.show_popup('error', {
                            'title': _t('No Folio'),
                            'body': _t('You must select a folio to transfer the order to the hotel.'),
                        });
                    }
                }
            }
        },
    });

    screens.define_action_button({
        'name': 'transfer_to_hotel_folio',
        'widget': TransferToFolioButton,
        'condition': function(){
            return this.pos.config.iface_transfer_to_folio && this.pos.config.transfer_type;
        }
    });
});