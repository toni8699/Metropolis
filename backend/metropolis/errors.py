from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        if exc.code == 400:
            payload = {"status": "validation_error", "message": exc.description}
        elif exc.code == 404:
            payload = {"status": "not_found", "message": exc.description}
        else:
            payload = {"status": "error", "message": exc.description}
        return jsonify(payload), exc.code
