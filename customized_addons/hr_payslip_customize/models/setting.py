from odoo import fields, models, api

class PayrollSetting(models.TransientModel):
    _inherit = "res.config.settings"

    exchange_rate = fields.Integer(string="Exchange Rate (GDT)")

    def set_values(self):
        res = super(PayrollSetting, self).set_values()
        self.env['ir.config_parameter'].set_param('hr_payslip_customize.exchange_rate', self.exchange_rate)
        return res

    @api.model
    def get_values(self):
        res = super(PayrollSetting, self).get_values()
        rates = int(self.env['ir.config_parameter'].sudo().get_param('hr_payslip_customize.exchange_rate'))
        res.update(
            exchange_rate=rates
        )
        return res
