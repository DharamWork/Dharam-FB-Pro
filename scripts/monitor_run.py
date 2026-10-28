import os
import sys
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.github_manager import _get_headers, API_BASE

runs_url = f"{API_BASE}/actions/workflows/post.yml/runs?per_page=1"
resp = requests.get(runs_url, headers=_get_headers()).json()
runs = resp.get("workflow_runs", [])
if not runs:
    print("No runs found!")
    exit(0)

r = runs[0]
run_id = r["id"]
print(f"Tracking Live Run ID: {run_id} | Created: {r.get('created_at')}")

for cycle in range(30):
    time.sleep(5)
    run_info = requests.get(f"{API_BASE}/actions/runs/{run_id}", headers=_get_headers()).json()
    status = run_info.get("status")
    conclusion = run_info.get("conclusion")

    jobs_info = requests.get(f"{API_BASE}/actions/runs/{run_id}/jobs", headers=_get_headers()).json()
    active_step = "None"
    for job in jobs_info.get("jobs", []):
        for s in job.get("steps", []):
            if s.get("status") == "in_progress":
                active_step = s.get("name")
            elif s.get("status") == "completed" and s.get("conclusion") == "failure":
                active_step = f"FAILED: {s.get('name')}"

    print(f"[{cycle*5+5}s] Status: {status} | Conclusion: {conclusion} | Step: {active_step}")

    if status == "completed":
        print(f"===> FINAL RUN RESULT: {conclusion}")
        break
