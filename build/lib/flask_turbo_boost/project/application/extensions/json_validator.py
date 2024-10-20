from functools import wraps
from flask import request
import jsonschema as js

from .errors import error_response


def validate(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            v = js.Draft4Validator(schema)
            errors = list()
            for error in sorted(v.iter_errors(request.json), key=str):
                # TODO more messages format
                errors.append(error.message)

            if errors:
                return error_response(errors)

            return func(*args, **kwargs)
        return wrapper
    return decorator

# Schema Example
# http://json-schema.org/example1.html
