from odoo import models, fields, api, _

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    project = fields.Many2one('account.analytic.account', compute="_compute_project", string='Analytic Account', store=True)


    @api.depends("purchase_id")
    def _compute_project(self):
        for record in self:
            project = ""
            if record.purchase_id.order_line:
                for order_line in record.purchase_id.order_line:
                    project = order_line.account_analytic_id
                    break
                record.project = project
            else:
                record.project = None


