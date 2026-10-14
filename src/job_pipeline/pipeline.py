from job_pipeline import gmail_client, linkedin_client, store
from job_pipeline.config import load_configs, load_exclusions
from job_pipeline.email_parser import parse_emails
from job_pipeline.filter_jobs import filter_jobs


def run(days: int | None = None, interactive: bool = False) -> None:
    """Run the job pipeline to fetch, parse, filter, and store job postings."""
    # Load configurations and exclusions
    
    s = load_configs()["gmail"]
    days = days or s["lookback_days"]
    gmail = gmail_client.connect(interactive=interactive)

    alert_emails = gmail_client.fetch_alert_emails(gmail, s["senders"], 
                                                   s["exclude_subjects"], s["lookback_days"])

    cards = parse_emails(alert_emails)

    conn = store.connect()
    seen = store.seen_jobs(conn)

    new_cards = [card for card in cards if card.job_id not in seen]

    exclusions = load_exclusions()
    kept, dropped = filter_jobs(new_cards, exclusions)
    store.add_jobs(conn, kept, status="new")
    store.add_jobs(conn, [card for card, _ in dropped], 
                    status="dropped", reason=[reason for _, reason in dropped])

    print(f"{len(alert_emails)} emails | {len(cards)} jobs | "
          f"{len(cards) - len(new_cards)} already seen | "
          f"{len(kept)} kept | {len(dropped)} dropped")
    for c in kept:
        print(f"  {c.company} | {c.title}")

    linkedin_cfg = load_configs()["linkedin"]
    fetched = linkedin_client.fetch_postings(conn, linkedin_cfg, interactive=interactive)
    print(f"Fetched {fetched} postings from LinkedIn.")