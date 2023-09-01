from odoo import models, fields, api


class AnalyticAccountForReporting(models.Model):
    _name = 'analytic.account.for.report'
    _description = 'This model is used to filtered the required analytic account for Detail Payment Reports'

    name = fields.Char('Locations', index=True, required=True, tracking=True)
    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts',
                                            index=True, required=True, tracking=True)
