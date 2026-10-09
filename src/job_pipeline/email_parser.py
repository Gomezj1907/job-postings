import logging
import re

from job_pipeline.models import JobCard

log = logging.getLogger(__name__)

JOB_ID = re.compile(r"/jobs/view/(\d+)")
SOURCE = re.compile(r"trk=eml-email_([a-z_]+?)(?:_\d+)?-")
ALERT_NAME = re.compile(r"^Your job alert for (.+)$")
HEADER = re.compile(r"^(Your job alert for|A new job matches|New jobs match)")



def parse_emails(emails: list[dict]) -> list[JobCard]:
    """Parse all emails, keeping one card per job_id."""
    seen = {}
    for email in emails:
        for card in _parse_job_email(email):
            seen.setdefault(card.job_id, card)
    return list(seen.values())





def _parse_job_email(email: dict) -> list[JobCard]:
    """Parses a job alert email and extracts job information.

    Args:
        email: A dictionary containing email details, including 'body' and 'id'.
    """

    lines = [line.strip() for line in email["body"].splitlines()]

    alert_name = next(
        (m.group(1).strip() for line in lines if (m := ALERT_NAME.match(line))), None
    )

    cards, start = [], 0 
    for i, line in enumerate(lines):
        if line.startswith("View job:"):
            content = [ln for ln in lines[start:i] if ln and not HEADER.match(ln)]
            job_id = JOB_ID.search(line)
            if len(content) >= 3 and job_id:
                source = SOURCE.search(line)
                cards.append(
                    JobCard(
                        job_id=job_id.group(1),
                        title=content[0],
                        company=content[1],
                        location=content[2],
                        insights=tuple(content[3:]),
                        source=source.group(1) if source else "unknown",
                        alert_name=alert_name,
                        email_id=email["id"],
                    )
                )
            else: 
                log.warning("Not parsable card in email %s", email["id"])
                start = i + 1

        elif _is_boundary(line):
            start = i + 1
    return cards




def _is_boundary(line: str) -> bool:
    """Check if a line is a boundary line in the email content."""
    return line.startswith("---") or ("http" in line and not line.startswith("View job:"))



if __name__ == "__main__":
    from job_pipeline.config import load_configs
    from job_pipeline.gmail_client import connect, fetch_alert_emails
    s = load_configs()["gmail"]

    gmail = connect()
    alert_emails = fetch_alert_emails(gmail, s["senders"], s["exclude_subjects"], s["lookback_days"])

    cards = parse_emails(alert_emails)
    for card in cards:
        print(card.job_id, "|", card.title, "|", card.company, "|", card.location, "|", card.source, "|", card.alert_name)



