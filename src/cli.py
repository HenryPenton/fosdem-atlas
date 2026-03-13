"""CLI for FOSDEM Explorer."""

import argparse
import sys


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FOSDEM Explorer - Schedule scraper and viewer",
        prog="fosdem-explorer",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape the FOSDEM schedule")
    scrape_parser.add_argument(
        "--url",
        default="https://fosdem.org/2026/schedule/xml",
        help="URL of the schedule XML (default: FOSDEM 2026)",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the web server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.command == "scrape":
        return cmd_scrape(args)
    elif args.command == "serve":
        return cmd_serve(args)
    else:
        parser.print_help()
        return 0


def cmd_scrape(args: argparse.Namespace) -> int:
    """Run the scraper."""
    from db.connection import close_connection
    from db.events import insert_events
    from scraper.fosdem import scrape

    print(f"Fetching schedule from {args.url}...")

    try:
        events = scrape(args.url)
        print(f"Found {len(events)} events")

        # Save to database
        print("Saving to database...")
        count = insert_events(events)
        print(f"Saved {count} events to database")

        # Group by day
        days: dict[str, int] = {}
        tracks: set[str] = set()
        rooms: set[str] = set()

        for event in events:
            days[event.day] = days.get(event.day, 0) + 1
            tracks.add(event.track)
            rooms.add(event.room)

        print(f"Days: {len(days)}")
        for day, count in sorted(days.items()):
            print(f"  {day}: {count} events")

        print(f"Tracks: {len(tracks)}")
        print(f"Rooms: {len(rooms)}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        close_connection()


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the web server."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
