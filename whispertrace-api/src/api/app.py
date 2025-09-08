"""
This module is the entry point for the API service. It sets up
the Flask app, registers the blueprints, and runs the app.
"""

import os

import warnings

from pathlib import Path

from dynaconf import FlaskDynaconf

from flask import Flask

from flask_smorest import Api

from flask_cors import CORS

from common.constants import ENV_CORS_ORIGIN
from common.setup import get_config_settings, set_up_logging

from api.corpus_api import corpus_blueprint
from api.checkpoint_api import checkpoint_blueprint
from api.mia_api import mia_blueprint


warnings.filterwarnings("ignore", message="Multiple schemas resolved to the name ")

app = Flask(__name__)
FlaskDynaconf(app, dynaconf_instance=get_config_settings())
set_up_logging(Path(app.root_path).parent / "logger_config.yaml")

# Enable CORS for a specific domain with any port
cors_origin = os.environ.get(ENV_CORS_ORIGIN, "http://localhost:*")
CORS(app, resources={r"/*": {"origins": cors_origin}})

api = Api(app)
api.register_blueprint(corpus_blueprint)
api.register_blueprint(checkpoint_blueprint)
api.register_blueprint(mia_blueprint)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
