# -*- coding: utf-8 -*-
# from odoo import http


# class CustomPrNo(http.Controller):
#     @http.route('/custom_pr_no/custom_pr_no/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_pr_no/custom_pr_no/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_pr_no.listing', {
#             'root': '/custom_pr_no/custom_pr_no',
#             'objects': http.request.env['custom_pr_no.custom_pr_no'].search([]),
#         })

#     @http.route('/custom_pr_no/custom_pr_no/objects/<model("custom_pr_no.custom_pr_no"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_pr_no.object', {
#             'object': obj
#         })
