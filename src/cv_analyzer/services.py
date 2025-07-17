# src/cv_analyzer/services.py

import logging
from typing import List, Dict, Any, Tuple
from supabase import Client


def get_ranked_resume_matches(
    keywords: List[str], supabase: Client
) -> List[Dict[str, Any]]:
    """
    Core business logic to fetch, score, and rank resumes against keywords.
    """
    logger: logging.Logger = logging.getLogger(__name__)

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

    scored_matches = []
    for resume_data in response.data:
        score = 0
        resume_text_lower = (resume_data.get("resume_text") or "").lower()

        for keyword in keywords:
            score += resume_text_lower.count(keyword)

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

    if not scored_matches:
        logger.info("No matches found for the given keywords.")
        return []

    sorted_matches = sorted(scored_matches, key=lambda x: x["score"], reverse=True)

    logger.info(
        f"Found {len(sorted_matches)} matches. Top score: {sorted_matches[0]['score']}"
    )

    return sorted_matches


def get_paginated_candidates(
    supabase: Client, page: int, limit: int, search_term: str, category: str
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetches a paginated, searchable, and filterable list of all candidates.
    """
    logger: logging.Logger = logging.getLogger(__name__)

    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Start building the query
    query = supabase.table("candidates").select("*, resumes(*)", count="exact")

    # Apply category filter if it's not 'all'
    if category != "all":
        # We need to filter on the joined 'resumes' table
        query = query.eq("resumes.category", category)

    # Apply search term filter if provided
    if search_term:
        # Search across multiple fields: full_name, email, and resume_text
        # The syntax is or(filter1, filter2, ...)
        query = query.or_(
            f"full_name.ilike.%{search_term}%,"
            f"email.ilike.%{search_term}%,"
            f"resumes.resume_text.ilike.%{search_term}%"
        )

    # Apply pagination and ordering
    query = query.range(offset, offset + limit - 1).order("created_at", desc=True)

    # Execute the query
    response = query.execute()

    if not response.data:
        return [], 0

    # The total count is returned in the 'count' attribute of the response
    total_count = response.count
    candidates = response.data

    logger.info(
        f"Fetched {len(candidates)} candidates for page {page} with total count {total_count}."
    )

    return candidates, total_count
