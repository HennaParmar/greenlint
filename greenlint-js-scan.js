/**
 * greenlint-js-scan.js
 * Simple JS sustainability checks (no external packages).
 * Emits findings => {summary, findings[]} in JSON.
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const findings = [];

function walk(dir) {
  const ents = fs.readdirSync(dir, {withFileTypes:true});
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (['node_modules','.git','.husky','.next','dist','build','coverage'].includes(e.name)) continue;
      walk(p);
    } else {
      if (/\.(js|mjs|cjs)$/i.test(e.name)) scanJs(p);
    }
  }
}

function addFinding(file, line, rule, message, severity='MEDIUM') {
  findings.push({ file: path.relative(ROOT, file), line, rule, message, severity });
}

function scanJs(file) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split(/\r?\n/);

// Tighter heuristic: only within ~10 lines and require await/.then
const netRegex = /\b(fetch|axios|superagent|request)\b/i;
for (let i=0;i<lines.length;i++) {
  if (/\b(for\s*\(|for\s+of|for\s+in|while\s*\()\b/.test(lines[i])) {
    for (let j=i; j<Math.min(i+10, lines.length); j++) {
      const lj = lines[j];
      if (netRegex.test(lj) && (/\bawait\b/.test(lj) || /\.then\s*\(/.test(lj))) {
        addFinding(file, j+1, "GLNET001",
          "Network call inside loop; prefer batching (Promise.all) or concurrency control.");
        break;
      }
    }
  }
}



  

  // Heuristic: Express app without compression middleware (GLWEB001)
  // If file uses express() but no 'compression' reference in file
  const usesExpress = /\bexpress\s*\(\s*\)/.test(text) || /require\(['"]express['"]\)/.test(text) || /from\s+['"]express['"]/.test(text);
  const hasCompression = /require\(['"]compression['"]\)/.test(text) || /from\s+['"]compression['"]/.test(text) || /\bcompression\s*\(/.test(text);
  if (usesExpress && !hasCompression) {
    // try best line
    const lineIndex = lines.findIndex(l => /\bexpress\s*\(\s*\)/.test(l) || /require\(['"]express['"]\)/.test(l));
    addFinding(file, lineIndex >=0 ? lineIndex+1 : 0, "GLWEB001",
      "Express app detected without compression middleware; enable gzip/Brotli (e.g., compression()).","LOW");
  }

  // Heuristic: express.static without cache options (GLWEB002)
  for (let i=0;i<lines.length;i++) {
    const l = lines[i];
    if (/express\.static\s*\(/.test(l)) {
      // If the next argument object isn't visible on this or next line, warn
      const windowText = [l, lines[i+1]||"", lines[i+2]||""].join("\n");
      const hasOptionsObject = /express\.static\s*\([^)]*\)\s*,\s*\{/.test(windowText) || /,\s*\{\s*[^}]*\}/.test(windowText);
      if (!hasOptionsObject) {
        addFinding(file, i+1, "GLWEB002",
          "Static assets served without explicit cache options; set Cache-Control/ETag (e.g., maxAge, etag).","LOW");
      }
    }
  }

}
// Run
walk(ROOT);
const out = { summary: { total_findings: findings.length }, findings };
fs.writeFileSync('greenlint_js.json', JSON.stringify(out, null, 2), 'utf8');
console.log(`JS scan findings: ${findings.length}`);
