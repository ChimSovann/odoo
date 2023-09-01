# -*- coding: utf-8 -*-
# from odoo import http


# class MarketList(http.Controller):
#     @http.route('/market_list/market_list/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/market_list/market_list/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('market_list.listing', {
#             'root': '/market_list/market_list',
#             'objects': http.request.env['market_list.market_list'].search([]),
#         })

#     @http.route('/market_list/market_list/objects/<model("market_list.market_list"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('market_list.object', {
#             'object': obj
#         })
