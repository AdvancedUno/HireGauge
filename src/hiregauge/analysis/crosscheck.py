import re

def crosscheck_claims(profile: dict) -> list[str]:
    """
    Compares resume text claims against fetched hard signals.
    Returns human-readable discrepancy strings (red flags).
    Must be best-effort (never raise, return [] on error/missing).
    """
    discrepancies = []
    
    if not profile or not isinstance(profile, dict):
        return discrepancies
        
    resume_text = profile.get("resume_text", "")
    if not resume_text:
        return discrepancies
        
    try:
        # Check star inflation
        # Find claims like "1000+ GitHub stars" or "500 stars"
        star_claim_match = re.search(r'(\d+)[k\+]?\s*(?:github\s*)?stars', resume_text, re.IGNORECASE)
        if star_claim_match:
            claimed_stars = int(star_claim_match.group(1))
            # Handle 'k' notation roughly
            if 'k' in star_claim_match.group(0).lower():
                claimed_stars *= 1000
                
            github_data = profile.get("github_data", {})
            if github_data and isinstance(github_data, dict):
                repos = github_data.get("repositories", [])
                max_stars = max([r.get("stargazers_count", 0) for r in repos]) if repos else 0
                
                # If claimed is significantly higher than fetched max (e.g., claimed 1000, fetched 12)
                if claimed_stars > max_stars * 2 and claimed_stars > 50:
                    discrepancies.append(f"Resume claims ~{claimed_stars} GitHub stars, but fetched max stars across owned repos is {max_stars}.")

        # Check phantom publications
        # Find claims about papers/authorship
        pub_keywords = ['publication', 'neurips', 'icml', 'cvpr', 'first-author', 'paper accepted']
        claims_pubs = any(kw in resume_text.lower() for kw in pub_keywords)
        
        if claims_pubs:
            pub_data = profile.get("publications", [])
            # If resume claims publications but fetched profile has none
            if not pub_data:
                # We only flag if we explicitly tried to fetch and got 0 (not if we skipped fetching)
                if "publications_fetched" in profile and profile["publications_fetched"] is True:
                    discrepancies.append("Resume claims publications/authorship, but fetched external profile shows zero papers.")
                    
    except Exception:
        # Best effort, fail silently
        pass
        
    return discrepancies
