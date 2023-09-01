odoo.define('vkclub', function (require) {
"use strict";



    const screens = require('point_of_sale.screens');
    const models = require('point_of_sale.models');
    const AbstractService = require('web.AbstractService');
    const bus_service = require('bus.BusService');
    const PosBaseWidget = require('point_of_sale.BaseWidget');
    const PaymentScreenWidget = require('point_of_sale.screens').PaymentScreenWidget;
    const gui = require('point_of_sale.gui');
    const chrome = require("point_of_sale.chrome");
    const core = require('web.core');
    const QWeb = core.qweb;
    const _t = core._t;

    var PosConnection = require('pos_longpolling.PosConnection');
    var LongpollingBus = require('bus.Longpolling');
    var global_order = {};
    var global_data = {};



    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
       initialize: function (session, attributes) {
            this.uuid = this.generateUUID();
            _super_order.initialize.apply(this, arguments);
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.qrcode = json.qrcode || '' ;
            this.uuid = json.uuid || this.uuid;
            this.vkpoint_cash = true;
        },
        export_for_printing: function () {
            let order = _super_order.export_for_printing.apply(this, arguments);
            order.uuid = this.uuid;
            order.qrcode = this.qrcode;
            order.vkpoint_cash = this.vkpoint_cash;
            const vat = Math.round(this.get_total_tax() * 100) / 100;
            let is_vkpoint_payment = true;
//            console.log("this is order", order)
            order.is_vkpoint = is_vkpoint_payment;
            return order;
        },
        export_as_JSON: function () {
            let order = _super_order.export_as_JSON.apply(this, arguments);
            order.uuid = this.uuid;
            order.qrcode = this.qrcode;
            order.vkpoint_cash = this.vkpoint_cash;
            return order;
        },
        generateUUID: function() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
          });
        },

        vkpoint_order_commit: function (partner_id, is_cash, remark, paymentScreen){
            const partner = this.pos.db.get_partner_by_id(partner_id);
            const self= this;

            self.set('state','paid');
            self.set_client(partner);
            _.each(self.pos.payment_methods, function (payment_method) {
                if (payment_method.name === "Vkpoint")
                    self.add_paymentline(payment_method);
                self.selected_paymentline.set_amount(self.get_total_with_tax())
            });
            let payment_lines = self.paymentlines.models;
//            console.log(payment_lines)
            payment_lines.forEach(function (line) {
                if (!line.selected)
                    self.remove_paymentline(line);
//                console.log("Currently in payment line")
            });
//            console.log("From line 41")
            self.save_to_db("order:change");
            if (!is_cash) {
                let data = self.get_vkpoint_data();
                data.remark = remark;
                self.pos.chrome.screens.payment._rpc({
                    model:'vk.data',
                    method:'create_vkorder',
                    args: ['OID-' + this.uid.split("-").join(""), data],
                });
                if (self.pos.config.iface_print_via_proxy) {
//                    console.log("line 55")
                    const receipt = QWeb.render('OrderReceipt', self.pos.chrome.screens.receipt.get_receipt_render_env());
//                    console.log("This is the receipt", receipt)
                    self.pos.proxy.printer.print_receipt(receipt);
//                    console.log("60 and this is the receipt", receipt)
                    setTimeout(function () {
                        self.pos.proxy.printer.print_receipt(receipt);
                        self.destroy();    //finish order and go back to scan screen
                    }, 1000);
                } else {
                    self.pos.gui.show_screen('receipt');
                    return false
                }
            } else {
                return true;
            }
            return true;
        },

        get_vkpoint_data: function () {
            if(!this.qrcode){
               let qr = new QRious();
                 qr.set({
                    background: 'white',
                    backgroundAlpha: 1,
                    foreground: 'black',
                    foregroundAlpha: 1,
                    level: 'H',
                    size: 200,
                    value: 'OID-' + this.uid.split("-").join("")
                });
                 this.qrcode = qr.toDataURL();
                 this.save_to_db("order:change")
            }
            const state = this.get('state') || 'pending';
            let items = [];
            let orderLines = this.pos.get_order().selected_orderline.collection.models;
            Object.keys(orderLines).forEach(function(index) {
                let orderline = orderLines[index];
                let unit_price = orderline.get_unit_price();
                let qty = orderline.get_quantity();
                let disc = Math.min(Math.max(parseFloat(orderline.get_discount()) || 0, 0),100);
                let subtotal = Math.round(unit_price * qty * (1 - disc/100) * 100) / 100;
//                console.log("Orderline product name", "==========", orderline.get_product().display_name)
                items.push({
                    'name': orderline.get_product().display_name,
                    'unitPrice': unit_price,
                    'uom': orderline.get_unit().name,
                    // 'imageURL': window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id=' + orderline.get_product().id,
                    'qty': qty,
                    'discount': disc,
                    'subtotal': subtotal
                });
        });


            const total = Math.round(this.get_total_with_tax() * 100) / 100;
            const vat = Math.round(this.get_total_tax() * 100) / 100;
            let vkpoint_cash = true;

            if(this.pos.config.name === "Activity")
                vkpoint_cash = false;
            vkpoint_cash = this.vkpoint_cash || vkpoint_cash;
            return {
                'purchaseId': 'OID-' + this.uid.split("-").join(""),
                'vendor': this.pos.config.name,
                'items': items,
                'state': state,
                'totalNoVat': Math.round((total - vat) * 100) / 100,
                'vat': vat,
                'is_cash': vkpoint_cash,
                'total': total
            };
        },
    })

    screens.PaymentScreenWidget.include({
       init: function(parent, options) {
        const self = this;
        this._super(parent, options);

        },

        update_payment_summary: function (order) {
            const self = this;

            console.log(order.uid.split("-").join(""), 'hello')
            let data = order.get_vkpoint_data();
            global_order = order
            global_data = data
//            console.log("Global Data>>>>vkpoint: ", global_data)

                const qrcode = QWeb.render('VKPointLineWidget');
                const qrcodeImage = self.$('.payment-buttons').html(qrcode);

                if(order.qrcode) {
                     self.$('.vkpoint').removeClass('oe_hidden');
                        self.$('.payment-state').html("Pending");
                        self.$('#qrcode').attr("src", order.qrcode);

            }

            self._rpc({
            model:'vk.data',
            method:'set_order',
            args: ['OID-' + order.uid.split("-").join(""), data],
        });

            return qrcodeImage

        },

        switch_validate_button: function(toggle) {

            const self = this;
            if (toggle==="validate"){
                const validate_xml = QWeb.render('Validate');
                const validate_button = self.$('.top-content .next').html(validate_xml);
                const no_qr = QWeb.render('NoQR');
                const no_qr_show = self.$('.payment-buttons').html(no_qr);
                return validate_button, no_qr_show
            }
            else{
                const check_payment = QWeb.render('CheckPayment');
                const validate_button = self.$('.top-content .next').html(check_payment);
                return validate_button
            }
        },

        click_paymentmethods: function(id) {
        let payment_method = this.pos.payment_methods_by_id[id];

        let order = this.pos.get_order();
//            if(payment_method.name.toLowerCase().substring(0,7) === 'vkpoint' && order.user_id !== 2){
            if(payment_method.name.toLowerCase().substring(0,7) === 'vkpoint'){
//                this.$('.top-content .next').hide();
//                console.log("This as an event", this);
                this.update_payment_summary(order);
                this.switch_validate_button("check_payment");
            } else {
                this.switch_validate_button("validate");
            }

            if (order.electronic_payment_in_progress()) {
            this.gui.show_popup('error',{
                'title': _t('Error'),
                'body':  _t('There is already an electronic payment in progress.'),
            });
        } else {
            order.add_paymentline(payment_method);
            this.reset_input();

            this.payment_interface = payment_method.payment_terminal;
            if (this.payment_interface) {
                order.selected_paymentline.set_payment_status('pending');
            }

            this.render_paymentlines();
        }

    },
    validate_order: function(force_validation) {
        const self = this;
        const payment_screen = self.chrome.screens.payment;

        var text = self.$(".top-content .next").first();
//        var text = html[1].innerText;
        text = text[0].innerText.trim();
//        console.log(text)
        if (text === "Validate"){
            if (payment_screen.order_is_valid(force_validation)) {
                payment_screen.finalize_validation();
            }
        }
        else{
//            console.log("Check Payment function here!!!");
//             console.log("Global Order>>>", order)
//             console.log("Global Data>>>>", global_data)
//             console.log("OID>>>>>", data.purchaseId)
             self._rpc({
                model:'vk.data',
                method:'check_payment_method',
                args: [global_data.purchaseId, global_data.purchaseId],
//                args: [global_data.purchaseId, 'OID-005040020002'],
             }).then(function (result){
//                console.log("Result of check_payment_method === ", result);
                if (result.is_paid){
                    const validateOrder = global_order.vkpoint_order_commit(result.partner_id,global_data.is_cash,result.remark);
                    if(validateOrder && payment_screen.order_is_valid(force_validation)){
//                    if(payment_screen.order_is_valid(force_validation)){
                        payment_screen.finalize_validation();
                    }
                }else{
                    alert("Order not paid or Client Token is expired!!!")
                }
             });
        }
    },
    });

var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
    initialize: function(){
        console.log("initalize hz hz")
        PosModelSuper.prototype.initialize.apply(this, arguments);
//        this.bus.add_channel_callback("vk.pos.order", this._onNotification, this);
    },

            _onNotification: function(message) {
            const self = this;
            console.log("This is the notification", message)




            console.log("Reach Channel Checking", self.get_order())
            _.each(self.get_order().collection.models, function (order) {
                console.log("order", order)
                let oid = 'OID-' + order.uid.split("-").join("");
                if ((message.purchaseId === oid) && (message.state==='paid')){
                    console.log("Message is cash", message.is_cash)
                    const validateOrder = order.vkpoint_order_commit(message.partner_id,message.is_cash,message.remark);
                    if(validateOrder){
                        self.chrome.screens.payment.validate_order();
                    }

                }

            });

        },


});


});
