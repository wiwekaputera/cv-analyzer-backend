# src/cv_analyzer/routes.py

import logging
from flask import Blueprint, request, jsonify, current_app
from pydantic import BaseModel, ValidationError, Field
from typing import List

from . import services


# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    keywords: List[str]
    limit: int = Field(default=5, gt=0, le=100)


# --- Blueprint ---
api_bp: Blueprint = Blueprint("api_bp", __name__)


# --- API Routes ---
@api_bp.route("/analyze", methods=["POST"])
def analyze_resumes():
    # ... (existing analyze_resumes function remains here) ...
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("Received request for /api/analyze")

    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "Request body must be JSON"}), 400

        validated_data = AnalyzeRequest(**json_data)
        keywords = [kw.lower() for kw in validated_data.keywords]
        limit = validated_data.limit
        logger.info(
            f"Analysis request validated for keywords: {keywords}, limit: {limit}"
        )

    except ValidationError as e:
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400

    try:
        matches = services.get_ranked_resume_matches(keywords, current_app.supabase)
        limited_matches = matches[:limit]
        final_response = []
        for i, match in enumerate(limited_matches):
            match["rank"] = i + 1
            final_response.append(match)
        return jsonify({"matches": final_response}), 200
    except Exception as e:
        logger.exception("An error occurred during the analysis process.")
        return jsonify({"error": "An internal error occurred during analysis."}), 500


# --- NEW ROUTE ADDED ---
@api_bp.route("/candidates", methods=["GET"])
def get_all_candidates():
    """
    Provides a paginated and searchable list of all candidates.
    Accepts query parameters: page, limit, search, category.
    """
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("Received request for /api/candidates")

    try:
        # Get query parameters from the URL, with defaults
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 12))
        search_term = request.args.get("search", "")
        category = request.args.get("category", "all")

        # Call the service layer to get the data
        candidates, total_count = services.get_paginated_candidates(
            current_app.supabase, page, limit, search_term, category
        )

        return (
            jsonify(
                {
                    "candidates": candidates,
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                }
            ),
            200,
        )

    except Exception as e:
        logger.exception("An error occurred while fetching candidates.")
        return jsonify({"error": "An internal error occurred."}), 500
