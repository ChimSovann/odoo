from odoo import fields, models, api


class SaleOrder(models.Model):
  _inherit = 'sale.order'

  deliver_to = fields.Char(string="Deliver To")
  tel = fields.Char(string='Tel')
  x_rate = fields.Float(string='Exchange rate (KHR)')
  x_amount_total_khmer = fields.Float(string="Total (KHR)", compute="_compute_total_khmer")

  @api.onchange('x_rate')
  def _compute_total_khmer(self):
    self.x_amount_total_khmer = self.x_rate * self.amount_total

  def _create_invoices(self, grouped=False, final=False):
    res = super(SaleOrder, self)._create_invoices(grouped, final)
    res.x_rate = self.x_rate
    return res
