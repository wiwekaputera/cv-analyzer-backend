# src/cv_analyzer/routes.py

import logging
from flask import Blueprint, request, jsonify, current_app
from pydantic import BaseModel, ValidationError, Field
from typing import List

# Import our new services module
from . import services


# --- 1. Define Data Validation Models ---
class AnalyzeRequest(BaseModel):
    keywords: List[str]
    # Add the new 'limit' field. It's optional, defaults to 5,
    # and must be between 1 and 100.
    limit: int = Field(default=5, gt=0, le=100)


# --- 2. Create the Blueprint ---
api_bp: Blueprint = Blueprint("api_bp", __name__)


# --- 3. Define API Routes ---
@api_bp.route("/analyze", methods=["POST"])
def analyze_resumes():
    """
    The core endpoint to analyze resumes based on keywords.
    This function acts as a "controller". It handles the HTTP request/response
    and delegates the core business logic to the service layer.
    """
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("Received request for /api/analyze")

    # --- Request Validation ---
    try:
        json_data = request.get_json()
        if not json_data:
            logger.warning("Request received with no JSON body.")
            return jsonify({"error": "Request body must be JSON"}), 400

        validated_data = AnalyzeRequest(**json_data)
        keywords = [kw.lower() for kw in validated_data.keywords]
        limit = validated_data.limit
        logger.info(
            f"Analysis request validated for keywords: {keywords}, limit: {limit}"
        )

    except ValidationError as e:
        logger.error(f"Request validation failed: {e}")
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred during request parsing: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

    # --- Call Service Layer and Format Response ---
    try:
        # Delegate the heavy lifting to the service function
        matches = services.get_ranked_resume_matches(keywords, current_app.supabase)

        # Limit the number of results before adding the rank
        limited_matches = matches[:limit]

        final_response = []
        for i, match in enumerate(limited_matches):
            match["rank"] = i + 1
            final_response.append(match)

        return jsonify({"matches": final_response}), 200

    except Exception as e:
        logger.exception("An error occurred during the analysis process.")
        return jsonify({"error": "An internal error occurred during analysis."}), 500
