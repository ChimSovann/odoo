# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseRequestImage(models.Model):
    _inherit = 'purchase.request.line'

    image_128 = fields.Binary(compute="_pr_image", stored=True, string="Product Image")

    @api.depends('product_id')
    def _pr_image(self):
        for product in self:
            product.image_128 = product.product_id.image_128
