#!/usr/bin/env python3
"""
scripts/github_manager.py
Automated GitHub Manager:
Enables Antigravity to manage repository secrets, trigger workflows, and check run status
completely autonomously via GitHub REST API. Zero manual user visits to GitHub required.
"""

import os
import sys
import json
import base64
import requests
from nacl import encoding, public

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GITHUB_OWNER = "DharamWork"
GITHUB_REPO = "Dharam-FB-Pro"


def _get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN="):
                    return line.strip().split("=", 1)[1].strip()
    return ""


GITHUB_TOKEN = _get_github_token()
API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"


def _get_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Dharam-FB-Pro-Manager"
    }


def get_public_key():
    url = f"{API_BASE}/actions/secrets/public-key"
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch public key (HTTP {resp.status_code}): {resp.text}")
    return resp.json()


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def set_github_secret(secret_name: str, secret_value: str):
    """Encrypts and sets a repository secret on GitHub Actions."""
    key_info = get_public_key()
    key_id = key_info["key_id"]
    public_key = key_info["key"]

    encrypted_val = encrypt_secret(public_key, secret_value)

    url = f"{API_BASE}/actions/secrets/{secret_name}"
    payload = {
        "encrypted_value": encrypted_val,
        "key_id": key_id
    }
    resp = requests.put(url, headers=_get_headers(), json=payload, timeout=30)
    if resp.status_code in [201, 204]:
        print(f"[✔] GitHub Secret '{secret_name}' successfully set autonomously!")
        return True
    else:
        print(f"[-] Failed to set secret '{secret_name}' (HTTP {resp.status_code}): {resp.text}")
        return False


def list_secrets():
    url = f"{API_BASE}/actions/secrets"
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    if resp.status_code == 200:
        secrets = resp.json().get("secrets", [])
        print(f"Active Secrets on {GITHUB_OWNER}/{GITHUB_REPO}: {len(secrets)}")
        for s in secrets:
            print(f"  🔒 {s['name']} (Updated: {s.get('updated_at')})")
        return [s["name"] for s in secrets]
    return []


def trigger_workflow(workflow_filename: str, ref: str = "main", inputs: dict = None):
    url = f"{API_BASE}/actions/workflows/{workflow_filename}/dispatches"
    payload = {"ref": ref}
    if inputs:
        payload["inputs"] = inputs

    resp = requests.post(url, headers=_get_headers(), json=payload, timeout=30)
    if resp.status_code == 204:
        print(f"[✔] Successfully triggered workflow '{workflow_filename}'!")
        return True
    else:
        print(f"[-] Failed to trigger workflow (HTTP {resp.status_code}): {resp.text}")
        return False


def get_recent_runs(limit: int = 5):
    url = f"{API_BASE}/actions/runs?per_page={limit}"
    resp = requests.get(url, headers=_get_headers(), timeout=30)
    if resp.status_code == 200:
        runs = resp.json().get("workflow_runs", [])
        print(f"Recent Workflow Runs on {GITHUB_OWNER}/{GITHUB_REPO}:")
        for r in runs:
            status = r.get("status")
            conclusion = r.get("conclusion") or "running"
            name = r.get("name")
            run_id = r.get("id")
            html_url = r.get("html_url")
            print(f"  • [{status.upper()}:{conclusion}] {name} (ID: {run_id}) -> {html_url}")
        return runs
    else:
        print(f"[-] Failed to fetch runs (HTTP {resp.status_code}): {resp.text}")
        return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous GitHub Manager")
    parser.add_argument("--set-secret", nargs=2, metavar=("NAME", "VALUE"), help="Set repository secret")
    parser.add_argument("--list-secrets", action="store_true", help="List active repository secrets")
    parser.add_argument("--trigger", help="Workflow filename to trigger (e.g. post.yml)")
    parser.add_argument("--dry-run", action="store_true", help="Pass dry_run=true to triggered workflow")
    parser.add_argument("--runs", action="store_true", help="List recent workflow runs")
    args = parser.parse_args()

    if args.set_secret:
        set_github_secret(args.set_secret[0], args.set_secret[1])
    elif args.list_secrets:
        list_secrets()
    elif args.trigger:
        inputs = {"dry_run": "true"} if args.dry_run else None
        trigger_workflow(args.trigger, inputs=inputs)
    elif args.runs:
        get_recent_runs()
    else:
        list_secrets()
