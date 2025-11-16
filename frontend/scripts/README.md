# Translation Scripts

Automated translation of i18n files using EPFL RCP AI.

## Quick Start

```bash
export RCP_API_KEY="sk-your-key-here"  # Get from https://portal.rcp.epfl.ch/aiaas/keys
./scripts/translate.sh
```

## Scripts

- **`translate.sh`** - Interactive translation tool
- **`auto-translate.js`** - Automated API translation
- **`validate-translations.js`** - Verify translation completeness

## Usage

```bash
# Translate both languages
node scripts/auto-translate.js --lang=both

# Validate
node scripts/validate-translations.js

# Resume interrupted translation
node scripts/auto-translate.js --lang=de --resume
```
