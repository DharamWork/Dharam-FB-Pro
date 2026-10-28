#!/usr/bin/env bash
# scripts/connect_wireguard_uk.sh
# Connects to WireGuard UK London server and enforces IP country kill-switch

set -euo pipefail

echo "========================================="
echo "🔒 WireGuard UK London VPN Connector"
echo "========================================="

if [ -z "${WIREGUARD_CONFIG_UK:-}" ]; then
  echo "[-] WIREGUARD_CONFIG_UK environment variable is not set. Skipping VPN tunnel."
  exit 0
fi

echo "[*] Writing WireGuard configuration to /etc/wireguard/wg0.conf..."
sudo mkdir -p /etc/wireguard
echo "$WIREGUARD_CONFIG_UK" | sudo tee /etc/wireguard/wg0.conf > /dev/null
sudo chmod 600 /etc/wireguard/wg0.conf

echo "[*] Bringing up WireGuard tunnel wg0..."
sudo wg-quick up wg0 || true

echo "[*] Verifying exit IP and Country..."
IP_INFO=$(curl -s --max-time 10 https://ipinfo.io/json || echo "{}")
COUNTRY=$(echo "$IP_INFO" | grep -o '"country": "[^"]*' | cut -d'"' -f4 || echo "")
IP=$(echo "$IP_INFO" | grep -o '"ip": "[^"]*' | cut -d'"' -f4 || echo "")

echo "[+] Current Exit IP: $IP (Country: $COUNTRY)"

if [ "$COUNTRY" != "GB" ] && [ "$COUNTRY" != "UK" ]; then
  echo "[!] KILL-SWITCH TRIGGERED: Exit IP country is '$COUNTRY' (Expected 'GB')."
  echo "[-] Aborting upload pipeline to protect account from cross-region flags."
  sudo wg-quick down wg0 || true
  exit 1
fi

echo "[SUCCESS] Verified UK London clean exit IP. Safe to proceed with Meta Graph API uploads."
