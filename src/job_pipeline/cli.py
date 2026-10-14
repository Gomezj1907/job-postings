import argparse

from job_pipeline import gmail_client, linkedin_client, pipeline
from job_pipeline.config import load_configs


def main():
    parser = argparse.ArgumentParser(prog = "jobs",description="Run the job pipeline.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth", help="Authenticate with Gmail and save the token.")
    sub.add_parser("login", help="Log in to LinkedIn (opens browser)")
    run = sub.add_parser("run", help="Run the job pipeline to fetch, parse, filter, and store job postings.")
    run.add_argument("--days", type=int, help="Override 7 days lookback")
    run.add_argument("--interactive", action="store_true",
                      help="Allow interactive prompts (e.g. for LinkedIn login)")
    

    args = parser.parse_args()
    if args.command == "auth":
        gmail_client.connect(interactive=True)
        print("Gmail token saved.")
        
    elif args.command == "run":
        pipeline.run(days=args.days, interactive=args.interactive)

    elif args.command == "login":
        linkedin_client.login(load_configs()["linkedin"])


if __name__ == "__main__":
    main()    

