#!/usr/bin/env bash
set -e

# Robin install script
# Usage: bash install.sh [--vault PATH] [--robin-home PATH]

ROBIN_HOME="${ROBIN_HOME:-}"
VAULT_PATH=""
FORCE=0
declare -a FAILURES=()

resolve_paths() {
  if [[ -n "$ROBIN_HOME" ]]; then
    CONFIG_DIR="$ROBIN_HOME/config"
    DATA_DIR="$ROBIN_HOME/data"
  elif [[ -n "${XDG_CONFIG_HOME:-}" || -n "${XDG_DATA_HOME:-}" ]]; then
    CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/robin"
    DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/robin"
  elif [[ -n "${HERMES_HOME:-}" ]]; then
    CONFIG_DIR="$HERMES_HOME/data"
    DATA_DIR="$HERMES_HOME/data"
  else
    CONFIG_DIR="$HOME/.config/robin"
    DATA_DIR="$HOME/.local/share/robin"
  fi

  CONFIG_FILE="$CONFIG_DIR/robin-config.json"
  INDEX_FILE="$DATA_DIR/robin-review-index.json"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --vault)
        VAULT_PATH="$2"
        shift 2
        ;;
      --robin-home)
        ROBIN_HOME="$2"
        shift 2
        ;;
      --force)
        FORCE=1
        shift
        ;;
      *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
  done
}

record_failure() {
  FAILURES+=("$1")
}

check_requirements() {
  local repo_root
  repo_root="$(cd "$(dirname "$0")" && pwd)"

  if ! command -v python3 &>/dev/null; then
    record_failure "python3 is required"
  else
    if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
      local detected_version
      detected_version="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
      record_failure "Python 3.11+ is required (found ${detected_version})"
    fi
  fi

  if [[ ! -f "$repo_root/references/robin-config.json.example" ]]; then
    record_failure "missing references/robin-config.json.example"
  fi

  if [[ ! -f "$repo_root/scripts/add_entry.py" ]]; then
    record_failure "missing scripts/add_entry.py"
  fi

  if [[ ! -d "$repo_root/src/robin" ]]; then
    record_failure "missing src/robin package"
  fi

  if [[ ! -d "$CONFIG_DIR" && ! -w "$(dirname "$CONFIG_DIR")" ]]; then
    record_failure "cannot create config directory at $CONFIG_DIR"
  fi

  if [[ ! -d "$DATA_DIR" && ! -w "$(dirname "$DATA_DIR")" ]]; then
    record_failure "cannot create data directory at $DATA_DIR"
  fi

  if [[ -n "$VAULT_PATH" ]]; then
    mkdir -p "$VAULT_PATH" 2>/dev/null || record_failure "cannot create or write to vault path $VAULT_PATH"
  fi

  if [[ ${#FAILURES[@]} -gt 0 ]]; then
    echo "ERROR: Robin cannot be installed because the following requirements are not met:"
    for failure in "${FAILURES[@]}"; do
      echo "  - $failure"
    done
    echo ""
    echo "Fix the missing requirements and re-run install.sh. No dependencies were installed."
    exit 1
  fi

  echo "✓ Requirements satisfied"
  echo "✓ Python $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
}

setup_directories() {
  mkdir -p "$CONFIG_DIR"
  mkdir -p "$DATA_DIR"
  echo "✓ State directories ready"
}

setup_config() {
  local example_file="$(dirname "$0")/references/robin-config.json.example"

  if [[ -f "$CONFIG_FILE" && "$FORCE" -eq 0 ]]; then
    echo "✓ Config already exists at $CONFIG_FILE (skipping)"
  else
    if [[ -f "$example_file" ]]; then
      cp "$example_file" "$CONFIG_FILE"
      echo "✓ Created $CONFIG_FILE from example"
    else
      echo "ERROR: example file not found at $example_file"
      exit 1
    fi
  fi
}

setup_index() {
  if [[ -f "$INDEX_FILE" && "$FORCE" -eq 0 ]]; then
    echo "✓ Index already exists (skipping)"
  else
    echo '{"items":{}}' > "$INDEX_FILE"
    echo "✓ Initialized $INDEX_FILE"
  fi
}

setup_vault() {
  local vault_path
  local topics_dir
  local media_dir

  if [[ -n "$VAULT_PATH" ]]; then
    # User specified a vault path — update config
    CONFIG_FILE="$CONFIG_FILE" VAULT_PATH="$VAULT_PATH" python3 -c "
import json
import os
with open(os.environ['CONFIG_FILE'], encoding='utf-8') as f:
    cfg = json.load(f)
cfg['vault_path'] = os.environ['VAULT_PATH']
with open(os.environ['CONFIG_FILE'], 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2)
"
    echo "✓ Vault path set to $VAULT_PATH"
    vault_path="$VAULT_PATH"
  else
    # Read from config
    vault_path=$(CONFIG_FILE="$CONFIG_FILE" python3 -c "
import json
import os
with open(os.environ['CONFIG_FILE'], encoding='utf-8') as f:
    cfg = json.load(f)
print(cfg.get('vault_path', ''))
" 2>/dev/null || echo "")
  fi

  topics_dir=$(CONFIG_FILE="$CONFIG_FILE" python3 -c "
import json
import os
with open(os.environ['CONFIG_FILE'], encoding='utf-8') as f:
    cfg = json.load(f)
print(cfg.get('topics_dir', 'topics'))
" 2>/dev/null || echo "topics")

  media_dir=$(CONFIG_FILE="$CONFIG_FILE" python3 -c "
import json
import os
with open(os.environ['CONFIG_FILE'], encoding='utf-8') as f:
    cfg = json.load(f)
print(cfg.get('media_dir', 'media'))
" 2>/dev/null || echo "media")

  if [[ -n "$vault_path" ]]; then
    mkdir -p "$vault_path/$topics_dir" "$vault_path/$media_dir"
    echo "✓ Vault ready at $vault_path/$topics_dir/"
    echo "✓ Media ready at $vault_path/$media_dir/"
  else
    echo "WARNING: No vault_path set in $CONFIG_FILE — set it manually or run with --vault"
  fi
}

main() {
  echo "Robin install"
  echo "============="
  echo ""

  parse_args "$@"
  resolve_paths

  [[ -n "$ROBIN_HOME" ]] && echo "ROBIN_HOME:  $ROBIN_HOME"
  echo "CONFIG_DIR:  $CONFIG_DIR"
  echo "DATA_DIR:    $DATA_DIR"
  [[ -n "$VAULT_PATH" ]] && echo "VAULT:       $VAULT_PATH"
  echo ""

  check_requirements
  setup_directories
  setup_config
  setup_index
  setup_vault

  echo ""
  echo "Done! Next steps:"
  echo "  1. Edit $CONFIG_FILE to set your vault_path"
  echo "  2. Start filing: send Robin content to collect"
  echo "  3. Set up periodic review in your agent host"
}

main "$@"
