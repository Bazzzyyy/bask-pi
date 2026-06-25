"""One-shot Google Calendar OAuth (run on Pi with display or SSH -L)."""

from argparse import ArgumentParser
from pathlib import Path

from bask.calendar.gcal import get_credentials


def main() -> None:
    p = ArgumentParser()
    p.add_argument("--client-secret", type=Path, default=Path("secrets/google_client_secret.json"))
    p.add_argument("--token", type=Path, default=Path("secrets/google_token.json"))
    args = p.parse_args()
    get_credentials(args.client_secret, args.token)
    print("Saved token to", args.token)


if __name__ == "__main__":
    main()
