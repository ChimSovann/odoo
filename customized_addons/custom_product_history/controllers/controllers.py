# -*- coding: utf-8 -*-
# from odoo import http


# class CustomProductHistory(http.Controller):
#     @http.route('/custom_product_history/custom_product_history/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_product_history/custom_product_history/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_product_history.listing', {
#             'root': '/custom_product_history/custom_product_history',
#             'objects': http.request.env['custom_product_history.custom_product_history'].search([]),
#         })

#     @http.route('/custom_product_history/custom_product_history/objects/<model("custom_product_history.custom_product_history"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_product_history.object', {
#             'object': obj
#         })
