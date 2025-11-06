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

    # PY003: logging f-string -> lazy logging
    if rule == "PY003":
        # Replace common patterns: logging.debug(f"...{x}") or "...".format(x)
        lazy = re.sub(
            r'logging\.(debug|info)\(\s*f?(".*?\{.*?\}".*?)\)',
            r'logging.\1("...", ...)',  # placeholder
            text
        )
        example_after = dedent('''\
            # After (lazy logging)
            logging.debug("Processing record %s", record_id)
            # or
            logging.info("User %s logged in", user.name)
        ''')
        note = "Use parameterised logging so string formatting only happens when the log level is enabled."
        return example_after, note

    # PY001: membership in loop -> use set
    if rule == "PY001":
        example_after = dedent('''\
            # After (O(1) membership)
            s = set(items)
            for i in items:
                if i in s:
                    process(i)
        ''')
        note = "Convert to a set once outside the loop for O(1) membership checks."
        return example_after, note

    # PY002: network in loop -> batch/parallelise
    if rule == "PY002":
        example_after = dedent('''\
            # After (parallel requests)
            from concurrent.futures import ThreadPoolExecutor
            import requests
            with ThreadPoolExecutor(max_workers=8) as ex:
                responses = list(ex.map(requests.get, urls))
        ''')
        note = "Batch or parallelise network calls to reduce wall-time and wasted idle CPU."
        return example_after, note

    # IO001: file I/O in loop -> chunking/buffering
    if rule == "IO001":
        example_after = dedent('''\
            # After (chunked reading)
            import pandas as pd
            for chunk in pd.read_csv("large.csv", chunksize=100_000):
                handle(chunk)
        ''')
        note = "Avoid per-iteration full reads; use chunking or preload once."
        return example_after, note

    # PD001: pandas row-wise ops -> vectorise
    if rule == "PD001":
        example_after = dedent('''\
            # After (vectorised)
            # Before: df.apply(lambda r: r["a"] + r["b"], axis=1)
            df["sum"] = df["a"] + df["b"]
        ''')
        note = "Replace row-wise apply/iterrows with vectorised column operations."
        return example_after, note

    # AI002: training from scratch -> use pre-trained
    if rule == "AI002":
        example_after = dedent('''\
            # After (transfer learning)
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)
            # fine-tune instead of training from scratch
        ''')
        note = "Prefer fine-tuning pre-trained models to reduce compute and energy."
        return example_after, note
 # ---------- JAVASCRIPT / NODE ----------
    if rule == "GLNET001":
        example_after = dedent('''\
// After (batch with Promise.all; or limit concurrency with p-limit)
await Promise.all(urls.map(u => fetch(u)));

// Or with controlled concurrency (no extra deps)
const concurrency = 8;
let i = 0;
const workers = Array.from({length: concurrency}, async () => {
  while (i < urls.length) {
    const u = urls[i++];
    await fetch(u);
  }
});
await Promise.all(workers);
        ''')
        note = "Avoid sequential network calls inside loops; batch or limit concurrency to cut wall-time/CPU."
        return example_after, note

    if rule == "GLWEB001":
        example_after = dedent('''\
// After (enable compression for Express)
const compression = require('compression');
app.use(compression());  // consider Brotli in reverse proxy/CDN too
        ''')
        note = "Enable gzip/Brotli so large responses transfer fewer bytes and save energy."
        return example_after, note

    if rule == "GLWEB002":
        example_after = dedent('''\
// After (cache headers for static assets)
app.use(express.static('public', {
  maxAge: '1d',      // tune for your content
  etag: true
}));
        ''')
        note = "Set Cache-Control/ETag on static files to reduce repeat transfers."
        return example_after, note

    # ---------- CONTAINER / DOCKER ----------
    if rule == "CT001":
        example_after = dedent('''\
# After (use minimal base)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
        ''')
        note = "Use alpine/distroless to shrink images and reduce network/storage costs."
        return example_after, note

    if rule == "CT002":
        example_after = dedent('''\
# After (drop root)
# ... build stage ...
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app ./
RUN addgroup -S app && adduser -S app -G app
USER app
CMD ["node", "server.js"]
        ''')
        note = "Run as non-root for security and best practice."
        return example_after, note

    if rule == "CT003":
        example_after = dedent('''\
# After (reproducible, faster installs)
COPY package*.json ./
RUN npm ci --only=production
        ''')
        note = "Use `npm ci` for deterministic, cache-friendly builds."
        return example_after, note

    if rule == "CT004":
        example_after = dedent('''\
# After (do not COPY . blindly)
# Ensure .dockerignore excludes node_modules, tests, docs, etc.
COPY package*.json ./
RUN npm ci --only=production
COPY src ./src
COPY public ./public
        ''')
        note = "Reduce context size; copy only what you need, and maintain a .dockerignore."
        return example_after, note

    if rule == "CT005":
        example_after = dedent('''\
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
        ''')
        note = "Use multi-stage builds to ship only runtime artifacts and shrink images."
        return example_after, note

    # ---------- AI helpers you added ----------
    if rule == "AI002":
        example_after = dedent('''\
# After (transfer learning)
from transformers import AutoModelForSequenceClassification
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)
        ''')
        note = "Prefer fine-tuning pre-trained models over training from scratch."
        return example_after, note

    # Fallback
    return None, "No auto-fix heuristic available for this rule; see project guidance."

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
