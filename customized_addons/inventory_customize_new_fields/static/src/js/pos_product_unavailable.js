odoo.define('inventory_customize_new_fields.PosClickProduct', function (require) {
"use strict";


var core = require('web.core');

var Screens = require('point_of_sale.screens');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var _t = core._t;

/** @override when click on product */
Screens.ProductScreenWidget.include({
   click_product: function(product) {

       if(product.to_weight && this.pos.config.iface_electronic_scale){
           this.gui.show_screen('scale',{product: product});
       }else if (product.qty_available <= 0 && product.type === 'product'){
          this.gui.show_popup('error',{
             'title': _t('Quantity is not enough'),
             'body':  _t('Cannot purchase product that not available in stock!'),
          });
       }
       else{
           this.pos.get_order().add_product(product);
       }
   },
});

/* @override Payment button */
Screens.ActionpadWidget.include({

    renderElement: function() {
        PosBaseWidget.prototype.renderElement.call(this);
        var self = this;
        this.$('.pay').click(function(){
            var order = self.pos.get_order();
            var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                return line.has_valid_product_lot();
            });
            /* loop order line*/
            var has_available_product = _.every(order.orderlines.models, function(line){
                var product = line.get_product();
                console.log(product.qty_available, " == ", line.get_quantity())
                if (product.qty_available < line.get_quantity() && product.type === 'product'){
                    return false
                }else{
                    return true
                }
            });

            if (!has_available_product){
                self.gui.show_popup('error',{
                       'title': _t('Quantity is not enough'),
                       'body':  _t('Cannot purchase product that not has enough in stock!'),
                });
            }
            /*===============*/
            else if(!has_valid_product_lot){
                self.gui.show_popup('confirm',{
                    'title': _t('Empty Serial/Lot Number'),
                    'body':  _t('One or more product(s) required serial/lot number.'),
                    confirm: function(){
                        self.gui.show_screen('payment');
                    },
                });
            }
            else{
                self.gui.show_screen('payment');
            }
        });
        this.$('.set-customer').click(function(){
            self.gui.show_screen('clientlist');
        });
    }
});
});
