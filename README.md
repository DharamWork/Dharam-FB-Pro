# 🚀 Dharam FB Pro - Facebook Reels & Video Automation Fleet

> **100% Cloud-Operated Google Drive to Facebook Reels Automation Engine with Mobile PWA Command Center.**

---

## 🌟 Key Architecture & Highlights

1. **Zero-PC Runtime:** You only drop videos into Google Drive folders. Your PC does not need to stay on. GitHub Actions cloud runners handle all posting automatically.
2. **Strict Page Isolation:** Every Facebook page has its own Drive folder, its own daily limit, and its own row in the database. A failure on one page never stops or affects other pages.
3. **Smart Aspect Ratio & Duration Routing:**
   - **Reels Route:** `3s to 90s` and `Vertical (9:16)` ➔ Meta Graph API (`/{page_id}/video_reels`)
   - **Classic Video Route:** `> 90s` or Horizontal ➔ Meta Graph API (`/{page_id}/videos`)
4. **Duplicate Guard:** SQLite database (`data/posted_videos.db` in WAL mode) strictly ensures no video is ever uploaded twice.
5. **Mobile PWA App ("Raj FB Pro"):** Obsidian & Gold themed web app hosted on GitHub Pages (`docs/`). Supports **Add to Home Screen** on Android and iPhone with zero hosting cost.

---

## 📁 Project Structure

```text
Fb Auto Pro/
├── .github/workflows/
│   ├── post.yml                  # USA Fleet posting cron (4x daily)
│   ├── uk_london_post.yml        # UK Fleet posting cron (staggered)
│   └── sync_views.yml            # 2-Hourly real-time dashboard analytics sync
├── config.yaml                   # Master configuration
├── config_uk_account1.yaml       # UK regional configuration
├── config_usa_account1.yaml      # USA regional configuration
├── data/
│   ├── posted_videos.db         # Persistent SQLite database (WAL mode)
│   ├── upload_history.json      # Upload events log
│   └── pages_tokens.json        # Permanent Page Tokens dictionary
├── docs/                         # GitHub Pages PWA Root
│   ├── .nojekyll
│   ├── manifest.json             # PWA Manifest
│   ├── index.html                # PWA Dashboard (All 8 modules)
│   ├── privacy.html              # Meta compliance Privacy Policy
│   ├── data-deletion.html        # Meta compliance Data Deletion
│   ├── css/gold_dashboard.css    # Luxe Obsidian & Gold theme
│   ├── js/app.js                 # UI controllers
│   ├── js/sync_service.js        # Live sync service
│   ├── icons/                    # App icons (192x192, 512x512)
│   └── data/pages_data.json      # Live payload for dashboard
├── scripts/
│   ├── exchange_tokens.py        # Token exchange tool
│   ├── sync_dashboard_data.py    # Pulls Meta & Drive stats
│   ├── connect_wireguard_uk.sh   # WireGuard UK VPN connector
│   ├── connect_wireguard_usa.sh  # WireGuard USA VPN connector
│   ├── audit_uploads_and_slots.py# Health & gap diagnostic
│   └── validate_config.py        # Pre-flight YAML validator
├── src/
│   ├── config.py                 # Pydantic validation models
│   ├── db.py                     # SQLite WAL manager & duplicate guard
│   ├── drive_client.py           # Google Drive Service Account client (FIFO)
│   ├── facebook_client.py        # Meta Graph API Reels & Video client
│   ├── page_runner.py            # Isolated per-page execution engine
│   ├── retry.py                  # Exponential backoff decorator
│   └── video_utils.py            # FFprobe probing & 9:16 aspect ratio detection
├── tests/                        # Full automated test suite (pytest)
├── dashboard_server.py           # Local PWA preview server (http://localhost:8080)
├── main.py                       # CLI execution entrypoint
└── requirements.txt              # Python dependencies
```

---

## ⚡ Quick Start & Verification

### 1. Run Unit Tests
```bash
.venv\Scripts\pytest.exe -v
```

### 2. Validate Configuration
```bash
.venv\Scripts\python.exe scripts/validate_config.py config.yaml
```

### 3. Run Dry-Run Simulation (No video posted, DB safe)
```bash
.venv\Scripts\python.exe main.py --dry-run
```

### 4. Preview the Mobile PWA App Locally
```bash
.venv\Scripts\python.exe dashboard_server.py
```
Open **`http://localhost:8080`** in your browser.

---

## 🔐 Credentials & Cloud Deployment Setup

### Step A: Connect Git & Push to GitHub
1. Create a private GitHub repository.
2. Initialize git and push:
   ```bash
   git init
   git branch -M main
   git remote add origin <YOUR_GITHUB_REPO_URL>
   git add .
   git commit -m "feat: complete FB Auto Pro engine and PWA dashboard"
   git push -u origin main
   ```
3. Enable GitHub Pages:
   - Go to **Settings ➔ Pages**
   - Source: **Deploy from a branch** ➔ Branch: `main`, Folder: `/docs`.

### Step B: Connect Google Cloud & Google Drive
1. Place your Google Cloud Service Account JSON file as **`service_account.json`** in this project root.
2. Share each page's Google Drive folder with your service account email (`Viewer` role).
3. Update `drive_folder_id` in `config.yaml`.
4. In GitHub Repo Settings ➔ **Secrets and variables ➔ Actions**, add secret:
   - `GDRIVE_SERVICE_ACCOUNT_JSON`: Paste entire contents of `service_account.json`.

### Step C: Connect Meta Developer App & Page Tokens
1. Ensure Meta Developer App is toggled to **"Live" Mode** (required to prevent 0-views suppression).
2. Generate permanent page tokens using:
   ```bash
   .venv\Scripts\python.exe scripts/exchange_tokens.py --app-id <APP_ID> --app-secret <APP_SECRET> --user-token <USER_TOKEN>
   ```
3. Add permanent tokens to `config.yaml` or GitHub Secret `FB_PAGE_ACCESS_TOKEN`.
