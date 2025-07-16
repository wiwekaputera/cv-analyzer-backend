# run.py

from src.cv_analyzer import create_app
from logging import getLogger, Logger
from flask import Flask

# Create the Flask app instance using the application factory
app: Flask = create_app()

if __name__ == "__main__":
    # Get Logger instance
    logger: Logger = getLogger(__name__)
    logger.info("Starting development server at http://localhost:5000")

    # Run the app
    app.run(host="0.0.0.0", port=5000, debug=True)
