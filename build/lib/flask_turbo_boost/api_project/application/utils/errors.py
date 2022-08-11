from flask import jsonify


def error_response(msg, imsg=None, code=None, more=None, **kwargs):
    return jsonify(dict(
                    success=False,
                    errors=dict(
                        message=msg,
                        internalMessage=imsg,
                        code=code,
                        moreInfo=more
                ))), kwargs.get('http_code', 400)
