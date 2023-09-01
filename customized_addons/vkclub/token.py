import functools
import logging

from odoo.addons.req_res_handling.response import valid_response, invalid_response
from odoo import http
from werkzeug.security import safe_str_cmp


from odoo.http import request
import datetime
import os
from odoo.tools import config


def validate_token(function):
    @functools.wraps(function)
    def wrap_validate_token(self, *args, **kwargs):
        """."""
        client_token = request.httprequest.headers.get("client_token")
        print("hello from validate_token")
        if not client_token:
            return invalid_response(
                "Client Token not found", "Missing Client Token in request header", 401
            )
        token = config['vkclub_api_key']
        if not safe_str_cmp(token, client_token):
            return invalid_response(
                "Client Token Error", "Wrong Client Token!", 401
            )
        return function(self, *args, **kwargs)
    return wrap_validate_token