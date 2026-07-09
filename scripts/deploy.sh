#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh — Shiva Sniper v10 VPS deployment script
# Run from LOCAL machine: bash scripts/deploy.sh
#
# What this does:
#   1. Installs Python 3.12 + pip + git on VPS (Ubuntu 24.04)
#   2. Clones or pulls the latest bot code from GitHub onto the VPS
#   3. Installs Python dependencies
#   4. Installs and starts/restarts systemd service
#   5. Opens firewall port for dashboard
#
# Usage:
#   bash scripts/deploy.sh                  # deploy to server in .env
#   VPS_IP=187.127.136.139 bash scripts/deploy.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

VPS_IP="${VPS_IP:-187.127.136.139}"
VPS_USER="${VPS_USER:-root}"
REMOTE_DIR="/app/shiva_sniper_bot"
SERVICE_NAME="goldbot"
DASHBOARD_PORT="10000"

echo "═══════════════════════════════════════════════════"
# Shiva Sniper v10
echo "  Shiva Sniper v10 — VPS Deploy (via GitHub)"
echo "  Target: ${VPS_USER}@${VPS_IP}"
echo "  Source: GitHub (main branch)"
echo "═══════════════════════════════════════════════════"

# ── 1. Install system dependencies ───────────────────────────────────────────
echo ""
echo "[1/5] Installing Python 3.12 & Git on VPS..."
ssh "${VPS_USER}@${VPS_IP}" "
  apt-get update -qq &&
  apt-get install -y python3.12 python3.12-venv python3-pip git &&
  python3.12 --version &&
  git --version
"

# ── 2. Clone or pull bot files from GitHub ────────────────────────────────────
echo ""
echo "[2/5] Fetching latest bot code from GitHub..."
ssh "${VPS_USER}@${VPS_IP}" "
  if [ ! -d '${REMOTE_DIR}/.git' ]; then
    echo '  Directory is not a git repository. Cloning from GitHub...' &&
    mkdir -p '${REMOTE_DIR}' &&
    git clone https://github.com/saniroy3311-spec/Bot-v10-30m.git '${REMOTE_DIR}'
  else
    echo '  Repository found. Pulling updates from GitHub...' &&
    cd '${REMOTE_DIR}' &&
    git fetch origin &&
    git reset --hard origin/main
  fi
"

echo "Code updated on VPS."

# ── 3. Install Python dependencies ───────────────────────────────────────────
echo ""
echo "[3/5] Installing Python dependencies..."
ssh "${VPS_USER}@${VPS_IP}" "
  cd ${REMOTE_DIR} &&
  pip3 install --break-system-packages -r requirements.txt
"

# ── 4. Setup .env if not present ─────────────────────────────────────────────
echo ""
echo "[4/5] Checking .env..."
ENV_EXISTS=$(ssh "${VPS_USER}@${VPS_IP}" "[ -f ${REMOTE_DIR}/.env ] && echo yes || echo no")
if [ "$ENV_EXISTS" = "no" ]; then
  echo "  .env not found — copying .env.example → .env"
  echo "  ⚠️  Edit ${REMOTE_DIR}/.env on the VPS with your real API keys!"
  ssh "${VPS_USER}@${VPS_IP}" "cp ${REMOTE_DIR}/.env.example ${REMOTE_DIR}/.env"
else
  echo "  .env already exists — keeping existing config."
fi

# ── 5. Install systemd service & Restart ──────────────────────────────────────
echo ""
echo "[5/5] Installing systemd service & restarting bot..."
ssh "${VPS_USER}@${VPS_IP}" "
  cp ${REMOTE_DIR}/systemd/shiva_sniper.service /etc/systemd/system/${SERVICE_NAME}.service &&
  systemctl daemon-reload &&
  systemctl enable ${SERVICE_NAME} &&
  systemctl restart ${SERVICE_NAME}
"

# Open firewall port for dashboard
ssh "${VPS_USER}@${VPS_IP}" "
  ufw allow ${DASHBOARD_PORT}/tcp 2>/dev/null || true
  echo 'Firewall rule added for port ${DASHBOARD_PORT}'
"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Deploy complete."
echo ""
echo "  NEXT STEPS:"
echo "  1. Edit your API keys (if needed):"
echo "     ssh ${VPS_USER}@${VPS_IP} 'nano ${REMOTE_DIR}/.env'"
echo ""
echo "  2. Check status:"
echo "     ssh ${VPS_USER}@${VPS_IP} 'systemctl status ${SERVICE_NAME}'"
echo ""
echo "  3. Live logs:"
echo "     ssh ${VPS_USER}@${VPS_IP} 'journalctl -u ${SERVICE_NAME} -f'"
echo ""
echo "  4. Dashboard URL:"
echo "     http://${VPS_IP}:${DASHBOARD_PORT}"
echo "═══════════════════════════════════════════════════"
