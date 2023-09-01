# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomProductHistory(models.Model):
    _inherit = 'product.template'

    def action_view_po(self):
        self.ensure_one()
        action = self.env.ref('custom_product_history.action_purchase_order_report_all_tree').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action


class ProductId(models.Model):
    _inherit = 'product.product'

    def action_view_po(self):
        self.ensure_one()
        action = self.env.ref('custom_product_history.action_purchase_order_report_all_tree').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action


class ProductTreeView(models.Model):
    _inherit = 'purchase.order.line'
