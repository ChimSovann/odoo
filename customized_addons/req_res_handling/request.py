import ast

def extract_arguments(payloads, offset=0, limit=0, order=None):
    """ Parse additional data  sent along request."""
    fields, domain, payload = [], [], {}

    if payloads.get("domain", None):
        domain = ast.literal_eval(payloads.get("domain"))
    if payload.get("fields"):
        fields += payload.get("fields")
    if payload.get("offset"):
        offset = int(payload["offset"])
    if payload.get("limit"):
        limit = int(payload.get("limit"))
    if payload.get("order"):
        order = payload.get("order")
    return [domain, fields, offset, limit, order]
