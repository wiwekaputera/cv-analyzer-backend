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

    if category != "all":
        logger.info(f"Applying category filter for: '{category}'")

        # Query resumes table with category filter, then join candidates
        query = (
            supabase.table("resumes")
            .select(
                "id, category, pdf_url, resume_text, created_at, candidates(id, full_name, email, phone_number, created_at)"
            )
            .eq("category", category)
        )

        # Apply search if provided
        if search_term and search_term.strip():
            logger.info(f"Applying search filter for: '{search_term}'")
            query = query.ilike("candidates.full_name", f"%{search_term}%")

        # Get ALL results first (without pagination) to count unique candidates
        all_response = query.execute()

        if not all_response.data:
            return [], 0

        # Count unique candidates
        unique_candidate_ids = set()
        all_candidates = []

        for item in all_response.data:
            candidate_data = item.get("candidates", {})
            if candidate_data:
                candidate_id = candidate_data.get("id")
                if candidate_id not in unique_candidate_ids:
                    unique_candidate_ids.add(candidate_id)
                    all_candidates.append(
                        {
                            "id": candidate_data.get("id"),
                            "full_name": candidate_data.get("full_name"),
                            "email": candidate_data.get("email"),
                            "phone_number": candidate_data.get("phone_number"),
                            "created_at": candidate_data.get("created_at"),
                            "resumes": [
                                {
                                    "id": item.get("id"),
                                    "category": item.get("category"),
                                    "pdf_url": item.get("pdf_url"),
                                    "resume_text": item.get("resume_text"),
                                    "created_at": item.get("created_at"),
                                }
                            ],
                        }
                    )

        # Now apply pagination to unique candidates
        total_count = len(all_candidates)
        candidates = all_candidates[offset : offset + limit]

    else:
        # Query candidates table normally
        query = supabase.table("candidates").select(
            "id, full_name, email, phone_number, created_at, resumes(id, category, pdf_url, resume_text, created_at)",
            count="exact",
        )

        # Apply search if provided
        if search_term and search_term.strip():
            logger.info(f"Applying search filter for: '{search_term}'")
            query = query.ilike("full_name", f"%{search_term}%")

        # Apply pagination and ordering
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)

        response = query.execute()

        if not response.data:
            return [], 0

        total_count = response.count or 0
        candidates = response.data

    logger.info(
        f"Fetched {len(candidates)} candidates for page {page} with total count {total_count}."
    )
    return candidates, total_count
