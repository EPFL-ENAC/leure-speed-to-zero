#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const LANG = process.argv.find((a) => a.startsWith('--lang='))?.split('=')[1] || 'all';
const I18N_DIR = path.join(__dirname, '../src/i18n');

function extractKeys(content) {
  const keys = [];
  for (const line of content.split('\n')) {
    const match = line.match(/^\s*'([^']+)':/);
    if (match) keys.push(match[1]);
  }
  return keys;
}

function validate(source, target, lang) {
  console.log(`\n🔍 Validating ${lang}/plotLabels.ts...`);

  const srcFile = path.join(I18N_DIR, source, 'plotLabels.ts');
  const tgtFile = path.join(I18N_DIR, lang, 'plotLabels.ts');

  if (!fs.existsSync(srcFile)) {
    console.error(`❌ Source file not found: ${srcFile}`);
    return false;
  }

  if (!fs.existsSync(tgtFile)) {
    console.error(`❌ Target file not found: ${tgtFile}`);
    return false;
  }

  const srcKeys = extractKeys(fs.readFileSync(srcFile, 'utf-8'));
  const tgtKeys = extractKeys(fs.readFileSync(tgtFile, 'utf-8'));

  const missing = srcKeys.filter((k) => !tgtKeys.includes(k));
  const extra = tgtKeys.filter((k) => !srcKeys.includes(k));

  if (missing.length > 0) {
    console.error(`❌ Missing ${missing.length} keys:`, missing.slice(0, 5));
    return false;
  }

  if (extra.length > 0) {
    console.error(`⚠️  Extra ${extra.length} keys:`, extra.slice(0, 5));
    return false;
  }

  console.log(`✅ Perfect! ${srcKeys.length} keys match.`);
  return true;
}

const langs = LANG === 'all' ? ['de-DE', 'fr-FR'] : [LANG === 'de' ? 'de-DE' : 'fr-FR'];
const results = langs.map((lang) => validate('en-US', lang, lang));

console.log('\n' + '='.repeat(40));
console.log(results.every((r) => r) ? '🎉 All valid!' : '⚠️  Fix issues above');
console.log('='.repeat(40) + '\n');

process.exit(results.every((r) => r) ? 0 : 1);
