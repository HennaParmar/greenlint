/**
 * greenlint-js-scan.js
 * Simple JS sustainability checks (no external packages).
 * Emits findings => {summary, findings[]} in JSON.
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const findings = [];

/* ------------------------- filesystem walking ------------------------- */
function walk(dir) {
  const ents = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (['node_modules', '.git', '.husky', '.next', 'dist', 'build', 'coverage'].includes(e.name)) continue;
      walk(p);
    } else {
      if (/\.(js|mjs|cjs)$/i.test(e.name)) scanJs(p);
    }
  }
}

function addFinding(file, line, rule, message, severity = 'MEDIUM') {
  findings.push({ file: path.relative(ROOT, file), line, rule, message, severity });
}

/* ------------------------------ scanners ------------------------------ */
function scanJs(file) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split(/\r?\n/);

  /* GLNET001: Network call inside loop with await/.then (prefer batching/limits) */
  const netRegex = /\b(fetch|axios|superagent|request)\b/i;
  for (let i = 0; i < lines.length; i++) {
    if (/\b(for\s*\(|for\s+of|for\s+in|while\s*\()\b/.test(lines[i])) {
      for (let j = i; j < Math.min(i + 10, lines.length); j++) {
        const lj = lines[j];
        if (netRegex.test(lj) && (/\bawait\b/.test(lj) || /\.then\s*\(/.test(lj))) {
          addFinding(
            file,
            j + 1,
            'GLNET001',
            'Network call inside loop; prefer batching (Promise.all) or concurrency control.'
          );
          break;
        }
      }
    }
  }

  /* GLWEB001: Express app without compression middleware */
  const usesExpress =
    /\bexpress\s*\(\s*\)/.test(text) ||
    /require\(['"]express['"]\)/.test(text) ||
    /from\s+['"]express['"]/.test(text);
  const hasCompression =
    /require\(['"]compression['"]\)/.test(text) ||
    /from\s+['"]compression['"]/.test(text) ||
    /\bcompression\s*\(/.test(text);
  if (usesExpress && !hasCompression) {
    const lineIndex = lines.findIndex(
      (l) => /\bexpress\s*\(\s*\)/.test(l) || /require\(['"]express['"]\)/.test(l)
    );
    addFinding(
      file,
      lineIndex >= 0 ? lineIndex + 1 : 0,
      'GLWEB001',
      'Express app detected without compression middleware; enable gzip/Brotli (e.g., compression()).',
      'LOW'
    );
  }

  /* GLWEB002: express.static without cache options */
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/express\.static\s*\(/.test(l)) {
      const windowText = [l, lines[i + 1] || '', lines[i + 2] || ''].join('\n');
      const hasOptionsObject =
        /express\.static\s*\([^)]*\)\s*,\s*\{/.test(windowText) || /,\s*\{\s*[^}]*\}/.test(windowText);
      if (!hasOptionsObject) {
        addFinding(
          file,
          i + 1,
          'GLWEB002',
          'Static assets served without explicit cache options; set Cache-Control/ETag (e.g., maxAge, etag).',
          'LOW'
        );
      }
    }
  }

  /* -------------------------- NEW: extra rules -------------------------- */

  // GLTPL001 – Nunjucks watch/noCache in production (disable in prod)
  if (/nunjucks\s*\(\s*app\s*,\s*\{[^}]*\b(watch|noCache)\s*:\s*true/i.test(text)) {
    const i = lines.findIndex((l) => /nunjucks\s*\(\s*app\s*,/.test(l));
    addFinding(
      file,
      i + 1,
      'GLTPL001',
      'Nunjucks configured with watch/noCache=true; disable in production to avoid extra FS work.',
      'LOW'
    );
  }

  // GLREQ001 – bodyParser.json without payload size limit
  const bpJsonNoArgs = /bodyParser\.json\s*\(\s*\)/.test(text);
  const bpJsonWithCfgNoLimit =
    /bodyParser\.json\s*\(\s*\{[^}]*\}\s*\)/.test(text) && !/bodyParser\.json\s*\(\s*\{[^}]*(?:^|,)\s*limit\s*:/m.test(text);
  if (bpJsonNoArgs || bpJsonWithCfgNoLimit) {
    const i = lines.findIndex((l) => /bodyParser\.json\s*\(/.test(l));
    addFinding(
      file,
      i + 1,
      'GLREQ001',
      "bodyParser.json() has no size limit; set e.g. { limit: '1mb' } to reduce CPU/memory spikes.",
      'LOW'
    );
  }

  // GLSESS001 – express-session MemoryStore used (no store configured)
  const sess = text.match(/app\.use\s*\(\s*session\s*\(\s*\{([\s\S]*?)\}\s*\)\s*\)/);
  if (sess && !/[\s,{]store\s*:/.test(sess[1])) {
    const i = lines.findIndex((l) => /app\.use\s*\(\s*session\s*\(/.test(l));
    addFinding(
      file,
      i + 1,
      'GLSESS001',
      'express-session without a store configured; MemoryStore is inefficient for production.',
      'MEDIUM'
    );
  }

  // GLLOG001 – console.log present (prefer leveled logging)
  if (/\bconsole\.log\s*\(/.test(text)) {
    const i = lines.findIndex((l) => /\bconsole\.log\s*\(/.test(l));
    addFinding(
      file,
      i + 1,
      'GLLOG001',
      'console.log detected; prefer leveled logging (debug/info) toggleable by env to reduce IO in prod.',
      'LOW'
    );
  }

  // GLWEB004 – static assets missing long-term caching (maxAge/immutable)
  for (let i = 0; i < lines.length; i++) {
    if (/express\.static\s*\(/.test(lines[i])) {
      const windowText = [lines[i], lines[i + 1] || '', lines[i + 2] || ''].join('\n');
      const hasOptions = /express\.static\s*\([^)]*\)\s*,\s*\{[^}]*\}/.test(windowText);
      const mentionsMaxAge = /\bmaxAge\s*:/.test(windowText);
      if (!hasOptions || !mentionsMaxAge) {
        addFinding(
          file,
          i + 1,
          'GLWEB004',
          'Static assets without long-term caching; set maxAge and consider immutable for hashed files.',
          'LOW'
        );
      }
    }
  }

  // GLCOOKIE001 – JSON.parse(cookie) without try/catch
  for (let i = 0; i < lines.length; i++) {
    if (
      /JSON\.parse\s*\(\s*cookie\s*\)/.test(lines[i]) &&
      !/try\s*{[\s\S]*JSON\.parse\s*\(\s*cookie\s*\)[\s\S]*}\s*catch/.test(text)
    ) {
      addFinding(
        file,
        i + 1,
        'GLCOOKIE001',
        'JSON.parse(cookie) without try/catch; guard to avoid expensive error paths.',
        'LOW'
      );
    }
  }
}

/* --------------------------------- run -------------------------------- */
const targets = ['client', 'server']; // scan only these
for (const t of targets) {
  const dirPath = path.join(ROOT, t);
  if (fs.existsSync(dirPath)) {
    walk(dirPath);
  } else {
    console.warn(`Skipping missing folder: ${t}`);
  }
}

const out = { summary: { total_findings: findings.length }, findings };
fs.writeFileSync('greenlint_js.json', JSON.stringify(out, null, 2), 'utf8');
console.log(`JS scan findings: ${findings.length}`);
