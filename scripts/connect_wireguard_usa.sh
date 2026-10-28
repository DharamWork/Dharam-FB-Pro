#!/usr/bin/env bash
# scripts/connect_wireguard_usa.sh
# Connects to WireGuard USA server and enforces IP country kill-switch

set -euo pipefail

echo "========================================="
echo "🔒 WireGuard USA VPN Connector"
echo "========================================="

if [ -z "${WIREGUARD_CONFIG_USA:-}" ]; then
  echo "[-] WIREGUARD_CONFIG_USA environment variable is not set. Skipping VPN tunnel."
  exit 0
fi

echo "[*] Writing WireGuard configuration to /etc/wireguard/wg0.conf..."
sudo mkdir -p /etc/wireguard
echo "$WIREGUARD_CONFIG_USA" | sudo tee /etc/wireguard/wg0.conf > /dev/null
sudo chmod 600 /etc/wireguard/wg0.conf

echo "[*] Bringing up WireGuard tunnel wg0..."
sudo wg-quick up wg0 || true

echo "[*] Verifying exit IP and Country..."
IP_INFO=$(curl -s --max-time 10 https://ipinfo.io/json || echo "{}")
COUNTRY=$(echo "$IP_INFO" | grep -o '"country": "[^"]*' | cut -d'"' -f4 || echo "")
IP=$(echo "$IP_INFO" | grep -o '"ip": "[^"]*' | cut -d'"' -f4 || echo "")

echo "[+] Current Exit IP: $IP (Country: $COUNTRY)"

if [ "$COUNTRY" != "US" ] && [ "$COUNTRY" != "USA" ]; then
  echo "[!] KILL-SWITCH TRIGGERED: Exit IP country is '$COUNTRY' (Expected 'US')."
  echo "[-] Aborting upload pipeline to protect account from cross-region flags."
  sudo wg-quick down wg0 || true
  exit 1
fi

echo "[SUCCESS] Verified USA clean exit IP. Safe to proceed with Meta Graph API uploads."
