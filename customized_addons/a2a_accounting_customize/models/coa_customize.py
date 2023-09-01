from odoo import models, fields


class ChartOfAccount(models.Model):
  _inherit = 'account.account'

  is_parent = fields.Boolean(string='Is Parent')


class AccountOpenChart(models.TransientModel):
  _inherit = 'account.open.chart'
  
  def line_data(self, level, parent_id, wiz_id=False, account=False):
    result = super(AccountOpenChart, self).line_data(level, parent_id, wiz_id, account)
    result['unfoldable'] = account.is_parent
    return result
