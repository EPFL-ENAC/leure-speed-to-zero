#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const API_KEY =
  process.argv.find((a) => a.startsWith('--api-key='))?.split('=')[1] || process.env.RCP_API_KEY;
const LANG = process.argv.find((a) => a.startsWith('--lang='))?.split('=')[1];
const CHUNK_SIZE =
  parseInt(process.argv.find((a) => a.startsWith('--chunk-size='))?.split('=')[1]) || 50;
const RESUME = process.argv.includes('--resume');

const LANGUAGES = {
  de: { name: 'German', code: 'de-DE' },
  fr: { name: 'French', code: 'fr-FR' },
};

const I18N_DIR = path.join(__dirname, '../src/i18n');
const PROGRESS_DIR = path.join(__dirname, '../.translation-progress');

function extractTranslations(content) {
  const translations = [];
  const lines = content.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(/^\s*'([^']+)':\s*'([^']*)'/);
    if (match) {
      translations.push({ key: match[1], value: match[2] });
    }
  }
  return translations;
}

function generatePrompt(chunk, lang) {
  const content = chunk.map((t) => `  '${t.key}': '${t.value}',`).join('\n');
  return `Translate this i18n file from English to ${LANGUAGES[lang].name}. Keep keys unchanged, translate only values. Preserve technical terms in brackets like [TWh]. Output only the TypeScript object:\n\n{\n${content}\n}`;
}

async function callAPI(prompt) {
  const res = await fetch('https://inference.rcp.epfl.ch/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${API_KEY}` },
    body: JSON.stringify({
      model: 'Qwen/Qwen3-30B-A3B-Instruct-2507-bfloat16',
      // model: 'swiss-ai/Apertus-8B-Instruct-2509-bfloat16',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.01,
    }),
  });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return data.choices[0].message.content.replace(/```(?:typescript)?\s*\n?|\n?```/g, '').trim();
}

function saveProgress(lang, index, content) {
  fs.mkdirSync(PROGRESS_DIR, { recursive: true });
  const file = path.join(PROGRESS_DIR, `${lang}-plotLabels.ts.json`);
  const progress = fs.existsSync(file)
    ? JSON.parse(fs.readFileSync(file, 'utf-8'))
    : { chunks: {} };
  progress.chunks[index] = content;
  progress.lastChunk = index;
  fs.writeFileSync(file, JSON.stringify(progress, null, 2));
}

async function translate(lang, translations) {
  console.log(`\n🌍 Translating to ${LANGUAGES[lang].name}...`);

  const chunks = [];
  for (let i = 0; i < translations.length; i += CHUNK_SIZE) {
    chunks.push(translations.slice(i, i + CHUNK_SIZE));
  }

  const progressFile = path.join(PROGRESS_DIR, `${lang}-plotLabels.ts.json`);
  let start = 0;
  if (RESUME && fs.existsSync(progressFile)) {
    const progress = JSON.parse(fs.readFileSync(progressFile, 'utf-8'));
    start = (progress.lastChunk || -1) + 1;
    console.log(`📍 Resuming from chunk ${start + 1}/${chunks.length}`);
  }

  for (let i = start; i < chunks.length; i++) {
    console.log(`📦 Processing chunk ${i + 1}/${chunks.length}...`);
    try {
      const prompt = generatePrompt(chunks[i], lang);
      const result = await callAPI(prompt);
      const cleaned =
        result.startsWith('{') && result.endsWith('}') ? result.slice(1, -1).trim() : result;
      saveProgress(lang, i, cleaned);
      await new Promise((r) => setTimeout(r, 600)); // Rate limit
    } catch (err) {
      console.error(`❌ Error at chunk ${i + 1}:`, err.message);
      throw err;
    }
  }

  // Assemble final file
  const progress = JSON.parse(fs.readFileSync(progressFile, 'utf-8'));
  const content = ['export default {'];
  Object.keys(progress.chunks)
    .sort((a, b) => a - b)
    .forEach((i) => {
      content.push(progress.chunks[i]);
    });
  content.push('};');

  const outFile = path.join(I18N_DIR, LANGUAGES[lang].code, 'plotLabels.ts');
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, content.join('\n'));
  console.log(`✅ Saved to ${outFile}`);
}

async function main() {
  if (!LANG || !['de', 'fr', 'both'].includes(LANG)) {
    console.error('Usage: node auto-translate.js --lang=<de|fr|both>');
    process.exit(1);
  }

  if (!API_KEY) {
    console.error('Error: Set RCP_API_KEY environment variable');
    process.exit(1);
  }

  const source = fs.readFileSync(path.join(I18N_DIR, 'en-US/plotLabels.ts'), 'utf-8');
  const translations = extractTranslations(source);
  console.log(`Found ${translations.length} translations`);

  const langs = LANG === 'both' ? ['de', 'fr'] : [LANG];
  for (const lang of langs) {
    await translate(lang, translations);
  }

  console.log('\n✨ Done! Run: node scripts/validate-translations.js');
}

main().catch(console.error);
