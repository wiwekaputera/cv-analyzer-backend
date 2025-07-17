# src/cv_analyzer/services.py

import logging
from typing import List, Dict, Any
from supabase import Client


def get_ranked_resume_matches(
    keywords: List[str], supabase: Client
) -> List[Dict[str, Any]]:
    """
    Core business logic to fetch, score, and rank resumes against keywords.

    Args:
        keywords: A list of lowercase keywords to search for.
        supabase: An initialized Supabase client instance.

    Returns:
        A sorted list of candidate matches, each as a dictionary.
    """
    logger: logging.Logger = logging.getLogger(__name__)

    # --- 1. Fetch all resumes and their associated candidate data ---
    # The 'candidates(*)' syntax tells Supabase to perform a JOIN.
    response = (
        supabase.table("resumes")
        .select("resume_text, pdf_url, candidates(id, full_name, email, phone_number)")
        .limit(3000)
        .execute()
    )

    if not response.data:
        logger.warning("No resumes found in the database to analyze.")
        return []

    logger.info(f"Successfully fetched {len(response.data)} resumes for analysis.")

    # --- 2. Score each resume based on keyword occurrences ---
    scored_matches = []
    for resume_data in response.data:
        score = 0
        # Ensure resume_text is not None before calling .lower()
        resume_text_lower = (resume_data.get("resume_text") or "").lower()

        for keyword in keywords:
            score += resume_text_lower.count(keyword)

        # Only include resumes that have a score greater than 0
        if score > 0:
            candidate_info = resume_data.get("candidates")
            if candidate_info:
                scored_matches.append(
                    {
                        "score": score,
                        "candidate": candidate_info,
                        "resume": {"pdf_url": resume_data.get("pdf_url")},
                    }
                )

    # --- 3. Sort the results by score in descending order ---
    # Add a check to ensure scored_matches is not empty before sorting/accessing
    if not scored_matches:
        logger.info("No matches found for the given keywords.")
        return []

    sorted_matches = sorted(scored_matches, key=lambda x: x["score"], reverse=True)

    logger.info(
        f"Found {len(sorted_matches)} matches. Top score: {sorted_matches[0]['score']}"
    )

    return sorted_matches
