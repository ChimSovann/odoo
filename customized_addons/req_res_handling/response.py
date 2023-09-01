import werkzeug.wrappers
import json
import datetime


def valid_response(data, status=200):
    """Valid Response
    This will be return when the http request was successfully processed."""
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data, default=datetime.datetime.isoformat),
    )


def invalid_response(type, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    # return json.dumps({})
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {
                "type": type,
                "message": str(message)
                if str(message)
                else "wrong arguments (missing validation)",
            },
            default=datetime.datetime.isoformat,
        ),
    )
