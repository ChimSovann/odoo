# -*- coding: utf-8 -*-
from addons.account_analytic_default_purchase.models import purchase_order_line
from odoo import models, fields, api


class PurchaseOrderImage(models.Model):
    _inherit = 'purchase.order.line'

    image_128 = fields.Binary(compute="_product_image", stored=True, string="Product Image")

    @api.depends('product_id')
    def _product_image(self):
        for product in self:
            product.image_128 = product.product_id.image_128
