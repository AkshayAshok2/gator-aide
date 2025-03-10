import json
import logging
import os

from asgiref.wsgi import WsgiToAsgi
from flask import Flask
from flask_cors import CORS
from tempfile import mkdtemp
from backend.flask.cache import get_app_cache
from backend.flask.lti import get_launch_data_storage

CONFIG = {
    "DEBUG": False,
    "ENV": "production",
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 600,
    "SECRET_KEY": os.getenv("FLASK_SECRET_KEY", "fallback_secret_key"),
    "SESSION_TYPE": "filesystem",
    "SESSION_FILE_DIR": mkdtemp(),
    "SESSION_COOKIE_NAME": "pylti1p3-flask-app-sessionid",
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": True,   
    "SESSION_COOKIE_SAMESITE": None,  
    "DEBUG_TB_INTERCEPT_REDIRECTS": False
}

def setup_app(app_name, static_folder='../../frontend', static_url_path=''):
    """
    Creates a Flask app and configures the Flask app,
    asgi app, logging, and exports the jwks file.

    :param app: The Flask application instance name.

    :return: app
    :rtype: Flask application instance.
    :return: asgi_app
    :rtype: Asgi application instance.
    :return: get_launch_data_storage()
    :rtype: LTI Launch Session Storage
    :return: cache
    :rtype: Flask Cache service instance.
    """
    configure_logging()

    app = Flask(
        app_name,
        static_folder=static_folder,
        static_url_path=static_url_path)
    app.config.from_mapping(CONFIG)
    logging.debug("Flask Config: %s", app.config)
    CORS(app)
    asgi_app = WsgiToAsgi(app)
    cache = get_app_cache(app)

    return app, asgi_app, get_launch_data_storage(cache), cache


def configure_logging():
    """
    Configures the Python logging module.

    :params: None

    :return: None
    """
    logging.getLogger().setLevel(10)