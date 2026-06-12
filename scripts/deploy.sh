#!/usr/bin/env bash
set -euo pipefail

APP_NAME="BettaFish"
APP_PORT_DEFAULT="5050"
POSTGRES_PORT_DEFAULT="5444"
DRY_RUN=0
SKIP_INSTALL=0
SKIP_BUILD=0
INSTALL_SHORTCUTS=1
INSTALL_SYSTEMD=1

log() { printf '\033[1;34m[%s]\033[0m %s\n' "$APP_NAME" "$*"; }
warn() { printf '\033[1;33m[%s]\033[0m %s\n' "$APP_NAME" "$*" >&2; }
fail() { printf '\033[1;31m[%s]\033[0m %s\n' "$APP_NAME" "$*" >&2; exit 1; }

usage() {
  cat <<USAGE
Usage: bash scripts/deploy.sh [options]

Options:
  --dry-run        Print actions without changing the server.
  --skip-install   Do not install or update server dependencies.
  --skip-build     Run docker compose up without rebuilding the image.
  --no-shortcuts   Do not install the global bf command.
  --no-systemd     Do not install systemd boot/health units.
  -h, --help       Show this help.

Environment overrides:
  APP_PORT=5050       Host port for the Flask app.
  POSTGRES_PORT=5444  Host port for PostgreSQL.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --skip-install) SKIP_INSTALL=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    --no-shortcuts) INSTALL_SHORTCUTS=0 ;;
    --no-systemd) INSTALL_SYSTEMD=0 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
  shift
done

run() {
  log "+ $*"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  "$@"
}

sudo_run() {
  if [[ "${EUID}" -eq 0 ]]; then
    run "$@"
  else
    command -v sudo >/dev/null 2>&1 || fail "sudo is required when not running as root."
    run sudo "$@"
  fi
}

ensure_project_root() {
  [[ -f "docker-compose.yml" && -f "Dockerfile" && -f ".env.example" ]] || \
    fail "Run this script from the BettaFish project root."
}

install_with_get_docker() {
  command -v curl >/dev/null 2>&1 || sudo_run apt-get install -y curl || true
  log "Installing Docker via get.docker.com fallback."
  if [[ "$DRY_RUN" == "1" ]]; then
    log "+ curl -fsSL https://get.docker.com | sh"
    return 0
  fi
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo_run sh /tmp/get-docker.sh
}

install_dependencies() {
  [[ "$SKIP_INSTALL" == "0" ]] || { log "Skipping dependency installation."; return 0; }

  if command -v apt-get >/dev/null 2>&1; then
    sudo_run apt-get update
    sudo_run apt-get install -y ca-certificates curl git openssl
    command -v docker >/dev/null 2>&1 || sudo_run apt-get install -y docker.io || install_with_get_docker
    docker compose version >/dev/null 2>&1 || sudo_run apt-get install -y docker-compose-plugin || sudo_run apt-get install -y docker-compose || install_with_get_docker
  elif command -v dnf >/dev/null 2>&1; then
    sudo_run dnf install -y ca-certificates curl git openssl
    command -v docker >/dev/null 2>&1 || sudo_run dnf install -y docker || install_with_get_docker
    docker compose version >/dev/null 2>&1 || sudo_run dnf install -y docker-compose-plugin || install_with_get_docker
  elif command -v yum >/dev/null 2>&1; then
    sudo_run yum install -y ca-certificates curl git openssl
    command -v docker >/dev/null 2>&1 || sudo_run yum install -y docker || install_with_get_docker
    docker compose version >/dev/null 2>&1 || sudo_run yum install -y docker-compose-plugin || install_with_get_docker
  elif command -v apk >/dev/null 2>&1; then
    sudo_run apk add --no-cache ca-certificates curl git openssl docker docker-cli-compose
  else
    warn "Unsupported package manager. Trying Docker official installer if Docker is missing."
    command -v docker >/dev/null 2>&1 || install_with_get_docker
  fi

  if command -v systemctl >/dev/null 2>&1; then
    sudo_run systemctl enable --now docker || warn "Could not start Docker with systemctl."
  elif command -v service >/dev/null 2>&1; then
    sudo_run service docker start || warn "Could not start Docker service."
  fi
}

docker_run() {
  if docker info >/dev/null 2>&1; then
    run docker "$@"
  else
    sudo_run docker "$@"
  fi
}

compose_run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    log "+ docker compose $*"
    return 0
  fi
  if docker info >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    run docker compose "$@"
  elif [[ "${EUID}" -ne 0 ]] && command -v sudo >/dev/null 2>&1 && sudo docker compose version >/dev/null 2>&1; then
    run sudo docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    run docker-compose "$@"
  elif [[ "${EUID}" -ne 0 ]] && command -v sudo >/dev/null 2>&1 && sudo docker-compose version >/dev/null 2>&1; then
    run sudo docker-compose "$@"
  else
    fail "Docker Compose is not available."
  fi
}

random_secret() {
  openssl rand -hex 24
}

ensure_env_file() {
  if [[ ! -f ".env" ]]; then
    log "Creating .env from .env.example."
    if [[ "$DRY_RUN" == "1" ]]; then
      log "+ cp .env.example .env"
    else
      cp .env.example .env
    fi
  fi
}

get_env_value() {
  local key="$1"
  [[ -f ".env" ]] || return 0
  awk -v key="$key" '
    index($0, key "=") == 1 {
      value = substr($0, length(key) + 2)
    }
    END {
      gsub(/^"/, "", value)
      gsub(/"$/, "", value)
      print value
    }
  ' .env
}

set_env_value() {
  local key="$1"
  local value="$2"
  log "Set ${key} in .env"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  local tmp
  tmp="$(mktemp)"
  if grep -qE "^${key}=" .env; then
    awk -v key="$key" -v value="$value" 'BEGIN{done=0} $0 ~ "^" key "=" {print key "=" value; done=1; next} {print} END{if(!done) print key "=" value}' .env > "$tmp"
  else
    cat .env > "$tmp"
    printf '%s=%s\n' "$key" "$value" >> "$tmp"
  fi
  mv "$tmp" .env
}

is_placeholder() {
  local value="${1:-}"
  case "$value" in
    ""|your_*|your-*|changeme|change_me|password|bettafish) return 0 ;;
    *) return 1 ;;
  esac
}

set_if_missing() {
  local key="$1"
  local value="$2"
  local current
  current="$(get_env_value "$key")"
  if is_placeholder "$current"; then
    set_env_value "$key" "$value"
  fi
}

configure_env() {
  ensure_env_file

  local app_port="${APP_PORT:-$APP_PORT_DEFAULT}"
  local pg_port="${POSTGRES_PORT:-$POSTGRES_PORT_DEFAULT}"
  local pg_user pg_db pg_password secret_key

  pg_user="$(get_env_value POSTGRES_USER)"
  is_placeholder "$pg_user" && pg_user="$(get_env_value DB_USER)"
  is_placeholder "$pg_user" && pg_user="bettafish"

  pg_db="$(get_env_value POSTGRES_DB)"
  is_placeholder "$pg_db" && pg_db="$(get_env_value DB_NAME)"
  is_placeholder "$pg_db" && pg_db="bettafish"

  pg_password="$(get_env_value POSTGRES_PASSWORD)"
  is_placeholder "$pg_password" && pg_password="$(get_env_value DB_PASSWORD)"
  is_placeholder "$pg_password" && pg_password="$(random_secret)"

  secret_key="$(get_env_value SECRET_KEY)"
  is_placeholder "$secret_key" && secret_key="$(random_secret)$(random_secret)"

  set_if_missing APP_PORT "$app_port"
  set_if_missing POSTGRES_PORT "$pg_port"
  set_if_missing POSTGRES_USER "$pg_user"
  set_if_missing POSTGRES_PASSWORD "$pg_password"
  set_if_missing POSTGRES_DB "$pg_db"
  set_if_missing SECRET_KEY "$secret_key"
  set_if_missing BETTAFISH_MEMORY_LIMIT "3g"
  set_if_missing BETTAFISH_SWAP_LIMIT "4g"
  set_if_missing BETTAFISH_LOG_MAX_SIZE "20m"
  set_if_missing BETTAFISH_LOG_MAX_FILE "5"
  set_if_missing POSTGRES_LOG_MAX_SIZE "10m"
  set_if_missing POSTGRES_LOG_MAX_FILE "3"

  set_if_missing HOST "0.0.0.0"
  set_if_missing PORT "5000"
  set_if_missing DB_DIALECT "postgresql"
  set_if_missing DB_HOST "db"
  set_if_missing DB_PORT "5432"
  set_if_missing DB_USER "$pg_user"
  set_if_missing DB_PASSWORD "$pg_password"
  set_if_missing DB_NAME "$pg_db"
  set_if_missing DB_CHARSET "utf8mb4"
  set_if_missing SEARCH_TOOL_TYPE "AnspireAPI"
  set_if_missing SMTP_ENABLED "False"
  set_if_missing EPAY_ENABLED "False"
}

prepare_runtime_dirs() {
  for dir in logs final_reports insight_engine_streamlit_reports media_engine_streamlit_reports query_engine_streamlit_reports db_data; do
    run mkdir -p "$dir"
  done
}

install_shortcuts() {
  [[ "$INSTALL_SHORTCUTS" == "1" ]] || { log "Skipping bf shortcut installation."; return 0; }
  [[ -f "scripts/bf" ]] || { warn "scripts/bf not found; skipping shortcuts."; return 0; }

  run chmod +x scripts/bf

  if [[ "$DRY_RUN" == "1" ]]; then
    log "+ install -m 0755 scripts/bf /usr/local/bin/bf"
    log "+ write APP_DIR=$(pwd) to /etc/bettafish/bf.env"
    [[ "$INSTALL_SYSTEMD" == "1" ]] && log "+ bf install-systemd"
    return 0
  fi

  if [[ "$INSTALL_SYSTEMD" == "1" && -d /run/systemd/system && -x "$(command -v systemctl 2>/dev/null)" ]]; then
    bash scripts/bf install-systemd || warn "Failed to install systemd units; bf command may still work from scripts/bf."
    return 0
  fi

  sudo_run install -d -m 0755 /etc/bettafish
  sudo_run install -m 0755 scripts/bf /usr/local/bin/bf
  printf 'APP_DIR=%q\n' "$(pwd)" | sudo_run tee /etc/bettafish/bf.env >/dev/null
  log "Installed /usr/local/bin/bf."
}

start_stack() {
  if [[ "$SKIP_BUILD" == "1" ]]; then
    compose_run up -d
  else
    compose_run up -d --build
  fi
  compose_run ps
}

health_check() {
  local app_port
  app_port="$(get_env_value APP_PORT)"
  [[ -n "$app_port" ]] || app_port="$APP_PORT_DEFAULT"

  if [[ "$DRY_RUN" == "1" ]]; then
    log "Would check http://127.0.0.1:${app_port}/radar/"
    return 0
  fi

  log "Waiting for http://127.0.0.1:${app_port}/radar/ ..."
  for _ in $(seq 1 40); do
    if curl -fsSI "http://127.0.0.1:${app_port}/radar/" >/dev/null 2>&1; then
      log "Deploy finished: http://127.0.0.1:${app_port}/radar/"
      log "Register the first Radar account to become super admin, then configure API keys/URLs in Platform Settings."
      return 0
    fi
    sleep 3
  done

  warn "Container started, but health check did not pass yet. Inspect logs with: docker compose logs -f bettafish"
}

main() {
  ensure_project_root
  install_dependencies
  configure_env
  prepare_runtime_dirs
  start_stack
  install_shortcuts
  health_check
}

main "$@"
