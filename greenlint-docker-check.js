/**
 * greenlint-docker-check.js
 * Simple Dockerfile heuristics for container sustainability best practices.
 * Scans Dockerfiles under client/ and server/, emits { findings: [...] } JSON.
 *
 * Rules:
 *  CT001: Base image not alpine/minimal (prefer node:*-alpine or distroless)
 *  CT002: USER root (prefer non-root)
 *  CT009: No USER specified at all (container runs as root by default)
 *  CT003: Uses `npm install` instead of `npm ci`
 *  CT004: `COPY .` risks copying large/unnecessary files (ensure .dockerignore)
 *  CT006: Debian/Ubuntu `apt-get install` without --no-install-recommends
 *  CT005: Missing multi-stage pattern (no FROM ... AS build / COPY --from=build)
 */

const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const TARGET_DIRS = ["client", "server"];
const SKIP_DIRS = new Set(["node_modules", ".git", "dist", "build", "coverage", ".next"]);
const findings = [];

function addFinding(file, line, rule, message, severity = "MEDIUM") {
  findings.push({
    file: path.relative(ROOT, file),
    line,
    rule,
    severity,
    message,
  });
}

function scanDockerfile(file) {
  const text = fs.readFileSync(file, "utf8");
  const lines = text.split(/\r?\n/);

  let sawUser = false;

  lines.forEach((l, i) => {
    const line = l.trim();

    // CT001: Base image not minimal/alpine
    // e.g., FROM node:20  (not alpine)
    if (/^FROM\s+node:(?!.*alpine)/i.test(line)) {
      addFinding(
        file,
        i + 1,
        "CT001",
        "Base image not alpine/minimal; prefer node:<version>-alpine or a distroless/base-minimal image.",
        "LOW"
      );
    }

    // Track USER presence
    if (/^USER\b/i.test(line)) {
      sawUser = true;
      // CT002: Explicitly running as root
      if (/^USER\s+root\b/i.test(line)) {
        addFinding(
          file,
          i + 1,
          "CT002",
          "Running as root; add a non-root user (USER node/app) for least privilege.",
          "MEDIUM"
        );
      }
    }

    // CT003: npm install (prefer npm ci)
    if (/^\s*RUN\s+npm\s+install\b/i.test(line)) {
      addFinding(
        file,
        i + 1,
        "CT003",
        "Use `npm ci` for reproducible, cache-friendly builds (and faster installs).",
        "LOW"
      );
    }

    // CT004: COPY . (risk of large build context)
    if (/^\s*COPY\s+\.\s+/i.test(line)) {
      addFinding(
        file,
        i + 1,
        "CT004",
        "COPY . may include node_modules/tests/docs; ensure a .dockerignore and copy only required paths.",
        "LOW"
      );
    }

    // CT006: apt-get install without --no-install-recommends (Debian/Ubuntu images)
    if (
      /^\s*RUN\s+apt-get\s+update.*&&.*apt-get\s+install\b/i.test(line) &&
      !/--no-install-recommends/i.test(line)
    ) {
      addFinding(
        file,
        i + 1,
        "CT006",
        "Use `--no-install-recommends` with apt-get install to reduce image bloat.",
        "LOW"
      );
    }
  });

  // CT009: No USER at all → container defaults to root
  if (!sawUser) {
    addFinding(
      file,
      0,
      "CT009",
      "No USER specified; container defaults to root. Add a non-root USER in the final stage.",
      "LOW"
    );
  }

  // CT005: Multi-stage build heuristic:
  // Expect both: (1) a builder stage  FROM ... AS build   and
  //              (2) COPY --from=build in a later stage
  const hasBuildStage = /(^|\n)\s*FROM\s+[^\s]+(?:\s+AS\s+build)\b/i.test(text);
  const copiesFromBuild = /COPY\s+--from=build\b/i.test(text);
  if (!(hasBuildStage && copiesFromBuild)) {
    addFinding(
      file,
      0,
      "CT005",
      "Consider a multi-stage build (FROM ... AS build + COPY --from=build) to ship only runtime artifacts.",
      "LOW"
    );
  }
}

function walk(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (SKIP_DIRS.has(e.name)) continue;
      walk(p);
    } else {
      // Only scan files literally named "Dockerfile" (case-insensitive)
      if (/^Dockerfile$/i.test(e.name)) {
        try {
          scanDockerfile(p);
        } catch (err) {
          addFinding(p, 0, "CT000", `Failed to parse Dockerfile: ${err.message || String(err)}`, "LOW");
        }
      }
    }
  }
}

/* ------------------------------- Run Scan ------------------------------ */
for (const folder of TARGET_DIRS) {
  const dirPath = path.join(ROOT, folder);
  if (fs.existsSync(dirPath)) {
    walk(dirPath);
  } else {
    // Not fatal—just skip if the folder doesn't exist
    // console.warn(`Skipping missing folder: ${folder}`);
  }
}

fs.writeFileSync("greenlint_docker.json", JSON.stringify({ findings }, null, 2), "utf8");
console.log(`Dockerfile scan findings: ${findings.length}`);
