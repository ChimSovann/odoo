import json

from odoo import models, fields, api, _
import requests
import logging

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Authorization of Smartlock API
api_token = "c93838ad-0080-4eee-b051-674e83b68298"
headers = {
    "Authorization": "Bearer {}".format(api_token)
}

"""
    This is for admin from frontdesk office to re-generate smartlock admin key.
    return OK if the admin QR code is SENT.
"""


class SmartLockAdminKey(models.TransientModel):
    _name = "smartlock.admin.key"
    _description = "Reset Admin QR Code"

    email = fields.Char(string="Email", default="info@vkirirom.com")

    def action_generate_admin_key(self):
        body = {
            "email": self.email
        }
        try:
            req = requests.patch("http://192.168.0.40:3000/api/room/resetAdminKey/", headers=headers, verify=False,
                                 json=body)
            # Notification
            if req.status_code == 200:
                msg = "Already Sent ADMIN QR Code! Please Check your Email."

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': msg,
                        'type': 'success',
                        'sticky': False
                    }
                }
            else:
                raise ValidationError(_("Error! Please check if this email is valid or not!"))
        except requests.exceptions.ConnectionError as e:
            _logger.info(e)
            print(e, 'error')
