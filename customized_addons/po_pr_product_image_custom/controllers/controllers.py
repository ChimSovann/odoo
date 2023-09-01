# -*- coding: utf-8 -*-
# from odoo import http


# class CustomPurchaseOrderProductImage(http.Controller):
#     @http.route('/custom_purchase_order_product_image/custom_purchase_order_product_image/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_purchase_order_product_image/custom_purchase_order_product_image/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_purchase_order_product_image.listing', {
#             'root': '/custom_purchase_order_product_image/custom_purchase_order_product_image',
#             'objects': http.request.env['custom_purchase_order_product_image.custom_purchase_order_product_image'].search([]),
#         })

#     @http.route('/custom_purchase_order_product_image/custom_purchase_order_product_image/objects/<model("custom_purchase_order_product_image.custom_purchase_order_product_image"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_purchase_order_product_image.object', {
#             'object': obj
#         })
