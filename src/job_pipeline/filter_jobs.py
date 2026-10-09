import re
import unicodedata

from job_pipeline.models import JobCard


def filter_jobs(
    cards: list[JobCard], exclusions: dict
) -> tuple[list[JobCard], list[tuple[JobCard, str]]]:
    """Split cards into kept and dropped (with the reason each was dropped)."""
    company_re = _pattern(exclusions["companies"])
    title_re = _pattern(exclusions["title_keywords"])

    kept, dropped, seen_roles = [], [], set()
    for card in cards:
        company, title = _normalize_text(card.company), _normalize_text(card.title)

        if m := company_re.search(company):
            dropped.append((card, f"company: {m.group(1)}"))
        elif m := title_re.search(title):
            dropped.append((card, f"title: {m.group(1)}"))
        elif (title, company) in seen_roles:
            dropped.append((card, "repost"))
        else:
            seen_roles.add((title, company))
            kept.append(card)
    return kept, dropped

def _normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and converting to lowercase."""
    text = unicodedata.normalize("NFKC", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _pattern(terms: list[str]) -> re.Pattern:
    """One regex matching any term as a whole word."""
    alts = "|".join(re.escape(_normalize_text(t)) for t in terms)
    return re.compile(rf"(?<!\w)({alts})(?!\w)")


