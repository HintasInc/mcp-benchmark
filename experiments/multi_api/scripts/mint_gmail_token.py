#!/usr/bin/env python3
"""
mint_gmail_token.py — issue a Gmail refresh token for a multi-API stack.

Runs the OAuth 2.0 "Desktop app" installed-app flow once: opens a browser,
you sign in as the stack's mailbox owner (the agent's Gmail mailbox) and grant the
scopes, and it prints the refresh token to paste into experiments/multi_api/.env
as BASELINE_GMAIL_TOKEN / HINTAS_GMAIL_TOKEN.

Prerequisites (one-time, per stack — see experiments/gmail/IMPLEMENTATION.md §2):
  * Gmail API enabled in the Google Cloud project.
  * An OAuth client of type "Desktop app" (its id/secret are the
    BASELINE_/HINTAS_GMAIL_CLIENT_ID/_SECRET env vars).
  * On the OAuth consent screen, add the mailbox account as a Test user — this
    keeps the app in Testing mode WITHOUT the 7-day refresh-token expiry that
    otherwise causes `invalid_grant`. (Or publish the app.)

Usage:
    # credentials from the stack's env vars (BASELINE_/HINTAS_GMAIL_CLIENT_ID/_SECRET):
    uv run python experiments/multi_api/scripts/mint_gmail_token.py --stack baseline

    # or from a downloaded client JSON:
    uv run python experiments/multi_api/scripts/mint_gmail_token.py --stack hintas \
        --client-json ~/Downloads/client_secret_xxx.json

Must be run on a machine with a browser (it serves a localhost redirect).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import add_stack_arg, stack_env, STACK_ENV_PREFIX, err, section

# Match experiments/gmail/scripts/utils.py SCOPES so the token covers everything
# the seed/reset scripts and the prompts may exercise (core + extension).
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.metadata",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Mint a Gmail refresh token for a multi-API stack")
    parser.add_argument("--client-id", help="OAuth client id (else BASELINE_/HINTAS_GMAIL_CLIENT_ID)")
    parser.add_argument("--client-secret", help="OAuth client secret (else BASELINE_/HINTAS_GMAIL_CLIENT_SECRET)")
    parser.add_argument("--client-json", help="Path to a downloaded OAuth client JSON (alternative to id/secret)")
    parser.add_argument("--port", type=int, default=0, help="Localhost redirect port (default: random free port)")
    add_stack_arg(parser)
    args = parser.parse_args()

    from google_auth_oauthlib.flow import InstalledAppFlow

    if args.client_json:
        flow = InstalledAppFlow.from_client_secrets_file(args.client_json, scopes=SCOPES)
    else:
        client_id = args.client_id or stack_env(args.stack, "GMAIL_CLIENT_ID")
        client_secret = args.client_secret or stack_env(args.stack, "GMAIL_CLIENT_SECRET")
        prefix = STACK_ENV_PREFIX[args.stack]
        if not client_id or not client_secret:
            err(f"Provide --client-json, or --client-id/--client-secret, or set "
                f"{prefix}GMAIL_CLIENT_ID and {prefix}GMAIL_CLIENT_SECRET.")
            return 1
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)

    section(f"Minting Gmail refresh token for stack '{args.stack}'")
    print("  A browser window will open. Sign in as the mailbox owner for this")
    print("  stack and accept all requested scopes.\n")

    # access_type=offline + prompt=consent guarantees a refresh token is returned
    # even if this account previously authorized the client.
    creds = flow.run_local_server(
        port=args.port,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    var = f"{STACK_ENV_PREFIX[args.stack]}GMAIL_TOKEN"
    print(f"\n{'=' * 60}")
    if creds.refresh_token:
        print("  Refresh token minted. Add this line to experiments/multi_api/.env:\n")
        print(f"  {var}={creds.refresh_token}\n")
        print("  Then verify:  uv run python experiments/multi_api/scripts/seed_gmail.py "
              f"--stack {args.stack} --verify")
    else:
        print("  No refresh token returned. Revoke prior access at")
        print("  https://myaccount.google.com/permissions and re-run.")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
