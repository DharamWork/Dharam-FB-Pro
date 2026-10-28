#!/usr/bin/env python3
"""
scripts/exchange_tokens.py
Exchanges a short-lived Meta User Access Token for a Long-Lived Token,
and retrieves Permanent Page Access Tokens for all managed pages.
"""

import os
import json
import argparse
import requests

GRAPH_API = "https://graph.facebook.com/v20.0"


def exchange_user_token(app_id: str, app_secret: str, short_lived_token: str) -> str:
    """Exchanges a short-lived user token for a 60-day long-lived user token."""
    url = f"{GRAPH_API}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token
    }
    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Failed to exchange user token: {data['error'].get('message')}")
    return data["access_token"]


def get_permanent_page_tokens(long_lived_user_token: str) -> dict:
    """Fetches permanent page access tokens for all pages the user administers."""
    url = f"{GRAPH_API}/me/accounts"
    params = {
        "access_token": long_lived_user_token,
        "fields": "id,name,access_token",
        "limit": 100
    }
    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Failed to fetch page tokens: {data['error'].get('message')}")

    tokens = {}
    for page in data.get("data", []):
        tokens[page["id"]] = {
            "name": page["name"],
            "access_token": page["access_token"]
        }
    return tokens


def main():
    parser = argparse.ArgumentParser(description="Exchange Meta Tokens and retrieve permanent Page Access Tokens")
    parser.add_argument("--app-id", required=True, help="Meta Developer App ID")
    parser.add_argument("--app-secret", required=True, help="Meta Developer App Secret")
    parser.add_argument("--user-token", required=True, help="Short-lived User Token from Graph API Explorer")
    parser.add_argument("--out", default="data/pages_tokens.json", help="Output path for tokens JSON")
    args = parser.parse_args()

    print(f"[*] Exchanging short-lived user token for App ID {args.app_id}...")
    long_lived_token = exchange_user_token(args.app_id, args.app_secret, args.user_token)
    print("[+] Long-lived token acquired successfully.")

    print("[*] Retrieving permanent Page Access Tokens...")
    page_tokens = get_permanent_page_tokens(long_lived_token)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(page_tokens, f, indent=2)

    print(f"[+] Saved {len(page_tokens)} page tokens to '{args.out}'.")
    for pid, pdata in page_tokens.items():
        print(f"    - {pdata['name']} (ID: {pid}): Token starts with {pdata['access_token'][:15]}...")


if __name__ == "__main__":
    main()
