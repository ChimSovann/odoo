odoo.define('pos_report.PosOrderModel', function (require) {
"use strict";

var PivotModel = require('web.PivotModel');
var core = require('web.core');
var _t = core._t;

var PointOfSaleModel = PivotModel.include({
    /**
     * @override
     */

    events: _.extend(PivotModel.prototype.events, {
        'input .o_composer_text_field': '_onInputX',
    }),

    init: function (parent, thread) {
        this._super.apply(this, arguments);
        this._thread = thread;
    },

    _sanitizeLabel: function (value, groupBy) {
        var fieldName = groupBy.split(':')[0];
        if (value === false) {
            if (this.modelName == "report.pos.order"){
                return _t("Hotel Card");
            }
            return _t("Undefined");
        }
        if (value instanceof Array) {
            return this._getNumberedLabel(value, fieldName);
        }
        if (fieldName && this.fields[fieldName] && (this.fields[fieldName].type === 'selection')) {
            var selected = _.where(this.fields[fieldName].selection, {0: value})[0];
            return selected ? selected[1] : value;
        }
        return value;
    },

});

return PointOfSaleModel;

});
