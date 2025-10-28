#!/bin/bash
set -e

# Get API key
if [ -z "$RCP_API_KEY" ]; then
    echo "Get your API key from: https://portal.rcp.epfl.ch/aiaas/keys"
    read -p "Enter API key: " api_key
    export RCP_API_KEY="$api_key"
fi

# Choose language
echo "Translate: (1) German (2) French (3) Both"
read -p "Choice: " choice

case $choice in
    1) LANG="de" ;;
    2) LANG="fr" ;;
    *) LANG="both" ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Translate
node "$SCRIPT_DIR/auto-translate.js" --lang=$LANG --resume

# Validate
if [ $? -eq 0 ]; then
    node "$SCRIPT_DIR/validate-translations.js"
fi
