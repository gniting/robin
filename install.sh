#!/usr/bin/env bash
set -e

# Robin install script
# Usage: bash install.sh [--vault PATH] [--hermes-home PATH]

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
VAULT_PATH=""
FORCE=0

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --vault)
        VAULT_PATH="$2"
        shift 2
        ;;
      --hermes-home)
        HERMES_HOME="$2"
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

check_python() {
  if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
  fi
  PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
  if [[ "$PYTHON_VERSION" -lt 11 ]]; then
    echo "ERROR: Python 3.11+ required (found 3.$PYTHON_VERSION)"
    exit 1
  fi
  echo "✓ Python 3.$PYTHON_VERSION"
}

setup_directories() {
  mkdir -p "$HERMES_HOME/data"
  mkdir -p "$HERMES_HOME/skills/personal"
  echo "✓ Directories ready"
}

setup_config() {
  local config_file="$HERMES_HOME/data/cb-config.json"
  local example_file="$(dirname "$0")/references/cb-config.json.example"

  if [[ -f "$config_file" && "$FORCE" -eq 0 ]]; then
    echo "✓ Config already exists at $config_file (skipping)"
  else
    if [[ -f "$example_file" ]]; then
      cp "$example_file" "$config_file"
      echo "✓ Created $config_file from example"
    else
      echo "ERROR: example file not found at $example_file"
      exit 1
    fi
  fi
}

setup_index() {
  local index_file="$HERMES_HOME/data/cb-review-index.json"
  if [[ -f "$index_file" && "$FORCE" -eq 0 ]]; then
    echo "✓ Index already exists (skipping)"
  else
    echo '{"items":{},"config":{"min_items_before_review":30,"review_cooldown_days":60}}' > "$index_file"
    echo "✓ Initialized $index_file"
  fi
}

setup_vault() {
  local config_file="$HERMES_HOME/data/cb-config.json"
  local vault_path

  if [[ -n "$VAULT_PATH" ]]; then
    # User specified a vault path — update config
    python3 -c "
import json
with open('$config_file') as f:
    cfg = json.load(f)
cfg['vault_path'] = '$VAULT_PATH'
with open('$config_file', 'w') as f:
    json.dump(cfg, f, indent=2)
"
    echo "✓ Vault path set to $VAULT_PATH"
    vault_path="$VAULT_PATH"
  else
    # Read from config
    vault_path=$(python3 -c "
import json
with open('$config_file') as f:
    cfg = json.load(f)
print(cfg.get('vault_path', ''))
" 2>/dev/null || echo "")
  fi

  if [[ -n "$vault_path" ]]; then
    mkdir -p "$vault_path/topics"
    echo "✓ Vault ready at $vault_path/topics/"
  else
    echo "WARNING: No vault_path set in $config_file — set it manually or run with --vault"
  fi
}

main() {
  echo "Robin install"
  echo "============="
  echo ""

  parse_args "$@"

  echo "HERMES_HOME: $HERMES_HOME"
  [[ -n "$VAULT_PATH" ]] && echo "VAULT:       $VAULT_PATH"
  echo ""

  check_python
  setup_directories
  setup_config
  setup_index
  setup_vault

  echo ""
  echo "Done! Next steps:"
  echo "  1. Edit ~/.hermes/data/cb-config.json to set your vault_path"
  echo "  2. Start filing: send Robin content to collect"
  echo "  3. Set up review cron for periodic surfacing"
  echo ""
  echo "For Hermes users:"
  echo "  hermes skills install ~/.hermes/skills/personal/robin"
}

main "$@"
