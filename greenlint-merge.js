/**
 * greenlint-merge.js
 * Merge JS + Docker results into greenlint_report.json (dashboard-compatible).
 */
const fs = require('fs');
function safeRead(p){ try { return JSON.parse(fs.readFileSync(p,'utf8')); } catch { return {summary:{total_findings:0},findings:[]}; } }
const js = safeRead('greenlint_js.json');
const dk = safeRead('greenlint_docker.json');
const findings = [...(js.findings||[]), ...(dk.findings||[])];
const out = {
  summary: {
    total_findings: findings.length,
    by_rule: findings.reduce((m,f)=>{ m[f.rule]=(m[f.rule]||0)+1; return m; }, {})
  },
  findings
};
fs.writeFileSync('greenlint_report.json', JSON.stringify(out,null,2),'utf8');
console.log('Merged findings:', out.summary.total_findings, 'By rule:', out.summary.by_rule);
