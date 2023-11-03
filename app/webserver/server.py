from flask import Flask, Response
from flask import request

from app.env_variables import logger

appFlask = Flask(__name__)


# POST endpoint
@appFlask.post('/api/wise-webhook')
def create_entry():
    data = request.get_json(force=True)
    logger.info(data)
    return Response(status=200)


@appFlask.errorhandler(404)
def not_found(e):
    return Response(status=204)


@appFlask.errorhandler(Exception)
def handle_exception(e):
    logger.exception("Error occurred while handling an event")
    return Response(status=204)
