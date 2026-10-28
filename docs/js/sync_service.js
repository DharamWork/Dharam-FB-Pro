/**
 * sync_service.js
 * Handles live payload polling with cache-busting and event bus for UI components.
 */

class DashboardSyncService {
  constructor(endpoint = "data/pages_data.json") {
    this.endpoint = endpoint;
    this.data = null;
    this.listeners = [];
  }

  subscribe(callback) {
    this.listeners.push(callback);
    if (this.data) callback(this.data);
  }

  notify() {
    for (const cb of this.listeners) {
      cb(this.data);
    }
  }

  async fetchLatest() {
    try {
      // Append cache-busting timestamp
      const url = `${this.endpoint}?t=${new Date().getTime()}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch dashboard data`);
      }
      this.data = await response.json();
      localStorage.setItem("fb_auto_cache", JSON.stringify(this.data));
      this.notify();
      return { success: true, data: this.data };
    } catch (err) {
      console.warn("Live fetch failed, loading local fallback:", err);
      const cached = localStorage.getItem("fb_auto_cache");
      if (cached) {
        this.data = JSON.parse(cached);
        this.notify();
        return { success: true, data: this.data, cached: true };
      }
      return { success: false, error: err.message };
    }
  }
}

window.syncService = new DashboardSyncService();
