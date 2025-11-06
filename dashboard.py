import json, os, io, pathlib
import pandas as pd
import streamlit as st

st.set_page_config(page_title="GreenLint Dashboard", layout="wide")
st.title("🌿 GreenLint Report Viewer")

st.caption("Upload one or more GreenLint JSON reports (Python or Java). "
           "Schema expected: findings = [{file, line, rule, message, severity}] + summary.")

# --- Upload one or more reports ---
uploads = st.file_uploader("Upload greenlint_report.json file(s)", type="json", accept_multiple_files=True)

all_rows = []
summaries = []
df = pd.DataFrame()  # Ensure df is always defined

def load_report(fp, name_hint):
    data = json.load(fp)
    # tolerate slightly different schemas
    findings = data.get("findings", data.get("results", []))
    summary = data.get("summary", {})
    for f in findings:
        all_rows.append({
            "report": name_hint,
            "file": f.get("file", ""),
            "line": f.get("line", 0),
            "rule": f.get("rule") or f.get("rule_id", "UNKNOWN"),
            "message": f.get("message", ""),
            "severity": f.get("severity", "MEDIUM"),
        })
    if summary:
        summaries.append({
            "report": name_hint,
            "total_findings": summary.get("total_findings", len(findings)),
            "score": summary.get("score", None)
        })
    else:
        summaries.append({
            "report": name_hint,
            "total_findings": len(findings),
            "score": None
        })

    

if uploads:
    for upl in uploads:
        load_report(upl, upl.name)

    df = pd.DataFrame(all_rows)
    sumdf = pd.DataFrame(summaries).drop_duplicates(subset=["report"])

    col1, col2, col3 = st.columns([2,2,3], gap="large")

    with col1:
        st.subheader("📈 Summary by report")
        st.dataframe(sumdf, use_container_width=True)
        if "score" in sumdf:
            st.bar_chart(sumdf.set_index("report")[["total_findings"]])

    with col2:
        st.subheader("🔎 Filter findings")
        rule_sel = st.multiselect("Rule", sorted(df["rule"].unique()))
        sev_sel = st.multiselect("Severity", sorted(df["severity"].unique()))
        file_sel = st.text_input("Filter by file path contains", "")

        mask = pd.Series([True]*len(df))
        if rule_sel: mask &= df["rule"].isin(rule_sel)
        if sev_sel: mask &= df["severity"].isin(sev_sel)
        if file_sel: mask &= df["file"].str.contains(file_sel, case=False, na=False)

        filtered = df[mask].sort_values(["report","file","line"]).reset_index(drop=True)
        st.metric("Shown findings", len(filtered))
        st.dataframe(filtered, use_container_width=True)

    with col3:
        st.subheader("🧩 Code context")
        st.caption("Pick a finding below to preview source with context.")
        if not df.empty:
            idx = st.number_input("Row index (from filtered table)", min_value=0, max_value=max(0, len(filtered)-1), value=0)
            if len(filtered) > 0:
                row = filtered.iloc[int(idx)]
                st.write(f"**{row['rule']}** — {row['message']}")
                st.write(f"File: `{row['file']}`  |  Line: `{row['line']}`")

                # Try to read local file and show context lines
                file_path = pathlib.Path(row["file"])
                if file_path.exists():
                    try:
                        text = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                        start = max(0, int(row["line"])-6)
                        end = min(len(text), int(row["line"])+5)
                        snip = text[start:end]
                        # annotate lines with numbers
                        numbered = "\n".join(f"{i+1:>5}: {line}" for i, line in enumerate(snip, start=start))
                        st.code(numbered, language="python")  # works for .py/.java display
                    except Exception as e:
                        st.info(f"Could not read local file for preview: {e}")
                else:
                    st.info("Local file not found. To see code preview, run the dashboard from the repo root where the files exist.")
else:
    st.info("Upload at least one `greenlint_report.json` to get started.")

# --- Auto Before/After (rule-aware suggestions) ---
import re
from textwrap import dedent

st.subheader("🛠 Auto Before / After (rule-aware suggestions)")

def read_context(path, line_no, before=5, after=5):
    try:
        lines = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None, None, None
    start = max(0, int(line_no)-1-before)
    end = min(len(lines), int(line_no)-1+after+1)
    ctx = lines[start:end]
    numbered = "\n".join(f"{i+1:>5}: {l}" for i, l in enumerate(ctx, start=start))
    return ctx, numbered, start

def suggest_fix(rule, before_lines):
    """
    Return (after_text, note) for known rules, else (None, advisory).
    Heuristics only — we don't rewrite the real file.
    """
    text = "\n".join(before_lines) if before_lines else ""

    from textwrap import dedent

    # -------------------- JAVASCRIPT / NODE / EXPRESS --------------------

    if rule == "GLNET001":
        after = dedent("""\
// After (batch with Promise.all; or limit concurrency)
await Promise.all(urls.map(u => fetch(u)));

// Or with controlled concurrency (no deps)
const concurrency = 8;
let i = 0;
const workers = Array.from({length: concurrency}, async () => {
  while (i < urls.length) {
    const u = urls[i++];
    await fetch(u);
  }
});
await Promise.all(workers);
""")
        note = "Avoid sequential network calls inside loops; batch or apply a small concurrency limit."
        return after, note

    if rule == "GLWEB001":
        after = dedent("""\
// After (enable compression for Express)
const compression = require('compression');
app.use(compression()); // Consider gzip/Brotli at CDN/proxy, too
""")
        note = "Enable gzip/Brotli so large responses transfer fewer bytes."
        return after, note

    if rule == "GLWEB002":
        after = dedent("""\
// After (cache headers for static assets)
app.use(express.static('public', {
  maxAge: '1d',
  etag: true
}));
""")
        note = "Add Cache-Control/ETag to static files to reduce repeat downloads."
        return after, note

    if rule == "GLWEB004":
        after = dedent("""\
// After (long-term caching for versioned assets)
app.use(express.static(app.get('appPath'), {
  maxAge: '7d',     // tune for your release cadence
  etag: true,
  immutable: true
}));
""")
        note = "Use maxAge/immutable for hashed assets to maximize cache hits."
        return after, note

    if rule == "GLTPL001":
        after = dedent("""\
// After (disable template watch/cache-bypass in production)
const isProd = process.env.NODE_ENV === 'production';
nunjucks(app, {
  autoescape: true,
  watch: !isProd,
  noCache: !isProd,
  filters,
  loader: njk.FileSystemLoader,
});
""")
        note = "Disable template watching and cache bypass in production to avoid extra filesystem work."
        return after, note

    if rule == "GLREQ001":
        after = dedent("""\
// After (limit JSON body size)
app.use(bodyParser.json({ limit: '1mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '1mb' }));
""")
        note = "Set sane payload limits to reduce CPU/memory spikes from large requests."
        return after, note

    if rule == "GLSESS001":
        after = dedent("""\
// After (use a proper session store)
const session = require('express-session');
const { createClient } = require('redis');
const RedisStore = require('connect-redis').default;
const redisClient = createClient({ url: process.env.REDIS_URL });
await redisClient.connect();
app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { sameSite: 'lax', secure: process.env.NODE_ENV === 'production' }
}));
""")
        note = "Avoid MemoryStore in production; use Redis (or another external store)."
        return after, note

    if rule == "GLLOG001":
        after = dedent("""\
// After (leveled logging instead of console.log)
const pino = require('pino');
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });
// logger.debug('details', { id })
logger.info('message');
""")
        note = "Use a leveled logger and set LOG_LEVEL in prod to avoid noisy IO."
        return after, note

    if rule == "GLCOOKIE001":
        after = dedent("""\
// After (guard JSON.parse on cookies)
let objCookie = null;
try {
  objCookie = JSON.parse(cookie);
} catch (e) {
  objCookie = null;
}
""")
        note = "Guard against malformed cookies to avoid exception-heavy code paths."
        return after, note

    if rule == "GLFS001":
        after = dedent("""\
// After (async fs in request path)
const fsp = require('fs/promises');
app.get('/route', async (req, res, next) => {
  try {
    const data = await fsp.readFile('file.txt', 'utf8');
    res.send(data);
  } catch (e) { next(e); }
});
""")
        note = "Replace sync fs calls in routes with fs/promises to avoid blocking the event loop."
        return after, note

    if rule == "GLNET002":
        after = dedent("""\
// After (wrap map(async ...) with Promise.all or p-limit)
const results = await Promise.all(items.map(async (x) => {
  return doAsync(x);
}));
""")
        note = "Ensure you await Promise.all when using map(async …) to avoid unbounded/dangling concurrency."
        return after, note

    if rule == "GLHTTP002":
        after = dedent("""\
// After (HTTP keep-alive agents)
const http = require('http');
const https = require('https');
const axios = require('axios');

const httpAgent = new http.Agent({ keepAlive: true });
const httpsAgent = new https.Agent({ keepAlive: true });

const client = axios.create({ httpAgent, httpsAgent });
const { data } = await client.get('https://example.com');
""")
        note = "Enable keep-alive so connections are reused and TCP/TLS handshakes are reduced."
        return after, note

    if rule == "GLHTTP003":
        after = dedent("""\
// After (timeouts / AbortController)
const controller = new AbortController();
const id = setTimeout(() => controller.abort(), 10000); // 10s

const res = await fetch(url, { signal: controller.signal });
clearTimeout(id);

// Axios example:
// const client = axios.create({ timeout: 10000 });
""")
        note = "Set request timeouts (or AbortController) to prevent hung sockets from wasting resources."
        return after, note

    if rule == "GLAPI001":
        after = dedent("""\
// After (explicit Cache-Control on cacheable GET)
app.get('/v1/data', (req, res) => {
  res.set('Cache-Control', 'public, max-age=60'); // tune policy
  res.json({ ok: true });
});
""")
        note = "For cacheable endpoints, set Cache-Control to reduce repeat processing."
        return after, note

    if rule == "GLCPU001":
        after = dedent("""\
// After (avoid JSON stringify/parse inside hot loops)
const payload = JSON.stringify(obj);   // do once outside
for (const item of items) {
  // use 'payload' instead of re-stringifying each iteration
}
""")
        note = "Hoist expensive (de)serialization outside the loop."
        return after, note

    if rule == "GLTIMER001":
        after = dedent("""\
// After (less aggressive timer)
const intervalMs = 250; // was < 50ms
const id = setInterval(doWork, intervalMs);
// Or debounce the work on demand
""")
        note = "Avoid sub-50ms intervals; use a slower cadence or debounce."
        return after, note

    if rule == "GLWEB003":
        after = dedent("""\
// After (tree-shakeable per-method imports)
// Before: import _ from 'lodash'
import debounce from 'lodash/debounce';
import isEqual from 'lodash/isEqual';
""")
        note = "Import only the methods you use (lodash/date-fns/ramda) to shrink bundles."
        return after, note

    if rule == "GLIMG001":
        after = dedent("""\
<!-- After (lazy-loading images) -->
<img src="/images/photo.jpg" loading="lazy" alt="..." width="800" height="600">
""")
        note = "Lazy-load offscreen images to avoid unnecessary network/CPU."
        return after, note

    if rule == "GLIMG002":
        after = dedent("""\
<!-- After (reserve image space to reduce layout shifts) -->
<img src="/images/photo.jpg" width="800" height="600" alt="...">
""")
        note = "Specify width/height so the browser can allocate space without reflows."
        return after, note

    if rule == "GLEV T001" or rule == "GLEVT001":  # tolerate spacing variant
        after = dedent("""\
// After (debounce/throttle high-frequency events)
const onScroll = throttle(() => {
  // work
}, 100); // or debounce(..., 100)

window.addEventListener('scroll', onScroll);
""")
        note = "Throttle/debounce scroll/resize/mousemove handlers to avoid excessive reflows."
        return after, note

    # ---------------------------- DOCKER / CT ----------------------------

    if rule == "CT001":
        after = dedent("""\
# After (prefer minimal base)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
""")
        note = "Use alpine/distroless to shrink images and reduce transfer/storage."
        return after, note

    if rule == "CT002":
        after = dedent("""\
# After (drop root)
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app ./
RUN addgroup -S app && adduser -S app -G app
USER app
CMD ["node", "server.js"]
""")
        note = "Run as non-root for least privilege."
        return after, note

    if rule == "CT003":
        after = dedent("""\
# After (reproducible installs)
COPY package*.json ./
RUN npm ci --only=production
""")
        note = "Prefer `npm ci` for deterministic, cache-friendly installs."
        return after, note

    if rule == "CT004":
        after = dedent("""\
# After (copy only what you need; maintain .dockerignore)
COPY package*.json ./
RUN npm ci --only=production
COPY src ./src
COPY public ./public
""")
        note = "Reduce context size; avoid COPY . unless necessary."
        return after, note

    if rule == "CT006":
        after = dedent("""\
# After (avoid recommended deps)
RUN apt-get update && apt-get install --no-install-recommends -y curl ca-certificates && rm -rf /var/lib/apt/lists/*
""")
        note = "Use --no-install-recommends to keep the image lean."
        return after, note

    if rule == "CT005":
        after = dedent("""\
# After (multi-stage build)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY package*.json ./
RUN npm ci --omit=dev
USER node
CMD ["node","dist/server.js"]
""")
        note = "Multi-stage builds ship only runtime artifacts and shrink images."
        return after, note

    if rule == "CT009":
        after = dedent("""\
# After (declare non-root USER in final stage)
RUN addgroup -S app && adduser -S app -G app
USER app
""")
        note = "Containers run as root by default; add an explicit non-root user."
        return after, note

    if rule == "CT000":
        return None, "The Dockerfile couldn’t be parsed; open it to fix syntax and re-run the scan."

    # ----------------------------- Fallback ------------------------------
    return None, "No auto-fix heuristic for this rule yet. Check project guidance or open a PR to add one here."


# UI: pick a row from the filtered table above
# Ensure 'filtered' is always defined
filtered = pd.DataFrame()
if uploads and not df.empty:
    # Recompute filtered mask as above
    rule_sel = st.session_state.get("rule_sel", [])
    sev_sel = st.session_state.get("sev_sel", [])
    file_sel = st.session_state.get("file_sel", "")
    mask = pd.Series([True]*len(df))
    if rule_sel: mask &= df["rule"].isin(rule_sel)
    if sev_sel: mask &= df["severity"].isin(sev_sel)
    if file_sel: mask &= df["file"].str.contains(file_sel, case=False, na=False)
    filtered = df[mask].sort_values(["report","file","line"]).reset_index(drop=True)

    st.markdown("Select a finding row (index from the filtered table) to preview:")
    idx2 = st.number_input("Row index", min_value=0, max_value=max(0, len(filtered)-1), value=0, step=1)
    if len(filtered) > 0:
        row = filtered.iloc[int(idx2)]
        st.write(f"**Rule:** {row['rule']} — {row['message']}")
        st.write(f"**File:** `{row['file']}`  |  **Line:** `{row['line']}`")

        ctx, numbered, start = read_context(row["file"], row["line"])
        if numbered:
            st.code(numbered, language="python")  # good enough for .py or .java display

            after, note = suggest_fix(row["rule"], ctx)
            st.markdown("**Suggested After:**")
            if after:
                # Guess display language from file extension / name
                f = str(row["file"]).lower()
                if f.endswith(".java"):
                    lang = "java"
                elif f.endswith((".js", ".mjs", ".cjs")):
                    lang = "javascript"
                elif f.endswith(("dockerfile",)) or f.endswith("/dockerfile") or f.endswith("\\dockerfile"):
                    lang = "dockerfile"
                else:
                    lang = "python"
                st.code(after, language=lang)
            st.caption(note)
        else:
            st.info("Could not read local source file. Run the dashboard from the repo root (so relative paths resolve), or copy/paste code here.")
    else:
        st.info("No findings available to preview.")
