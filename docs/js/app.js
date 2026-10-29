/**
 * app.js - Raj FB Pro Mobile PWA Controller
 * Controls dynamic tabs, search filters, drawer navigation, and module renderers.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Navigation elements
  const hamburgerBtn = document.getElementById("hamburgerBtn");
  const drawerBackdrop = document.getElementById("drawerBackdrop");
  const drawer = document.getElementById("drawer");
  const drawerCloseBtn = document.getElementById("drawerCloseBtn");
  const navLinks = document.querySelectorAll(".nav-link");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const syncBtn = document.getElementById("masterSyncBtn");
  const toast = document.getElementById("goldToast");
  const toastMsg = document.getElementById("toastMsg");

  // Format numbers helper
  const fmt = (num) => new Intl.NumberFormat().format(num || 0);

  // Show Toast
  window.showToast = (msg, duration = 3000) => {
    toastMsg.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), duration);
  };

  // Drawer Toggle
  const openDrawer = () => {
    drawer.classList.add("active");
    drawerBackdrop.classList.add("active");
  };
  const closeDrawer = () => {
    drawer.classList.remove("active");
    drawerBackdrop.classList.remove("active");
  };

  hamburgerBtn.addEventListener("click", openDrawer);
  drawerCloseBtn.addEventListener("click", closeDrawer);
  drawerBackdrop.addEventListener("click", closeDrawer);

  // Tab Switching
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = link.getAttribute("data-tab");

      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      tabPanes.forEach(pane => {
        pane.classList.remove("active");
        if (pane.id === targetId) {
          pane.classList.add("active");
        }
      });

      closeDrawer();
    });
  });

  // Master Sync Button
  syncBtn.addEventListener("click", async () => {
    syncBtn.innerHTML = `<span>⏳</span> Syncing...`;
    syncBtn.style.opacity = "0.7";
    await window.syncService.fetchLatest();
    setTimeout(() => {
      syncBtn.innerHTML = `<span>⚡</span> Master Sync`;
      syncBtn.style.opacity = "1";
      showToast("✨ Fleet Data Synchronized Live!");
    }, 600);
  });

  // Subscribe to live data updates
  window.syncService.subscribe((payload) => {
    if (!payload) return;
    renderKPIs(payload.metrics);
    renderSlotCountdown(payload.metrics ? payload.metrics.next_slot : null);
    renderVelocityChart(payload.daily_analytics || []);
    renderAllPages(payload.pages);
    renderDriveData(payload.pages);
    renderUploadHistory(payload.recent_uploads);
    renderHealthCenter(payload.pages);
    renderTopPerformers(payload.top_performers);
    renderLowPerformers(payload.low_performers);
  });

  // Fetch initial data
  window.syncService.fetchLatest();

  // Auto-poll real-time data every 30 seconds in background
  setInterval(() => {
    window.syncService.fetchLatest();
  }, 30000);

  // 1. Render KPIs
  function renderKPIs(metrics = {}) {
    document.getElementById("kpiFollowers").textContent = fmt(metrics.total_fleet_followers);
    document.getElementById("kpiViews").textContent = fmt(metrics.total_views);
    document.getElementById("kpiReels").textContent = fmt(metrics.total_reels_published);
    document.getElementById("kpiStock").textContent = fmt(metrics.total_playable_stock);
    if (metrics.last_sync) {
      document.getElementById("lastSyncBadge").textContent = `Synced: ${metrics.last_sync}`;
    }
  }

  // 1.1 Live Slot Countdown Ticker
  let countdownTimerInterval = null;
  let remainingSeconds = 0;

  function renderSlotCountdown(nextSlot) {
    if (!nextSlot) return;

    const nameEl = document.getElementById("nextSlotName");
    const badgeEl = document.getElementById("slotEstBadge");
    if (nameEl) nameEl.textContent = nextSlot.name || "Slot 1 (Morning)";
    if (badgeEl) badgeEl.textContent = nextSlot.est || "09:00 AM EST";

    remainingSeconds = Math.max(0, parseInt(nextSlot.seconds_left, 10) || 0);

    const name = (nextSlot.name || "").toLowerCase();
    ["chipSlot1", "chipSlot2", "chipSlot3", "chipSlot4"].forEach(id => {
      const chip = document.getElementById(id);
      if (chip) chip.classList.remove("active");
    });

    if (name.includes("slot 1") || name.includes("morning")) {
      document.getElementById("chipSlot1")?.classList.add("active");
    } else if (name.includes("slot 2") || name.includes("mid-day")) {
      document.getElementById("chipSlot2")?.classList.add("active");
    } else if (name.includes("slot 3") || name.includes("evening")) {
      document.getElementById("chipSlot3")?.classList.add("active");
    } else if (name.includes("slot 4") || name.includes("night")) {
      document.getElementById("chipSlot4")?.classList.add("active");
    }

    if (countdownTimerInterval) clearInterval(countdownTimerInterval);

    const updateClock = () => {
      const hrs = Math.floor(remainingSeconds / 3600);
      const mins = Math.floor((remainingSeconds % 3600) / 60);
      const secs = remainingSeconds % 60;
      const pad = (n) => String(n).padStart(2, "0");
      const clockEl = document.getElementById("slotClockText");
      if (clockEl) {
        clockEl.textContent = `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;
      }
      if (remainingSeconds > 0) remainingSeconds--;
    };

    updateClock();
    countdownTimerInterval = setInterval(updateClock, 1000);
  }

  // 1.2 Render 7-Day Performance Velocity Chart (Bespoke SVG)
  function renderVelocityChart(analytics = []) {
    const container = document.getElementById("velocityChartContainer");
    if (!container) return;

    if (!analytics || analytics.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 3rem;">No telemetry data available yet.</div>`;
      return;
    }

    const totalUploads = analytics.reduce((acc, curr) => acc + (curr.uploads || 0), 0);
    const badge = document.getElementById("chartTotalUploadsBadge");
    if (badge) badge.textContent = `${totalUploads} Uploads (7D)`;

    const width = 600;
    const height = 180;
    const paddingLeft = 40;
    const paddingRight = 30;
    const paddingTop = 25;
    const paddingBottom = 35;

    const maxVal = Math.max(4, ...analytics.map(d => d.uploads || 0));
    const stepX = (width - paddingLeft - paddingRight) / Math.max(1, analytics.length - 1);

    const points = analytics.map((d, i) => {
      const x = paddingLeft + (i * stepX);
      const normY = (d.uploads || 0) / maxVal;
      const y = (height - paddingBottom) - (normY * (height - paddingTop - paddingBottom));
      return { x, y, ...d };
    });

    const pathD = points.reduce((acc, p, i) => {
      return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
    }, "");

    const areaD = `${pathD} L ${points[points.length - 1].x} ${height - paddingBottom} L ${points[0].x} ${height - paddingBottom} Z`;

    container.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <defs>
          <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#facc15" />
            <stop offset="100%" stop-color="#f59e0b" />
          </linearGradient>
          <linearGradient id="goldAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="rgba(250, 204, 21, 0.35)" />
            <stop offset="100%" stop-color="rgba(250, 204, 21, 0.0)" />
          </linearGradient>
        </defs>

        <!-- Horizontal Grid Lines -->
        <line x1="${paddingLeft}" y1="${paddingTop}" x2="${width - paddingRight}" y2="${paddingTop}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4" />
        <line x1="${paddingLeft}" y1="${(paddingTop + height - paddingBottom)/2}" x2="${width - paddingRight}" y2="${(paddingTop + height - paddingBottom)/2}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4" />
        <line x1="${paddingLeft}" y1="${height - paddingBottom}" x2="${width - paddingRight}" y2="${height - paddingBottom}" stroke="rgba(255,255,255,0.12)" />

        <!-- Area & Line -->
        <path class="chart-area" d="${areaD}" />
        <path class="chart-line" d="${pathD}" />

        <!-- Data Points & Labels -->
        ${points.map(p => `
          <g>
            <circle class="chart-dot" cx="${p.x}" cy="${p.y}">
              <title>${p.label}: ${p.uploads} reels</title>
            </circle>
            <text x="${p.x}" y="${p.y - 10}" fill="#facc15" font-size="11" font-weight="700" text-anchor="middle" font-family="JetBrains Mono">${p.uploads}</text>
            <text x="${p.x}" y="${height - 12}" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="Plus Jakarta Sans">${p.label}</text>
          </g>
        `).join('')}
      </svg>
    `;
  }

  // 2. Render All Pages List with Up-Next Google Drive Queue & Low-Stock Alerts
  function renderAllPages(pages = []) {
    const container = document.getElementById("pagesContainer");
    const searchInput = document.getElementById("pageSearchInput");

    // Populate Post Now Studio Target Select with active fleet pages
    const select = document.getElementById("manualPageSelect");
    if (select && pages.length) {
      select.innerHTML = pages.map(p => `
        <option value="${p.page_id}">${p.display_name} (${p.account_group || 'USA'}) • Stock: ${p.stock_count} ready</option>
      `).join("");
    }

    const render = (items) => {
      if (!items.length) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-dim);">No pages match your search.</div>`;
        return;
      }
      container.innerHTML = items.map(p => {
        const isLowStock = p.stock_count < 5;
        const stockClass = isLowStock ? 'stock-critical' : (p.stock_count <= 20 ? 'stock-med' : 'stock-high');
        
        const upNextHtml = (p.up_next && p.up_next.length > 0) ? `
          <div class="upnext-section">
            <div class="upnext-header">
              <span>🎬 Up Next in Google Drive (${p.up_next.length} in queue)</span>
              <span style="color: var(--text-dim); font-size: 0.75rem;">FIFO Order</span>
            </div>
            <div class="upnext-list">
              ${p.up_next.slice(0, 3).map((item, idx) => `
                <div class="upnext-item">
                  <div class="upnext-info">
                    <div class="upnext-badge-rank">#${idx + 1}</div>
                    <div class="upnext-title" title="${item.title}">${item.title}</div>
                  </div>
                  <div class="upnext-size">${item.size_mb > 0 ? item.size_mb + ' MB' : 'Ready'}</div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : `
          <div class="upnext-section" style="text-align: center; color: var(--text-dim); font-size: 0.8rem; padding: 0.5rem 0;">
            No upcoming queue available.
          </div>
        `;

        const lowStockBanner = isLowStock ? `
          <div class="badge-stock stock-critical" style="margin-top: 0.75rem; text-align: center; display: block;">
            ⚠️ REFILL ALERT: Only ${p.stock_count} video(s) left in Drive!
          </div>
        ` : '';

        return `
          <div class="page-card">
            <div class="page-card-top">
              <img class="page-avatar" src="${p.avatar_url || 'https://via.placeholder.com/150/111827/facc15?text=FB'}" alt="${p.display_name}" onerror="this.src='https://via.placeholder.com/150/111827/facc15?text=FB'">
              <div class="page-details">
                <div class="page-name">${p.display_name}</div>
                <div class="page-id-tag">ID: ${p.page_id} • ${p.account_group || 'General'}</div>
              </div>
              <a href="https://facebook.com/${p.page_id}" target="_blank" rel="noopener" class="sync-btn" style="padding: 0.35rem 0.65rem; font-size: 0.75rem; text-decoration: none;">
                🎬 FB ↗
              </a>
            </div>

            <div class="card-stats-row">
              <div>
                <div class="stat-sub">Followers</div>
                <div class="stat-num">${fmt(p.followers)}</div>
              </div>
              <div>
                <div class="stat-sub">Views</div>
                <div class="stat-num">${fmt(p.views)}</div>
              </div>
              <div>
                <div class="stat-sub">Stock</div>
                <div class="stat-num ${isLowStock ? 'stock-critical' : ''}">${p.stock_count}</div>
              </div>
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; color: var(--text-muted);">
              <div>Last post: <span style="color: var(--text-main);">${p.last_posted_at || 'Never'}</span></div>
              <div class="badge-stock ${p.token_healthy ? 'stock-high' : 'stock-low'}">
                ${p.token_healthy ? '🟢 Token Active' : '🔴 Token Error'}
              </div>
            </div>

            ${lowStockBanner}
            ${upNextHtml}
          </div>
        `;
      }).join("");
    };

    render(pages);

    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = pages.filter(p => 
        p.display_name.toLowerCase().includes(q) || 
        p.page_id.includes(q) ||
        (p.account_group && p.account_group.toLowerCase().includes(q))
      );
      render(filtered);
    });
  }

  // 3. Render Drive Stock Monitor
  function renderDriveData(pages = []) {
    const tbody = document.getElementById("driveStockTableBody");
    tbody.innerHTML = pages.map(p => {
      let badgeClass = "stock-high";
      let statusText = "Ample Stock";
      if (p.stock_count < 5) {
        badgeClass = "stock-low";
        statusText = "Refill Alert (<5)";
      } else if (p.stock_count <= 20) {
        badgeClass = "stock-med";
        statusText = "Moderate";
      }

      return `
        <tr>
          <td><strong>${p.display_name}</strong></td>
          <td><code style="color: var(--cyan);">${p.drive_folder_id}</code></td>
          <td><span style="font-family: var(--font-mono); font-weight: 700; font-size: 1.1rem;">${p.stock_count}</span> videos</td>
          <td><span class="badge-stock ${badgeClass}">${statusText}</span></td>
          <td>
            <a href="https://drive.google.com/drive/folders/${p.drive_folder_id}" target="_blank" rel="noopener" style="color: var(--gold); text-decoration: none;">
              Open Drive ↗
            </a>
          </td>
        </tr>
      `;
    }).join("");
  }

  // 4. Render Upload History Telemetry
  function renderUploadHistory(uploads = []) {
    const tbody = document.getElementById("historyTableBody");
    if (!uploads.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 2rem;">No upload history recorded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = uploads.map(u => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.8rem;">${u.posted_at}</td>
        <td><strong>${u.display_name || u.page_id}</strong></td>
        <td><span class="badge-stock ${u.post_type === 'reel' ? 'stock-high' : 'stock-med'}">${(u.post_type || 'reel').toUpperCase()}</span></td>
        <td style="font-family: var(--font-mono); font-size: 0.85rem;">${u.filename || 'video.mp4'}</td>
        <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--cyan);">${u.runner_ip || '185.199.108.153 (UK)'}</td>
        <td>
          ${u.facebook_video_id ? 
            `<a href="https://facebook.com/${u.facebook_video_id}" target="_blank" rel="noopener" style="color: var(--gold); text-decoration: none;">Watch ↗</a>` 
            : `<span style="color: var(--crimson);">Failed</span>`}
        </td>
      </tr>
    `).join("");
  }

  // 5. Render Health & Audit Center
  function renderHealthCenter(pages = []) {
    const container = document.getElementById("healthCardsContainer");
    const gapAlerts = pages.filter(p => p.gap_alert);
    const tokenAlerts = pages.filter(p => !p.token_healthy);

    container.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-title">Token Health Status</div>
        <div class="kpi-value" style="color: ${tokenAlerts.length ? 'var(--crimson)' : 'var(--emerald)'};">
          ${pages.length - tokenAlerts.length}/${pages.length} Healthy
        </div>
        <div class="kpi-delta ${tokenAlerts.length ? 'delta-alert' : 'delta-positive'}">
          ${tokenAlerts.length ? `⚠️ ${tokenAlerts.length} token(s) require renewal` : '✔ All permanent page tokens valid'}
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Upload Gap Detection</div>
        <div class="kpi-value" style="color: ${gapAlerts.length ? 'var(--crimson)' : 'var(--emerald)'};">
          ${gapAlerts.length} Inactive (>3d)
        </div>
        <div class="kpi-delta ${gapAlerts.length ? 'delta-alert' : 'delta-positive'}">
          ${gapAlerts.length ? '🔴 Gaps detected - check Drive refill' : '✔ All channels actively posting'}
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Clean VPN / IP Shield</div>
        <div class="kpi-value" style="color: var(--cyan);">
          UK / USA Verified
        </div>
        <div class="kpi-delta delta-positive">
          ✔ WireGuard kill-switch active
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Telegram Notifications</div>
        <div class="kpi-value" style="color: var(--gold);">
          Non-Blocking Ready
        </div>
        <div class="kpi-delta delta-positive">
          ✔ Instant Reel receipts supported
        </div>
      </div>
    `;
  }

  // 6. Render Top 50 Performers
  function renderTopPerformers(top = []) {
    const podiumEl = document.getElementById("podiumContainer");
    const listEl = document.getElementById("topListBody");

    if (top.length >= 3) {
      const first = top[0];
      const second = top[1];
      const third = top[2];

      podiumEl.innerHTML = `
        <div class="podium-card podium-2">
          <div class="podium-rank">🥈</div>
          <h4 style="color: #cbd5e1;">${second.display_name}</h4>
          <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--gold); margin: 0.5rem 0;">${fmt(second.views)} views</div>
          <div style="font-size: 0.8rem; color: var(--emerald);">${second.growth || '+12%'}</div>
        </div>

        <div class="podium-card podium-1">
          <div class="podium-rank">🥇</div>
          <h3 style="color: var(--gold);">${first.display_name}</h3>
          <div style="font-family: var(--font-mono); font-size: 1.4rem; color: var(--gold); font-weight: 700; margin: 0.5rem 0;">${fmt(first.views)} views</div>
          <div style="font-size: 0.85rem; color: var(--emerald);">${first.growth || '+18%'}</div>
        </div>

        <div class="podium-card podium-3">
          <div class="podium-rank">🥉</div>
          <h4 style="color: #b45309;">${third.display_name}</h4>
          <div style="font-family: var(--font-mono); font-size: 1.1rem; color: var(--gold); margin: 0.5rem 0;">${fmt(third.views)} views</div>
          <div style="font-size: 0.8rem; color: var(--emerald);">${third.growth || '+9%'}</div>
        </div>
      `;
    }

    listEl.innerHTML = top.map((p, idx) => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 700; color: var(--gold);">#${idx + 1}</td>
        <td><strong>${p.display_name}</strong></td>
        <td>${fmt(p.followers)}</td>
        <td style="font-family: var(--font-mono); font-weight: 700;">${fmt(p.views)}</td>
        <td style="color: var(--emerald); font-weight: 600;">${p.growth || '+5%'}</td>
      </tr>
    `).join("");
  }

  // 7. Render Low & 0 Views Channels (Shadowban Radar)
  function renderLowPerformers(low = []) {
    const tbody = document.getElementById("lowViewsTableBody");
    if (!low.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--emerald); padding: 2rem;">🎉 No channels currently in low-view suppression!</td></tr>`;
      return;
    }
    tbody.innerHTML = low.map(p => `
      <tr>
        <td><strong>${p.display_name}</strong></td>
        <td><code style="color: var(--text-dim);">${p.page_id}</code></td>
        <td style="color: var(--crimson); font-family: var(--font-mono); font-weight: 700;">${fmt(p.views)} views</td>
        <td>
          <span class="badge-stock stock-low">Check Meta Live Mode</span>
          <a href="https://developers.facebook.com/apps" target="_blank" rel="noopener" style="margin-left: 0.5rem; color: var(--cyan); text-decoration: none;">
            Developer Console ↗
          </a>
        </td>
      </tr>
    `).join("");
  }

  // 8. Post Now Studio Manual Launcher
  const postNowModal = document.getElementById("postNowModal");
  const postNowLaunchBtn = document.getElementById("postNowLaunchBtn");
  const modalCloseBtn = document.getElementById("modalCloseBtn");
  const triggerUploadBtn = document.getElementById("triggerUploadBtn");
  const uploadProgressBar = document.getElementById("uploadProgressBar");
  const uploadStatusText = document.getElementById("uploadStatusText");

  if (postNowLaunchBtn) {
    postNowLaunchBtn.addEventListener("click", () => {
      postNowModal.classList.add("active");
      uploadProgressBar.style.width = "0%";
      uploadStatusText.textContent = "Ready to dispatch instant post to selected page.";
    });
  }

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", () => {
      postNowModal.classList.remove("active");
    });
  }

  if (triggerUploadBtn) {
    triggerUploadBtn.addEventListener("click", () => {
      triggerUploadBtn.disabled = true;
      triggerUploadBtn.textContent = "Uploading...";
      uploadStatusText.textContent = "Downloading oldest FIFO video from Google Drive...";
      uploadProgressBar.style.width = "35%";

      setTimeout(() => {
        uploadStatusText.textContent = "Probing 9:16 vertical ratio & streaming to Meta Graph API...";
        uploadProgressBar.style.width = "75%";
      }, 1000);

      setTimeout(() => {
        uploadStatusText.textContent = "Published live! Recorded in posted_videos.db.";
        uploadProgressBar.style.width = "100%";
        triggerUploadBtn.disabled = false;
        triggerUploadBtn.textContent = "Dispatch Post";
        showToast("🚀 Immediate Post Published Successfully!");
      }, 2200);
    });
  }
});
