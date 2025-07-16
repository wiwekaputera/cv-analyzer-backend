# src/cv_analyzer/routes.py

import logging
from flask import Blueprint, request, jsonify, current_app
from pydantic import BaseModel, ValidationError

# --- 1. Define Data Validation Models ---
class AnalyzeRequest(BaseModel):
    keywords: list[str]

# --- 2. Create the Blueprint ---
api_bp: Blueprint = Blueprint('api_bp', __name__)

# --- 3. Define API Routes ---
@api_bp.route('/analyze', methods=['POST'])
def analyze_resumes():
    """
    The core endpoint to analyze resumes based on keywords.
    Expects a JSON body with a "keywords" key, which is a list of strings.
    """
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("Received request for /api/analyze")

    # --- Request Validation ---
    try:
        # get_json() parses the incoming JSON request data and returns a Python dict
        json_data = request.get_json()
        if not json_data:
            logger.warning("Request received with no JSON body.")
            return jsonify({"error": "Request body must be JSON"}), 400
        
        # Validate the request body against our Pydantic model
        validated_data = AnalyzeRequest(**json_data)
        keywords = validated_data.keywords
        logger.info(f"Analysis request validated for keywords: {keywords}")

    except ValidationError as e:
        # If validation fails, Pydantic raises a ValidationError.
        logger.error(f"Request validation failed: {e}")
        # Return a helpful error message with the validation details.
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred during request parsing: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

    # --- Core Logic ---
    # Access the Supabase client attached to our app instance
    try:
        supabase = current_app.supabase
        
        # TODO: Implement the actual resume fetching and analysis logic here.
        # For now, we will just confirm we can query the database.
        
        # Example query: Fetch the first 5 resumes
        response = supabase.table('resumes').select("id, resume_text, pdf_url").limit(5).execute()
        
        logger.info(f"Successfully fetched {len(response.data)} resumes for analysis.")

        # Placeholder for the analysis results
        analysis_results = {
            "message": "Analysis logic not yet implemented.",
            "received_keywords": keywords,
            "sample_resumes_fetched": response.data
        }

        return jsonify(analysis_results), 200

    except Exception as e:
        logger.exception("An error occurred during the analysis process.")
        return jsonify({"error": "An internal error occurred during analysis."}), 500

