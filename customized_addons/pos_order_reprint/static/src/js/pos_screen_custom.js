odoo.define('pos_order_reprint.pos_screen_custom', function (require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var screens = require('point_of_sale.screens');
    var OrderSuper = models.Order;

    var QWeb = core.qweb;

    var TableGuestsButton = screens.ActionButtonWidget.extend({
        template: 'TableGuestsButton',
        guests: function() {
            if (this.pos.get_order()) {
                return this.pos.get_order().customer_count;
            } else {
                return 0;
            }
        },
        button_click: function() {
            var self = this;
            this.gui.show_popup('number', {
                'title':  _t('Guests ?'),
                'cheap': true,
                'value':   this.pos.get_order().customer_count,
                'confirm': function(value) {
                    value = Math.max(1,Number(value));
                    self.pos.get_order().set_customer_count(value);
                    self.renderElement();
                },
            });
        },
    });

    screens.define_action_button({
        'name': 'guests',
        'widget': TableGuestsButton,
        'condition': function(){
            return !this.pos.config.iface_floorplan;
        },
    });

    models.Order = models.Order.extend({
        export_for_printing: function(){
            var result = OrderSuper.prototype.export_for_printing.call(this);

            //add total quantity to receipt
            var total_quantity = 0;
            var order_lines = result.orderlines;
            order_lines.forEach(function(order_line) {
                total_quantity += order_line.quantity;
            });
            result.total_quantity = total_quantity;

            //add order_ref to receipt
            result.order_ref = this.order_ref;
            result.order_date = moment().format(
                "YYYY-MM-DD HH:mm:ss"
            );

            return result;
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        push_order: function(order, opts) {
            _super_posmodel.push_order.call(this, order, opts);
            opts = opts || {};
            var self = this;
            if(order){
                this.db.add_order(order.export_as_JSON());
            }

            var pushed = new $.Deferred();

            this.flush_mutex.exec(function(){
                var flushed = self._flush_orders(self.db.get_orders(), opts);
                //tasos get order_ref from server
                if(order){
                    rpc.query({
                        model: 'pos.order',
                        method: 'search_read',
                        domain: [['pos_reference', '=', order.name]],
                        fields: ['name', 'payment_ids', 'customer_count'],
                        limit: 1,
                    }).then(function(data){
                        if(data.length > 0){
                            var order_ref = data[0].name;
                            order.order_ref = order_ref;
                            order.customer_count = data[0].customer_count;

                            if(opts["reprint"] === true) {
                                order.reprint = true;

                                var payment_ids = data[0].payment_ids;
                                var pushed1 = new $.Deferred();
                                rpc.query({
                                    model: 'pos.payment',
                                    method: 'search_read',
                                    domain: [['id', '=', payment_ids]],
                                    fields: ['amount', 'payment_method_id'],
                                }).then(function(payments){
                                    var paymentlines = [];
                                    for(var i = 0, l = payments.length; i < l; i++) {
                                        var paymentline = {
                                            name: payments[i].payment_method_id[1],
                                            amount: payments[i].amount
                                        };
                                        if(paymentline.amount < 0) {
                                            order.change = Math.abs(paymentline.amount);
                                        } else {
                                            paymentlines.push(paymentline);
                                        }
                                    }
                                    order.reprint_paymentlines = paymentlines;
                                    pushed1.resolve();
                                    pushed.resolve();
                                });
                            } else {
                                pushed.resolve();
                            }
                        };
                    });
                } else{
                    pushed.resolve();
                };
                return flushed;
            });
            return pushed;
        },
    });

    screens.PaymentScreenWidget.include({
        finalize_validation: function() {
            var self = this;
            var order = this.pos.get_order();

            if ((order.is_paid_with_cash() || order.get_change()) && this.pos.config.iface_cashdrawer) {

                    this.pos.proxy.printer.open_cashbox();
            }

            order.initialize_validation_date();
            order.finalized = true;

            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;

                invoiced.catch(this._handleFailedPushForInvoice.bind(this, order, false));

                invoiced.then(function (server_ids) {
                    self.invoicing = false;
                    var post_push_promise = [];
                    post_push_promise = self.post_push_order_resolve(order, server_ids);
                    post_push_promise.then(function () {
                            self.gui.show_screen('receipt');
                    }).catch(function (error) {
                        self.gui.show_screen('receipt');
                        if (error) {
                            self.gui.show_popup('error',{
                                'title': "Error: no internet connection",
                                'body':  error,
                            });
                        }
                    });
                });
            } else {
                if (order.wait_for_push_order()){
                    var server_ids = [];
                    ordered.then(function (ids) {
                      server_ids = ids;
                    }).finally(function() {
                        var post_push_promise = [];
                        post_push_promise = self.post_push_order_resolve(order, server_ids);
                        post_push_promise.then(function () {
                                self.gui.show_screen('receipt');
                            }).catch(function (error) {
                              self.gui.show_screen('receipt');
                              if (error) {
                                  self.gui.show_popup('error',{
                                      'title': "Error: no internet connection",
                                      'body':  error,
                                  });
                              }
                            });
                      });
                }
                else {
                  this.pos.push_order(order).then(function() {
                    self.gui.show_screen('receipt');
                  });
                }

            }
        },
    });

    // Extend ReceiptScreenWidget to override print_html function to print receipt twice or double print receipt
    screens.ReceiptScreenWidget.include({
        print_html: function() {
            const self = this;
            var receipt = QWeb.render('OrderReceipt', this.get_receipt_render_env());
            this.pos.proxy.printer.print_receipt(receipt);
            const order = this.pos.get_order();
            const reprint = order.reprint || this.pos.last_receipt_render_env.receipt.reprint || false;
            const bill = this.pos.last_receipt_render_env.receipt.bill || false;
            if (!(reprint || bill)) {
                setTimeout(function () {
                    self.pos.proxy.printer.print_receipt(receipt);
                }, 1000);
            }
            this.pos.get_order()._printed = true;
        },
    });
});