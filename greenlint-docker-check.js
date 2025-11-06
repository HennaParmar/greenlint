//usr/bin/env node
// Simple Dockerfile heuristics for container sustainability best practices.
const fs = require("fs");
const path = require("path");

const file = process.argv[2] || "Dockerfile";
if (!fs.existsSync(file)) { console.log(JSON.stringify({ findings: [] }, null, 2)); process.exit(0); }
const text = fs.readFileSync(file, "utf8");
const lines = text.split(/\r?\n/);

const findings = [];
function warn(line, rule, msg) { findings.push({ file, line, rule, severity: "MEDIUM", message: msg }); }

lines.forEach((l, i) => {
  const line = l.trim();
  if (/^FROM\s+node:(?!.*alpine)/i.test(line)) warn(i+1, "CT001", "Base image not alpine/minimal; prefer node:alpine or distroless.");
  if (/^USER\s+root/i.test(line)) warn(i+1, "CT002", "Running as root; use non-root user for security/least-privilege.");
  if (/^\s*RUN\s+npm\s+install\b/.test(line)) warn(i+1, "CT003", "Use `npm ci` for reproducible, faster builds.");
  if (/^COPY\s+\.\s+/.test(line)) warn(i+1, "CT004", "COPY . may include node_modules; ensure .dockerignore exists and excludes it.");
  if (/^FROM\b/.test(line) && !/AS\s+build/i.test(text)) { /* heuristic */ }
});

// Multi-stage build heuristic
if (!/FROM\s+.*\s+AS\s+build/i.test(text) || !/COPY\s+--from=build/i.test(text)) {
  findings.push({ file, line: 0, rule: "CT005", severity: "LOW", message: "Consider multi-stage builds to reduce final image size." });
}

console.log(JSON.stringify({ findings }, null, 2));
