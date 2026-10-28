# 🚀 GOOGLE DRIVE TO FACEBOOK REELS AUTOMATION & MOBILE PWA APP (RAJ FB PRO)
## Master Replication Blueprint & Implementation Guide for Antigravity AI

> **DOCUMENT PURPOSE:**
> This document is an all-inclusive, zero-ambiguity architectural blueprint and execution roadmap. 
> When Antigravity opens this file on any new machine/workspace, it must execute this pipeline from A to Z with **100% precision, zero hallucinations, zero missing gaps, and zero glitches.**

---

## 📑 TABLE OF CONTENTS
1. [System Architecture & Working Philosophy](#1-system-architecture--working-philosophy)
2. [Exact Directory & Codebase Structure](#2-exact-directory--codebase-structure)
3. [The Phone App: UI/UX, Design Tokens & All 8 Modules](#3-the-phone-app-uiux-design-tokens--all-8-modules)
4. [Real-Time Data Sync Architecture](#4-real-time-data-sync-architecture)
5. [Step-by-Step Implementation Roadmap for Antigravity](#5-step-by-step-implementation-roadmap-for-antigravity)
   - [Phase 1: Environment & Scaffolding](#phase-1-environment--scaffolding)
   - [Phase 2: Google Cloud & Drive Setup](#phase-2-google-cloud--drive-setup)
   - [Phase 3: Meta App Live Mode & Token Pipeline](#phase-3-meta-app-live-mode--token-pipeline)
   - [Phase 4: SQLite Database & Duplicate Guard](#phase-4-sqlite-database--duplicate-guard)
   - [Phase 5: Core Upload & Routing Engine](#phase-5-core-upload--routing-engine)
   - [Phase 6: VPN / WireGuard & Anti-Ban Protection](#phase-6-vpn--wireguard--anti-ban-protection)
   - [Phase 7: GitHub Actions Cloud Automation](#phase-7-github-actions-cloud-automation)
   - [Phase 8: Building & Deploying the Phone App (PWA)](#phase-8-building--deploying-the-phone-app-pwa)
   - [Phase 9: Automated Testing & Verification](#phase-9-automated-testing--verification)
6. [User Fill-In Sheet (Plug-and-Play Credentials)](#6-user-fill-in-sheet-plug-and-play-credentials)

---

## 1. System Architecture & Working Philosophy

### 1.1 Core Philosophy
- **Zero-PC Runtime (100% Cloud-Operated):** The user's computer does **not** need to stay open, awake, or powered on for postings to occur. The PC is only used for dropping new videos into Google Drive.
- **Strict Isolation:** Every Facebook Page has its own designated Google Drive folder, its own daily upload quota, its own row in the tracking database, and its own configuration. A failure on one page never blocks or delays other pages.
- **Zero Cross-Posting:** A video file is posted strictly once to its designated page. Never duplicate, cross-post, or reuse files.
- **Smart Route Detection:** Video dimensions and length are inspected per-file at runtime:
  - **Reels Route:** `3 to 90 seconds` AND `Vertical 9:16 aspect ratio` ➔ Meta Graph API (`/{page_id}/video_reels`)
  - **Classic Video Route:** `> 90 seconds` ➔ Meta Graph API (`/{page_id}/videos`)

### 1.2 End-to-End Workflow Diagram

```text
┌────────────────────────────────────────────────────────┐
│ USER PC (Creator)                                     │
│ Drops AI/Viral videos into Google Drive synced folder  │
└──────────────────────────┬─────────────────────────────┘
                           │ (Google Drive Desktop Sync)
                           ▼
┌────────────────────────────────────────────────────────┐
│ GOOGLE CLOUD STORAGE                                   │
│ Individual Folder per Facebook Page                    │
└──────────────────────────┬─────────────────────────────┘
                           │ (Read by Service Account JSON)
                           ▼
┌────────────────────────────────────────────────────────┐
│ GITHUB ACTIONS CLOUD RUNNERS (Staggered Crons)         │
│ 1. Connect WireGuard / Regional Proxy (London/USA)     │
│ 2. Check SQLite Duplicate Guard (posted_videos.db)     │
│ 3. Download Next Video (FIFO Order - Oldest First)     │
│ 4. Probe Video (Aspect Ratio & Duration)               │
│ 5. Upload via Meta Graph API (Reel or Classic Video)   │
│ 6. Commit Updated SQLite State back to GitHub Repo     │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            ▼ (Every 2 Hours Auto-Sync)       ▼ (Direct API Call)
┌───────────────────────────────┐  ┌─────────────────────────────┐
│ DATA SYNC SCRIPT              │  │ FACEBOOK GRAPH API          │
│ 1. Fetches Total Views        │  │ Video published live to     │
│ 2. Fetches Followers/Fans     │  │ Followers & Recommendation  │
│ 3. Fetches Drive Stock Counts │  └─────────────────────────────┘
│ 4. Writes docs/data/pages.json│
└───────────┬───────────────────┘
            │ (Auto Git Commit & Push)
            ▼
┌────────────────────────────────────────────────────────┐
│ GITHUB PAGES HOSTING (docs/ folder)                    │
│ Hosts the Mobile PWA App "Raj FB Pro"                  │
└──────────────────────────┬─────────────────────────────┘
                           │ (PWA Instant Standalone App)
                           ▼
┌────────────────────────────────────────────────────────┐
│ USER'S SMARTPHONE (iOS / Android)                      │
│ Live Dashboard, Health Center, Stock Counter, Top 50   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Exact Directory & Codebase Structure

When Antigravity scaffolds the project on the new PC, it must establish this exact hierarchy:

```text
project_root/
├── .agents/                               # Antigravity Rules & Customizations
├── .github/
│   └── workflows/
│       ├── post.yml                       # USA Fleet Posting Workflow
│       ├── uk_london_post.yml             # UK Fleet Posting Workflow (Staggered)
│       └── sync_views.yml                 # 2-Hourly Real-Time Dashboard Sync
├── config.yaml                            # Master Configuration File
├── config_uk_account1.yaml                # Regional / Account-Specific Configs
├── config_usa_account1.yaml
├── data/
│   ├── posted_videos.db                  # SQLite Database (WAL Mode, Persistent)
│   ├── upload_history.json               # Full upload event log & runner telemetry
│   └── pages_tokens.json                 # Permanent Page Access Tokens dictionary
├── docs/                                  # Mobile PWA App & GitHub Pages Root
│   ├── .nojekyll                          # Disables Jekyll processing on GitHub Pages
│   ├── favicon.ico
│   ├── manifest.json                      # PWA Manifest (Icons, Name, Theme, Standalone)
│   ├── index.html                         # Full Mobile & Desktop Dashboard UI
│   ├── privacy.html                       # Meta Compliance Privacy Policy
│   ├── data-deletion.html                 # Meta Compliance Data Deletion Instructions
│   ├── css/
│   │   └── gold_dashboard.css             # Obsidian & Gold Glassmorphic Theme
│   ├── js/
│   │   ├── app.js                         # Core Controller, Dynamic Filters & Tabs
│   │   ├── sync_service.js                # Live Data Poller & Sync Handler
│   │   └── components/                    # Modular UI renderers
│   ├── icons/
│   │   ├── icon-192.png                   # PWA Mobile Icon
│   │   └── icon-512.png                   # PWA Large Icon / Meta App Icon
│   └── data/
│       └── pages_data.json                # Live Sync Payload (Followers, Views, Stock)
├── scripts/
│   ├── exchange_tokens.py                 # User Token -> Permanent Page Tokens
│   ├── sync_dashboard_data.py             # Pulls Meta & Drive Stats -> JSON
│   ├── connect_wireguard_uk.sh            # UK WireGuard Runner VPN Script
│   ├── connect_wireguard_usa.sh           # USA WireGuard Runner VPN Script
│   ├── audit_uploads_and_slots.py         # Slot collision & health audit CLI
│   └── validate_config.py                 # Pre-flight YAML configuration validator
├── src/
│   ├── config.py                          # Pydantic Configuration Models
│   ├── db.py                              # SQLite Manager with Duplicate Prevention
│   ├── drive_client.py                    # Google Drive Service Account Client
│   ├── facebook_client.py                 # Meta Graph API Reels & Video Client
│   ├── page_runner.py                     # Execution Orchestrator with Failure Isolation
│   ├── retry.py                           # Exponential Backoff & Transient Error Handler
│   └── video_utils.py                     # FFprobe Video Probing & Dimensions Validator
├── tests/
│   ├── test_config.py                     # Validates YAML parsing
│   ├── test_db.py                         # Validates SQLite integrity
│   ├── test_video_routing.py              # Validates 9:16 Reel vs Video detection
│   └── test_page_isolation.py             # Validates page failure independence
├── dashboard_server.py                    # Local Dev Server (http://localhost:8080)
├── main.py                                # CLI Runner Entrypoint
├── requirements.txt                       # Python Dependencies
├── service_account.json                   # Google Cloud Service Account Key (Git Ignored)
└── README.md
```

---

## 3. The Phone App: UI/UX, Design Tokens & All 8 Modules

The phone app is a **Progressive Web App (PWA)** hosted directly on GitHub Pages (`docs/` directory). When opened on any smartphone, tapping **"Add to Home Screen"** installs it as a native-feeling standalone app with no browser URL bar, custom splash screen, and smooth mobile interactions.

### 3.1 Design System & Aesthetic Tokens
- **Theme Concept:** *Luxe Obsidian & Gold Command Center*
- **Background Color:** `#07090e` (Deepest Obsidian Void)
- **Card Background:** `rgba(17, 24, 39, 0.7)` with `backdrop-filter: blur(16px)`
- **Border Gradients:** `1px solid rgba(255, 255, 255, 0.08)` with hover highlight `rgba(250, 204, 21, 0.4)`
- **Accent Palette:**
  - 🥇 **Luxe Gold:** `#facc15` / `#f5ba23` (Headers, active tabs, podiums)
  - ⚡ **Electric Cyan:** `#38bdf8` (Drive stock, sync bars, live connections)
  - 🟢 **Emerald Green:** `#10b981` (Healthy tokens, successful uploads)
  - 🔴 **Crimson Warning:** `#ef4444` (0-views, gaps >3 days, expired tokens)
- **Typography:**
  - Headings & Branding: `'Outfit', sans-serif` (Weights: 600, 700, 800)
  - Body & UI: `'Plus Jakarta Sans', sans-serif` (Weights: 400, 500, 600)
  - Numbers, IDs & Timestamps: `'JetBrains Mono', monospace` (Weight: 600)

### 3.2 Mobile-First Navigation & Layout
1. **Sticky Top Mobile Header:**
   - Left: `☰ Menu` Hamburger button (opens slide-over navigation drawer).
   - Center: `Raj FB Pro` logo with amber badge.
   - Right: `⚡ Master Sync` button (triggers immediate client refresh with instant animated progress bar).
2. **Slide-Over Navigation Drawer:**
   - Smooth slide-in from the left with dark backdrop blur.
   - Clean modular navigation tiles leading to each of the 8 modules.
3. **Toast Notification System:**
   - Floating dark-gold pill at top-center (`#goldToast`) providing instant feedback on user actions.

### 3.3 The 8 Complete Feature Modules

| # | Module Name | Icon | Purpose & Features |
|---|---|:---:|---|
| **1** | **Master Dashboard** | 📊 | **Portfolio KPI Overview:**<br>• Total Fleet Followers & Total Views with 24h delta.<br>• Total Published Reels counter.<br>• Playable Google Drive Stock across all folders.<br>• Quick Fleet Performance summary cards. |
| **2** | **All Pages List** | 📑 | **Multi-Account Directory:**<br>• Search bar across all pages by name or Page ID.<br>• Grouped by Account / Manager Profile.<br>• Live Page avatar with automatic Graph API fallback (`https://graph.facebook.com/v20.0/{page_id}/picture?type=large`).<br>• Direct external link to Facebook Page (`🎬 FB ↗`). |
| **3** | **Post Now Studio** | 🚀 | **Manual Upload Launcher:**<br>• Instant multi-page upload trigger from the phone.<br>• Allows user to dispatch immediate posting without waiting for cron schedule. |
| **4** | **Drive Data** | 📁 | **Cloud Inventory Monitor:**<br>• Lists every Google Drive folder and its current count of unposted videos.<br>• Color-coded badges: Green (>20 videos), Yellow (5–20 videos), Red (<5 videos — Refill Alert!). |
| **5** | **Upload History** | 📜 | **Real-Time Telemetry & Audit:**<br>• Chronological feed of uploaded Reels with direct Facebook Video links.<br>• Displays Cloud Runner IP, City (e.g. London, Los Angeles), and timestamp.<br>• Shows exact filename, duration, and post type (`Reel` vs `Video`). |
| **6** | **Health & Audit Center** | 🛡️ | **System Diagnostic Hub:**<br>• **Token Health:** Validates Page Access Tokens; flags invalid/expired tokens.<br>• **Upload Gap Detector:** Red alert for any channel with zero posts in >3 days.<br>• **VPN Health:** Confirms UK/USA exit IP cleanliness. |
| **7** | **Top 50 Performers** | 🏆 | **Viral Leaderboard:**<br>• Channels ranked descending by timeframe views.<br>• **Podium Display:** #1 Gold, #2 Silver, #3 Bronze with viral thumbnail previews.<br>• Follower growth velocity indicator. |
| **8** | **Low & 0 Views Channels** | ❄️ | **Suppression & Shadowban Radar:**<br>• Lists channels stuck at 0 views or <500 views.<br>• Direct diagnostic link to verify Meta App Live Mode and permission status. |

---

## 4. Real-Time Data Sync Architecture

How data moves from Facebook and Google Drive to the user's phone app with **zero cloud hosting fees**:

```text
[Cron: Every 2 Hours] ──► GitHub Actions Runner
                                │
                                ├─ Runs `scripts/sync_dashboard_data.py`
                                │   ├─ Queries Meta Graph API for Views & Followers
                                │   ├─ Queries Google Drive API for Remaining Video Stock
                                │   └─ Reads `data/posted_videos.db` for Upload History
                                │
                                ├─ Writes consolidated payload to `docs/data/pages_data.json`
                                ├─ Commits & pushes `docs/data/` to GitHub `main` branch
                                │
                                └─ GitHub Pages automatically deploys static update
                                        │
                                        ▼ (Instant cache-busting fetch)
                           User opens PWA on Phone ➔ Fresh Data Displayed!
```

---

## 5. Step-by-Step Implementation Roadmap for Antigravity

Follow these phases in strict chronological order when setting up on the new PC.

### Phase 1: Environment & Scaffolding
1. Create the project root directory.
2. Initialize Git repository:
   ```bash
   git init
   git branch -M main
   ```
3. Create Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install pydantic pyyaml requests google-api-python-client google-auth httpx pytest
   ```
4. Save `requirements.txt`.

### Phase 2: Google Cloud & Drive Setup
1. **Google Cloud Console:** Create project `fb-automation-fleet`.
2. **Enable APIs:** Enable **Google Drive API**.
3. **Service Account:**
   - Create Service Account: `drive-runner@fb-automation-fleet.iam.gserviceaccount.com`.
   - Create and download JSON key file ➔ save as `service_account.json` in project root.
4. **Drive Folders Organization:**
   - Create a dedicated Google Drive folder for each Facebook Page.
   - **Crucial Step:** Share every folder with the Service Account email (`Viewer` role).
   - Record the `drive_folder_id` for each page (found in folder URL: `drive.google.com/drive/folders/<FOLDER_ID>`).

### Phase 3: Meta App Live Mode & Token Pipeline

> [!CAUTION]
> **1000% MANDATORY RULE: Meta App Must Be in "Live" Mode!**
> If the Meta App remains in "In Development" mode, Meta suppresses Reels from public recommendation feeds, causing **permanent 0-Views on all uploads**.

1. **Create Meta App:**
   - Go to [Meta for Developers](https://developers.facebook.com/).
   - Create App ➔ Use Case: **Business / Other**.
2. **Configure App Basic Settings (`/settings/basic/`):**
   - **App Domains:** Your GitHub Pages domain (e.g. `username.github.io`).
   - **Privacy Policy URL:** `https://username.github.io/repo-name/privacy.html`.
   - **User Data Deletion:** `https://username.github.io/repo-name/data-deletion.html`.
   - **Category:** `Business and Pages`.
   - **App Icon:** Upload square 512x512 icon from `docs/icons/icon-512.png`.
   - **Add Platform:** Choose `Website` ➔ Site URL: `https://username.github.io/repo-name/`.
   - **Save Changes.**
3. **Switch to LIVE Mode:**
   - Toggle the top header switch from **"In Development"** to **"Live"**.
4. **Request Graph API Permissions:**
   - `pages_show_list`
   - `pages_manage_posts`
   - `pages_read_engagement`
5. **Generate Permanent Page Access Tokens:**
   - Obtain a short-lived User Access Token from Graph API Explorer.
   - Run the included exchange script:
     ```bash
     python scripts/exchange_tokens.py --app-id <APP_ID> --app-secret <APP_SECRET> --user-token <USER_TOKEN>
     ```
   - Store generated permanent tokens in `data/pages_tokens.json` and `config.yaml`.

### Phase 4: SQLite Database & Duplicate Guard
Create `src/db.py` to manage `data/posted_videos.db`:
- **Table `videos`:** `(id INTEGER PRIMARY KEY, page_id TEXT, drive_file_id TEXT UNIQUE, facebook_video_id TEXT, filename TEXT, post_type TEXT, status TEXT, posted_at DATETIME)`
- **Table `runs`:** `(id INTEGER PRIMARY KEY, started_at DATETIME, completed_at DATETIME, status TEXT, runner_ip TEXT, pages_processed INTEGER, errors TEXT)`
- Enable SQLite **WAL mode** (`PRAGMA journal_mode=WAL;`) for high concurrency and zero locking issues.

### Phase 5: Core Upload & Routing Engine
Implement `src/` modules:
1. `video_utils.py`: Runs FFprobe / metadata extraction.
   - Vertical ratio check: `height >= width`.
   - Duration check: `<= 90 seconds` ➔ `reel`, `> 90 seconds` ➔ `classic_video`.
2. `drive_client.py`: Lists files ordered by `createdTime asc` (FIFO queue). Downloads next eligible unposted file.
3. `facebook_client.py`:
   - **Reels Flow:** Initializes upload session at `POST /{page_id}/video_reels` ➔ Streams binary chunks to `upload_url` ➔ Calls publish endpoint.
   - **Classic Video Flow:** Chunked resumable upload to `POST /{page_id}/videos`.
4. `page_runner.py`: Wraps page execution with `try...except` isolation so failure on one page never stops the pipeline.

### Phase 6: VPN / WireGuard & Anti-Ban Protection
To protect Facebook accounts from cross-region flag bans:
1. Cloud Runners must route uploads through regional clean residential/datacenter IPs.
2. In GitHub Actions, use WireGuard:
   - Install `wireguard resolvconf` on Ubuntu runner.
   - Load config from GitHub Secret `WIREGUARD_CONFIG_UK` or `WIREGUARD_CONFIG_USA`.
   - Execute kill-switch test: if `curl ipinfo.io` does not match target country, abort immediately before calling Meta Graph API.

### Phase 7: GitHub Actions Cloud Automation
Set up GitHub repository secrets:
- `GDRIVE_SERVICE_ACCOUNT_JSON`
- `FB_PAGE_ACCESS_TOKEN`
- `WIREGUARD_CONFIG_UK`
- `WIREGUARD_CONFIG_USA`
- `DISCORD_WEBHOOK_URL` (Optional alerts)

Configure workflow files in `.github/workflows/`:
- `post.yml`: USA postings (staggered 4 times daily).
- `uk_london_post.yml`: UK postings (staggered across profiles with 10–20 minute offsets to prevent slot collisions).
- `sync_views.yml`: Runs every 2 hours to update dashboard data.

### Phase 8: Building & Deploying the Phone App (PWA)
1. Build `docs/index.html` with all 8 modules and mobile drawer.
2. Link `docs/css/gold_dashboard.css` with obsidian `#07090e` and gold tokens.
3. Configure `docs/manifest.json`:
   ```json
   {
     "name": "Raj FB Pro",
     "short_name": "Raj FB Pro",
     "start_url": "./index.html",
     "display": "standalone",
     "background_color": "#07090e",
     "theme_color": "#07090e",
     "orientation": "portrait-primary",
     "icons": [
       { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
       { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
     ]
   }
   ```
4. In GitHub Repo Settings ➔ **Pages** ➔ Source: **Deploy from a branch** ➔ Branch: `main`, Folder: `/docs`.
5. Open URL on iPhone/Android Safari or Chrome ➔ **"Add to Home Screen"**.

### Phase 9: Automated Testing & Verification
Before pushing to production, Antigravity must execute:
```bash
# 1. Validate configuration syntax
python scripts/validate_config.py config.yaml

# 2. Run unit tests
python -m pytest tests/ -v

# 3. Test local dry-run (verifies Drive & DB without posting)
python main.py --dry-run

# 4. Launch local dashboard preview
python dashboard_server.py
```
Open `http://localhost:8080` in browser to visually confirm UI rendering, navigation drawer, and data tables.

---

## 6. User Fill-In Sheet (Plug-and-Play Credentials)

User: Fill in these details for your new PC / new fleet. Antigravity will parse these entries directly:

### 6.1 Meta Developer App Details
```yaml
meta_app:
  app_id: "ENTER_NEW_META_APP_ID_HERE"
  app_secret: "ENTER_NEW_META_APP_SECRET_HERE"
  app_mode: "live" # Must be 'live'
  user_access_token: "ENTER_TEMPORARY_USER_ACCESS_TOKEN_FOR_EXCHANGE"
```

### 6.2 Target Facebook Pages & Drive Folders
```yaml
pages:
  - page_id: "ENTER_PAGE_ID_1"
    name: "page_1"
    display_name: "Channel Name 1"
    account_group: "Profile_1" # e.g. USA Account 1 or UK Account 1
    drive_folder_id: "ENTER_GOOGLE_DRIVE_FOLDER_ID_1"
    daily_limit: 4
    enabled: true

  - page_id: "ENTER_PAGE_ID_2"
    name: "page_2"
    display_name: "Channel Name 2"
    account_group: "Profile_1"
    drive_folder_id: "ENTER_GOOGLE_DRIVE_FOLDER_ID_2"
    daily_limit: 4
    enabled: true

  - page_id: "ENTER_PAGE_ID_3"
    name: "page_3"
    display_name: "Channel Name 3"
    account_group: "Profile_2"
    drive_folder_id: "ENTER_GOOGLE_DRIVE_FOLDER_ID_3"
    daily_limit: 4
    enabled: true
```

### 6.3 VPN & Proxy Settings
```yaml
network:
  region: "UK" # "UK" or "USA"
  wireguard_enabled: true
  wireguard_peer_endpoint: "ENTER_VPN_ENDPOINT_IF_APPLICABLE"
  require_regional_ip: true
```

### 6.4 Posting Time Slots (Target Local & IST)
```yaml
schedules:
  slot_1: "09:00 AM Target Time"
  slot_2: "01:00 PM Target Time"
  slot_3: "05:00 PM Target Time"
  slot_4: "09:30 PM Target Time"
```

---

> **FINAL DIRECTIVE TO ANTIGRAVITY EXECUTING ON NEW PC:**
> 1. Read this blueprint thoroughly.
> 2. Read the user-provided credentials from the sheet above.
> 3. Scaffold the directories and files exactly as specified.
> 4. Verify all tests pass before scheduling GitHub Actions.
> 5. Deploy the PWA to `/docs` and confirm live deployment on GitHub Pages.
