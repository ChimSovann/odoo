# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MarketList(models.Model):
    _name = 'market.list'
    _description = 'market_list.market_list'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()
