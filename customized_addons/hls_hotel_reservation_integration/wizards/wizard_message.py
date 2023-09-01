from odoo import models, fields


class MessageWizard(models.TransientModel):
    _name = 'message.wizard'
    _description = "Use for pop up message"

    message = fields.Text('Message', required=True)

    @staticmethod
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}
