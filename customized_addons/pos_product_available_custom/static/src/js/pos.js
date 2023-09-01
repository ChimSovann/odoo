odoo.define("pos_product_available_custom.PosModel", function(require) {
    "use strict";

    var rpc = require("web.rpc");
    var models = require("point_of_sale.models");

    var PosModelSuper = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_product_model: function() {
            return _.find(this.models, function(model) {
                return model.model === "product.product";
            });
        },
        initialize: function(session, attributes) {
            this.product_product_model = this.get_product_model(this.models);
            PosModelSuper.initialize.apply(this, arguments);
        },
        load_server_data: function() {
            var self = this;

            var loaded = PosModelSuper.load_server_data.call(this);
            return loaded.then(function() {
                return rpc
                    .query({
                        model: "product.product",
                        method: "search_read",
                        args: [],
                        fields: ["qty_available", "type"],
                        domain: self.product_product_model.domain,
                        context: {
                            location: self.config.default_location_src_id[0],
                        },
                    })
                    .then(function(products) {
                        self.add_product_qty(products);
                    });
            });
        },
    });
});
