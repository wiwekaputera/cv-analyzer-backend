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
    logger.info(
        f"Getting candidates - page: {page}, limit: {limit}, search: '{search_term}', category: '{category}'"
    )

    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Start building the query
    query = supabase.table("candidates").select("*, resumes(*)", count="exact")

    # Apply search term filter if provided
    if search_term and search_term.strip():
        logger.info(f"Applying search filter for: '{search_term}'")
        # Correct Supabase syntax for OR conditions
        query = query.or_(
            f"full_name.ilike.%{search_term}%," f"email.ilike.%{search_term}%"
        )

    # Apply category filter if it's not 'all'
    if category != "all":
        logger.info(f"Applying category filter for: '{category}'")
        query = query.eq("resumes.category", category)

    # Apply pagination and ordering
    query = query.range(offset, offset + limit - 1).order("created_at", desc=True)

    # Execute the query
    response = query.execute()

    if not response.data:
        return [], 0

    total_count = response.count or 0
    candidates = response.data

    logger.info(
        f"Fetched {len(candidates)} candidates for page {page} with total count {total_count}."
    )

    return candidates, total_count
