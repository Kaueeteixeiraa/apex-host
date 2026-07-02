#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Execute como root para permitir instalacao de pacotes, firewall e timers:"
  echo "sudo bash $0"
  exit 1
fi

echo "==> Apex Host Go Live"
export APP_DIR="${APP_DIR:-${INSTALL_DIR:-/opt/apex-host}}"
bash "$SCRIPT_DIR/install.sh"
bash "$APP_DIR/scripts/bootstrap-production.sh"

if [[ "${SKIP_APEX_REALMS:-false}" != "true" ]]; then
  bash "$APP_DIR/scripts/publish-apex-realms.sh"
else
  echo "Apex Realms publication skipped because SKIP_APEX_REALMS=true"
fi

if bash "$APP_DIR/scripts/check-vps.sh"; then
  echo
  echo "[OK] Ambiente pronto para producao"
else
  echo
  echo "[ERRO] Ambiente ainda precisa de correcoes. Veja a lista acima."
  exit 1
fi
