import argparse

from job_pipeline import gmail_client, pipeline


def main():
    parser = argparse.ArgumentParser(prog = "jobs",description="Run the job pipeline.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth", help="Authenticate with Gmail and save the token.")
    run = sub.add_parser("run", help="Run the job pipeline to fetch, parse, filter, and store job postings.")
    run.add_argument("--days", type=int, help="Override 7 days lookback")

    args = parser.parse_args()
    if args.command == "auth":
        gmail_client.connect(interactive=True)
        print("Gmail token saved.")
        
    elif args.command == "run":
        pipeline.run(days=args.days)


if __name__ == "__main__":
    main()    

