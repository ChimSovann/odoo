odoo.define('a2a_accounting_customize.CoAWidget', function (require){
    'use strict';
    var core = require('web.core');
    var Widget = require('web.Widget');
    var pyUtils = require('web.py_utils');
    var QWeb = core.qweb;
    var CoAWidget = require('account_parent.CoAWidget')
    CoAWidget.include({
        start: function() {
            QWeb.add_template("/a2a_accounting_customize/static/src/xml/parent_line.xml");
            return this._super.apply(this, arguments);
        },
    })
})