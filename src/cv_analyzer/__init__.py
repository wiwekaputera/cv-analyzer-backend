# src/cv_analyzer/__init__.py

import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import os
from flask import Flask
from flask_cors import CORS
from decouple import config
from supabase import create_client, Client

from .routes import api_bp


def create_app(config_class=None) -> Flask:
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)

    # --- 1. Configure Logging ---
    log_file = "backend.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)

    stream_handler = StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    stream_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info("CV Analyzer backend starting up...")

    # --- 2. Initialize Supabase Client ---
    try:
        url: str = config("SUPABASE_URL")
        key: str = config("SUPABASE_KEY")

        # Initialize the Supabase client
        supabase: Client = create_client(url, key)

        # Attach the client to the app instance so we can access it anywhere
        app.supabase = supabase

        app.logger.info("Supabase client initialized successfully.")
    except Exception as e:
        app.logger.error(f"CRITICAL: Failed to initialize Supabase client: {e}")

    # --- 3. Configure CORS ---
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    app.logger.info("CORS configured to allow requests from http://localhost:3000")

    # --- 4. Register Blueprints ---
    ### CHANGED ###
    app.register_blueprint(api_bp, url_prefix="/api")
    app.logger.info("API blueprint registered.")

    @app.route("/health")
    def health_check():
        """A simple health check endpoint to confirm the app is running."""
        return "OK", 200

    return app
