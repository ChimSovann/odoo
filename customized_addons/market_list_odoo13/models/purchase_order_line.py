from odoo import models, fields, api
from odoo.osv.osv import except_osv

_STATES = [
    ('draft', 'Draft'),
    ('progress', 'Progress'),
    ('validate', 'Validated'),
    ('done', 'Done'),
]


class InventoryCustomizeNewFields(models.Model):
    _inherit = 'stock.picking'

    request_reference = fields.Char('Request Reference', index=True,
                                    states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                                    help="Request Reference of the document")


class MarketListPurchaseOrderLine(models.Model):
    _name = 'kr.purchase.order.line'
    _description = 'mainly used for creating the purchase order with different analytic account'

    # return the currency's id of KHR
    def _get_usd_currency(self):
        currency_model = self.env['res.currency'].search([('name', '=', 'KHR')])
        return currency_model.id

    name = fields.Char(string='Order Reference')

    order_id = fields.Many2one('kr.purchase.order', string='Order ID')

    product_id = fields.Many2one('product.product', string='Product ID', required=True)

    product_type = fields.Char("Product Type", compute="_onchange_product_identifier")

    product_qty = fields.Float(string='Quantity', required=True)

    price_per_unit = fields.Float(string='Unit Price', default=1)

    sub_total = fields.Float('Sub total', store=True, readonly=True, compute="_compute_sub_total")

    category_id = fields.Many2one('product.category', string='Category')

    currency_id = fields.Many2one('res.currency', "Currency", domain=[('name', 'in', ('USD', 'KHR'))],
                                  default=_get_usd_currency)

    product_uom_id = fields.Many2one('uom.uom', string='Unit', readonly=True)

    date_order = fields.Date(string='Order Date')

    supplier_id = fields.Many2one('kirirom.supplier', string='Supplier')

    invoice_number = fields.Char(string='Invoice')

    state = fields.Selection(selection=_STATES, default='draft', related='order_id.state')

    analytic_acc = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=False)

    debit_acc = fields.Many2one('account.account', string='Debit Account', required=False,
                                states={'done': [('readonly', True)]})

    real_price = fields.Float('Real Price', required=True, default=0)

    price_diff = fields.Float('Price Dif.(num)', compute="_onchange_price_diff", readonly=1)

    price_diff_percent = fields.Float('Price Dif.(%)', compute="_onchange_price_diff_percent", readonly=1)

    entry_ref_invoice = fields.Many2one('account.move', string='Entry Reference', store=True, readonly=True)

    def get_product_n_order_obj(self,
                                vals_list):
        product_id = self.env["product.product"].search([("id", "=", vals_list["product_id"])])
        order_id = self.env["kr.purchase.order"].search([("id", "=", vals_list["order_id"])])
        return [product_id, order_id]

    @api.model
    def create(self,
               vals_list):
        vals_list = dict(vals_list or {})
        values = self.get_product_n_order_obj(vals_list)
        product_id, order_id = values[0], values[1]
        vals_list["category_id"] = product_id.categ_id.id
        vals_list["date_order"] = order_id.date_order
        vals_list["analytic_acc"] = order_id.analytic_account_id.id
        vals_list["entry_ref_invoice"] = order_id.entry_ref
        if vals_list.get("product_uom_id") is None:
            vals_list['product_uom_id'] = product_id.uom_id.id
        res = super(MarketListPurchaseOrderLine, self).create(vals_list)
        return res

    def write(self,
              vals_list):
        vals_list = dict(vals_list or {})
        vals_list['product_uom_id'] = self.product_id.uom_id.id
        res = super(MarketListPurchaseOrderLine, self).write(vals_list)
        return res

    # This computed method's purpose is to find sub total of product quantity and unit price
    ## This onchange method's purpose is to find sub total of product quantity and unit price/real price
    @api.depends("product_qty", "real_price", "price_per_unit")
    def _compute_sub_total(self):
        for line in self:
            print("invoked")
            if line.real_price == 0:
                line.sub_total = line.product_qty * line.price_per_unit
                print("real_price", line.real_price)
                print("unit price", line.price_per_unit)
            else:
                line.sub_total = line.product_qty * line.real_price
                print("real_price", line.real_price)
                print("unit price", line.price_per_unit)

    # This computed method's purpose is to calculate differences
    # between estimated price and real price of product in number
    @api.onchange("price_per_unit", "real_price")
    def _onchange_price_diff(self):
        for line in self:
            line.price_diff = abs(line.real_price - line.price_per_unit)

    # This computed method's purpose is to calculate differences
    # between estimated price and real price of product in percentages
    @api.onchange("price_per_unit", "real_price")
    def _onchange_price_diff_percent(self):
        for line in self:
            if line.price_per_unit == 0 and line.real_price == 0:
                line.price_diff_percent = 0
            elif line.price_per_unit == 0 and line.real_price != 0:
                line.price_diff_percent = 100
            elif line.price_per_unit != 0:
                line.price_diff_percent = (abs(line.real_price - line.price_per_unit) / line.price_per_unit) * 100
            else:
                line.price_diff_percent = 0

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.category_id = self.product_id.categ_id.id
            self.date_order = self.order_id.date_order
            self.analytic_acc = self.order_id.analytic_account_id.id

    @api.onchange('product_id')
    def _onchange_product_identifier(self):
        for line in self:
            if line.product_id.type == "product":
                line.product_type = "Storable Product"
            elif line.product_id.type == "consu":
                line.product_type = "Consumable"
            elif line.product_id.type == "service":
                line.product_type = "Service"
            else:
                line.product_type = "N/A"
