from odoo import fields, models, _

class VkPosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_vkpoint = fields.Boolean(string="Is Vkpoint ?", default=False)
