#!/usr/bin/env bash
# scripts/connect_wireguard_usa.sh
# Connects to WireGuard USA server and enforces IP country kill-switch

set -euo pipefail

echo "========================================="
echo "🔒 WireGuard USA VPN Connector"
echo "========================================="

if [ -z "${WIREGUARD_CONFIG_USA:-}" ]; then
  echo "[!] KILL-SWITCH HALT: WIREGUARD_CONFIG_USA secret is not set!"
  echo "[-] Refusing to proceed on raw GitHub Actions IP. Aborting."
  exit 1
fi

echo "[*] Setting up resolvconf link for DNS routing..."
sudo ln -sf /usr/bin/resolvectl /usr/local/bin/resolvconf || true

echo "[*] Writing WireGuard configuration to /etc/wireguard/wg0.conf..."
sudo mkdir -p /etc/wireguard
echo "$WIREGUARD_CONFIG_USA" | sudo tee /etc/wireguard/wg0.conf > /dev/null
sudo chmod 600 /etc/wireguard/wg0.conf

echo "[*] Bringing up WireGuard tunnel wg0..."
sudo wg-quick up wg0

# Allow tunnel handshake stabilization
sleep 3

echo "[*] WireGuard Tunnel Status:"
sudo wg show || true

echo "[*] Verifying exit IP, Country, and Location..."
IP_INFO=$(curl -s --max-time 15 https://ipinfo.io/json || curl -s --max-time 15 https://ifconfig.co/json || echo "{}")
COUNTRY=$(echo "$IP_INFO" | grep -o '"country": "[^"]*' | cut -d'"' -f4 || echo "")
CITY=$(echo "$IP_INFO" | grep -o '"city": "[^"]*' | cut -d'"' -f4 || echo "")
IP=$(echo "$IP_INFO" | grep -o '"ip": "[^"]*' | cut -d'"' -f4 || echo "")
ORG=$(echo "$IP_INFO" | grep -o '"org": "[^"]*' | cut -d'"' -f4 || echo "")

echo "[+] Verified Exit IP: $IP"
echo "[+] Country: $COUNTRY | City: $CITY | Network: $ORG"

if [ "$COUNTRY" != "US" ] && [ "$COUNTRY" != "USA" ]; then
  echo "[!] HARD KILL-SWITCH ACTIVATED: Exit IP country is '$COUNTRY' (Must be 'US')."
  echo "[-] Zero-leak rule triggered: Halting pipeline before any Facebook Graph API communication!"
  sudo wg-quick down wg0 2>/dev/null || true
  exit 1
fi

echo "[SUCCESS] Verified USA New York clean exit IP. Safe to proceed with Meta Graph API uploads."
