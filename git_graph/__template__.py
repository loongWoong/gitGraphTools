"""HTML template for the git repository intelligence dashboard.

5-tab layout: Overview | Graph | Timeline | Authors | AI Insights
GitHub Dark color scheme, Inter + JetBrains Mono fonts.
The ``{{GRAPH_DATA}}`` placeholder is replaced at build time.
"""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Repository Intelligence Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ── GitHub Dark Theme ─────────────────────────────────────────── */
:root {
  --bg-primary:    #0d1117;
  --bg-secondary:  #161b22;
  --bg-tertiary:   #21262d;
  --border:        #30363d;
  --text-primary:  #c9d1d9;
  --text-secondary:#8b949e;
  --text-link:     #58a6ff;

  /* Status colors (colorblind-safe) */
  --healthy:       #238636;
  --aging:         #d29922;
  --zombie-merged: #8957e5;
  --zombie-abandoned: #f85149;
  --merged-stale:  #6e7681;

  /* Graph */
  --edge-default:  #30363d;
  --edge-active:   #58a6ff;
  --commit-dot:    #c9d1d9;
  --commit-merge:  #d29922;
  --commit-head:   #58a6ff;

  --font-body: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
  --radius: 6px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 13px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Light Theme ──────────────────────────────────────────────── */
[data-theme="light"] {
  --bg-primary:    #ffffff;
  --bg-secondary:  #f6f8fa;
  --bg-tertiary:   #eaeef2;
  --border:        #d0d7de;
  --text-primary:  #1f2328;
  --text-secondary:#656d76;
  --text-link:     #0969da;
  --edge-default:  #d0d7de;
  --commit-dot:    #1f2328;
  --commit-head:   #0969da;
}
[data-theme="light"] .heatmap-cell { background: #eaeef2; }
[data-theme="light"] .metric-card,
[data-theme="light"] .section-card,
[data-theme="light"] .health-gauge { border-color: var(--border); }
[data-theme="light"] .branch-row { border-color: var(--border); }
[data-theme="light"] #detail-panel .field-value.message { background: var(--bg-secondary); }
[data-theme="light"] #tooltip { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
[data-theme="light"] #graph-legend { border-color: var(--border); }
[data-theme="light"] #graph-container { background: var(--bg-primary); }

/* ── Tab Navigation ────────────────────────────────────────────── */
#tab-nav {
  display: flex;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  padding: 0 16px;
}
.tab-btn {
  padding: 10px 18px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  white-space: nowrap;
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { color: var(--text-link); border-bottom-color: var(--text-link); }

/* ── Tab Content ───────────────────────────────────────────────── */
.tab-content { display: none; flex: 1; overflow: auto; }
.tab-content.active { display: flex; flex-direction: column; }

/* ── Overview Tab ──────────────────────────────────────────────── */
#overview-tab { padding: 24px; gap: 20px; }

.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.metric-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
}
.metric-card .value {
  font-size: 32px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}
.metric-card .label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.overview-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.health-gauge {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.health-ring {
  position: relative;
  width: 100px; height: 100px;
  flex-shrink: 0;
}
.health-ring svg { transform: rotate(-90deg); }
.health-ring .bg-ring { fill: none; stroke: var(--bg-tertiary); stroke-width: 8; }
.health-ring .fg-ring { fill: none; stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset 0.8s ease; }
.health-ring .score-text {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 700; font-family: var(--font-mono);
}

.section-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.section-card h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.quick-actions .action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
}
.quick-actions .action-item:last-child { border-bottom: none; }
.quick-actions .action-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.action-dot.healthy { background: var(--healthy); }
.action-dot.aging { background: var(--aging); }
.action-dot.zombie_merged { background: var(--zombie-merged); }
.action-dot.zombie_abandoned { background: var(--zombie-abandoned); }
.action-dot.merged_stale { background: var(--merged-stale); }

.branch-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
}
.branch-row:last-child { border-bottom: none; }
.branch-row .name { flex: 1; font-family: var(--font-mono); font-size: 11px; }
.branch-row .dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.dot.healthy { background: var(--healthy); }
.dot.aging { background: var(--aging); }
.dot.zombie_merged { background: var(--zombie-merged); }
.dot.zombie_abandoned { background: var(--zombie-abandoned); }
.dot.merged_stale { background: var(--merged-stale); }

/* ── Graph Tab ─────────────────────────────────────────────────── */
#graph-tab { flex-direction: row; }

#graph-legend {
  width: 200px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  flex-shrink: 0;
  padding: 8px 0;
}
#graph-legend .legend-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  padding: 8px 14px 4px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 14px;
  cursor: pointer;
  font-size: 11px;
  font-family: var(--font-mono);
  transition: background 0.1s;
  user-select: none;
}
.legend-item:hover { background: var(--bg-tertiary); }
.legend-item.selected { background: rgba(88,166,255,0.1); }
.legend-item .dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.legend-item .name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 10px; }
.legend-item .zombie-tag { font-size: 9px; color: var(--zombie-merged); margin-left: auto; }

#graph-container {
  flex: 1;
  overflow: auto;
  position: relative;
  cursor: grab;
  background: var(--bg-primary);
}
#graph-container:active { cursor: grabbing; }
#graph-svg { display: block; }

/* Graph elements */
.commit-circle { cursor: pointer; transition: r 0.15s, opacity 0.2s; }
.commit-circle:hover { r: 8; }
.commit-normal { fill: var(--commit-dot); stroke: var(--commit-dot); stroke-width: 1.5; }
.commit-merge  { fill: var(--bg-primary); stroke: var(--commit-merge); stroke-width: 2; }
.commit-head   { fill: var(--commit-head); stroke: var(--commit-head); stroke-width: 2.5; }
.edge-line { fill: none; stroke: var(--edge-default); stroke-width: 1.5; stroke-linecap: round; transition: opacity 0.2s; }
.edge-merge { stroke: var(--commit-merge); }
.edge-fork  { stroke: var(--text-secondary); }
.dimmed { opacity: 0.08; transition: opacity 0.25s; }

.branch-label-pill {
  font-family: var(--font-mono);
  font-size: 9px;
  cursor: pointer;
  transition: opacity 0.2s;
  user-select: none;
}
.branch-label-pill:hover { opacity: 1 !important; }

.date-marker {
  font-family: var(--font-mono);
  font-size: 9px;
  fill: var(--text-secondary);
}

/* Minimap */
#minimap {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 180px;
  height: 120px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  opacity: 0.7;
  transition: opacity 0.2s;
  pointer-events: none;
  z-index: 10;
}
#minimap:hover { opacity: 1; }
#minimap .viewport-rect {
  fill: rgba(88,166,255,0.15);
  stroke: var(--text-link);
  stroke-width: 1;
  stroke-dasharray: 3 2;
}

/* Detail panel */
#detail-panel {
  width: 360px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border);
  overflow-y: auto;
  flex-shrink: 0;
  display: none;
}
#detail-panel.visible { display: flex; flex-direction: column; }
#detail-panel .panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-bottom: 1px solid var(--border);
  position: sticky; top: 0; background: var(--bg-secondary); z-index: 5;
}
#detail-panel .panel-header h3 { font-size: 13px; color: var(--text-link); font-weight: 600; }
#detail-panel .panel-close { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 18px; }
#detail-panel .panel-close:hover { color: var(--text-primary); }
#detail-panel .panel-body { padding: 14px; }
#detail-panel .field { margin-bottom: 10px; }
#detail-panel .field-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-secondary); margin-bottom: 2px; }
#detail-panel .field-value { font-size: 12px; word-break: break-all; line-height: 1.5; }
#detail-panel .field-value.hash { font-family: var(--font-mono); color: var(--text-secondary); font-size: 11px; }
#detail-panel .field-value.message { white-space: pre-wrap; background: var(--bg-primary); padding: 10px; border-radius: var(--radius); max-height: 300px; overflow-y: auto; }
#detail-panel .parent-link { color: var(--text-link); cursor: pointer; text-decoration: none; }
#detail-panel .parent-link:hover { text-decoration: underline; }

.badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; margin: 1px 2px; }
.badge-local  { background: rgba(35,134,54,0.15); color: var(--healthy); }
.badge-remote { background: rgba(88,166,255,0.15); color: var(--text-link); }
.badge-head   { background: rgba(88,166,255,0.18); color: var(--text-link); }
.badge-zombie { background: rgba(137,87,229,0.15); color: var(--zombie-merged); }

/* Health status badge variants */
.badge-healthy          { background: rgba(35,134,54,0.12); color: var(--healthy); }
.badge-aging            { background: rgba(210,153,34,0.12); color: var(--aging); }
.badge-zombie_merged    { background: rgba(137,87,229,0.12); color: var(--zombie-merged); }
.badge-zombie_abandoned { background: rgba(248,81,73,0.12); color: var(--zombie-abandoned); }
.badge-merged_stale     { background: rgba(110,118,129,0.12); color: var(--merged-stale); }

/* Tooltip branch tags */
#tooltip .tt-branches {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 6px;
}
#tooltip .tt-branch-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--font-mono);
}
.tt-branch-tag.healthy          { background: rgba(35,134,54,0.1); color: var(--healthy); }
.tt-branch-tag.aging            { background: rgba(210,153,34,0.1); color: var(--aging); }
.tt-branch-tag.zombie_merged    { background: rgba(137,87,229,0.1); color: var(--zombie-merged); }
.tt-branch-tag.zombie_abandoned { background: rgba(248,81,73,0.1); color: var(--zombie-abandoned); }
.tt-branch-tag.merged_stale     { background: rgba(110,118,129,0.1); color: var(--merged-stale); }
.tt-branch-tag .dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
}
.tt-branch-tag.healthy          .dot { background: var(--healthy); }
.tt-branch-tag.aging            .dot { background: var(--aging); }
.tt-branch-tag.zombie_merged    .dot { background: var(--zombie-merged); }
.tt-branch-tag.zombie_abandoned .dot { background: var(--zombie-abandoned); }
.tt-branch-tag.merged_stale     .dot { background: var(--merged-stale); }

/* ── Timeline Tab ──────────────────────────────────────────────── */
#timeline-tab { padding: 24px; gap: 24px; }

.heatmap-grid {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
}
.heatmap-cell {
  width: 12px; height: 12px;
  border-radius: 2px;
  background: var(--bg-tertiary);
  transition: background 0.1s;
}
.heatmap-cell:hover { outline: 1px solid var(--text-primary); }
.heatmap-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.lifetime-bars { margin-top: 8px; }
.lifetime-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
  font-size: 11px;
}
.lifetime-row .lname {
  width: 160px;
  font-family: var(--font-mono);
  font-size: 10px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
  cursor: pointer;
}
.lifetime-row .lname:hover { color: var(--text-link); }
.lifetime-row .lbar-wrap {
  flex: 1;
  height: 14px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}
.lifetime-row .lbar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.lifetime-row .lbar.healthy { background: var(--healthy); }
.lifetime-row .lbar.aging { background: var(--aging); }
.lifetime-row .lbar.zombie_merged { background: var(--zombie-merged); opacity: 0.6; }
.lifetime-row .lbar.zombie_abandoned { background: var(--zombie-abandoned); }
.lifetime-row .lbar.merged_stale { background: var(--merged-stale); opacity: 0.5; }
.lifetime-row .ldur { width: 50px; font-size: 10px; color: var(--text-secondary); flex-shrink: 0; }

/* ── Authors Tab ───────────────────────────────────────────────── */
#authors-tab { padding: 24px; gap: 24px; }

.author-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
  font-size: 12px;
}
.author-bar-row .aname { width: 140px; font-weight: 500; text-align: right; flex-shrink: 0; }
.author-bar-row .abar-wrap { flex: 1; height: 20px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden; }
.author-bar-row .abar { height: 100%; background: var(--text-link); border-radius: 4px; transition: width 0.5s ease; }
.author-bar-row .acount { width: 100px; font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); flex-shrink: 0; }

.bf-warning {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
}
.bf-warning:last-child { border-bottom: none; }
.bf-warning .bf-icon { color: var(--aging); font-weight: bold; flex-shrink: 0; }
.bf-warning .bf-file { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); word-break: break-all; }
.bf-warning .bf-detail { color: var(--text-secondary); font-size: 11px; }

/* ── AI Tab ────────────────────────────────────────────────────── */
#ai-tab { padding: 24px; align-items: center; justify-content: center; }
#ai-tab .placeholder {
  text-align: center;
  color: var(--text-secondary);
}
#ai-tab .placeholder h2 { font-size: 18px; color: var(--text-primary); margin-bottom: 8px; }
#ai-tab .placeholder p { font-size: 13px; }

/* ── Search / Controls ─────────────────────────────────────────── */
#graph-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-secondary);
}
#graph-controls input {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 4px 10px;
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 11px;
  width: 200px;
  outline: none;
}
#graph-controls input:focus { border-color: var(--text-link); }
#graph-controls button {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 4px 10px;
  border-radius: var(--radius);
  cursor: pointer;
  font-family: var(--font-body);
  font-size: 11px;
}
#graph-controls button:hover { background: var(--border); }
#graph-controls .match-count { color: var(--text-link); font-weight: 500; }

/* ── Scrollbar ─────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-tertiary); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border); }

/* ── Tooltip ───────────────────────────────────────────────────── */
#tooltip {
  position: fixed;
  pointer-events: none;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: 12px;
  max-width: 400px;
  z-index: 100;
  opacity: 0;
  transition: opacity 0.1s;
}
#tooltip.visible { opacity: 1; }
#tooltip .tt-hash { color: var(--text-secondary); font-size: 10px; font-family: var(--font-mono); }
#tooltip .tt-subject { color: var(--text-primary); margin-top: 2px; }
#tooltip .tt-meta { color: var(--text-secondary); font-size: 10px; margin-top: 4px; }
/* ── Diff Viewer ───────────────────────────────────────────────── */
.diff-viewer {
  margin-top: 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.diff-file-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border);
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-secondary);
}
.diff-content {
  max-height: 400px;
  overflow: auto;
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.5;
}
.diff-line {
  padding: 0 12px;
  white-space: pre;
  display: flex;
}
.diff-add { background: rgba(35,134,54,0.15); color: var(--healthy); }
.diff-del { background: rgba(248,81,73,0.15); color: var(--zombie-abandoned); }
.diff-hunk { background: rgba(88,166,255,0.06); color: var(--text-link); font-size: 10px; }
.diff-header-line { color: var(--text-secondary); font-size: 10px; }
.diff-collapsed { color: var(--text-secondary); text-align: center; font-style: italic; padding: 4px; }

[data-theme="light"] .diff-add { background: #d2fed1; }
[data-theme="light"] .diff-del { background: #ffd7d5; }

/* Changed files list */
.changed-files { margin-top: 10px; }
.changed-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  cursor: pointer;
  border-radius: 3px;
  font-size: 11px;
  font-family: var(--font-mono);
}
.changed-file:hover { background: var(--bg-tertiary); }
.changed-file .cf-status {
  width: 16px; text-align: center;
  font-size: 10px; font-weight: 600; flex-shrink: 0;
}
.cf-status.A { color: var(--healthy); }
.cf-status.M { color: var(--aging); }
.cf-status.D { color: var(--zombie-abandoned); }
.changed-file .cf-path { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.changed-file .cf-stats { font-size: 10px; color: var(--text-secondary); flex-shrink: 0; }

/* Server mode hint */
.server-hint {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius);
  font-size: 11px;
  color: var(--text-secondary);
}
</style>
</head>
<body>

<!-- ── Tab Navigation ──────────────────────────────────────────── -->
<div id="tab-nav">
  <button class="tab-btn active" data-tab="overview">Overview</button>
  <button class="tab-btn" data-tab="graph">Graph</button>
  <button class="tab-btn" data-tab="timeline">Timeline</button>
  <button class="tab-btn" data-tab="authors">Authors</button>
  <button class="tab-btn" data-tab="ai">AI Insights</button>
  <span style="flex:1"></span>
  <button id="theme-toggle" title="Toggle light/dark theme" style="background:none;border:1px solid var(--border);color:var(--text-secondary);cursor:pointer;padding:4px 10px;border-radius:var(--radius);font-size:14px;">&#x263C;</button>
</div>

<!-- ── Overview Tab ────────────────────────────────────────────── -->
<div class="tab-content active" id="overview-tab">
  <div class="metric-cards" id="metric-cards"></div>
  <div class="overview-row">
    <div class="health-gauge" id="health-gauge"></div>
    <div class="section-card quick-actions" id="quick-actions"></div>
  </div>
  <div class="overview-row">
    <div class="section-card" id="top-branches"></div>
    <div class="section-card" id="needs-attention"></div>
  </div>
</div>

<!-- ── Graph Tab ───────────────────────────────────────────────── -->
<div class="tab-content" id="graph-tab">
  <div id="graph-legend">
    <div class="legend-title">Branches</div>
    <div id="legend-list"></div>
  </div>
  <div style="display:flex;flex-direction:column;flex:1;">
    <div id="graph-controls">
      <input type="text" id="graph-search" placeholder="Search commits..." />
      <span class="match-count" id="match-count"></span>
      <span style="flex:1"></span>
      <button id="btn-fit">Fit</button>
      <button id="btn-reset">Reset</button>
      <span style="color:var(--text-secondary)">| +/- zoom  |  drag pan  |  Esc clear</span>
    </div>
    <div id="graph-container">
      <svg id="graph-svg"></svg>
      <div id="minimap"><svg id="minimap-svg"></svg></div>
    </div>
  </div>
  <div id="detail-panel">
    <div class="panel-header">
      <h3>Commit Detail</h3>
      <button class="panel-close" id="panel-close">&times;</button>
    </div>
    <div class="panel-body" id="panel-body"></div>
  </div>
</div>

<!-- ── Timeline Tab ────────────────────────────────────────────── -->
<div class="tab-content" id="timeline-tab">
  <div class="section-card" style="flex:1;display:flex;flex-direction:column;min-height:0">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
      <h3>Branch Fork &amp; Merge Timeline</h3>
      <label style="font-size:11px;color:var(--text-secondary);cursor:pointer">
        <input type="checkbox" id="tl-merged-toggle" checked onchange="renderTimeline()"> Show merged
      </label>
    </div>
    <div id="timeline-graph-container" style="flex:1;overflow:auto;position:relative;min-height:0;background:var(--bg-primary);border:1px solid var(--border);border-radius:var(--radius)"></div>
  </div>
  <div class="section-card">
    <h3>Commit Activity Heatmap</h3>
    <div class="heatmap-grid" id="heatmap-grid"></div>
    <div class="heatmap-labels" id="heatmap-labels"></div>
  </div>
</div>

<!-- ── Authors Tab ─────────────────────────────────────────────── -->
<div class="tab-content" id="authors-tab">
  <div class="section-card">
    <h3>Author Contributions</h3>
    <div id="author-bars"></div>
  </div>
  <div class="section-card">
    <h3>Bus Factor Warnings</h3>
    <div id="bus-factor-list"></div>
  </div>
</div>

<!-- ── AI Insights Tab ─────────────────────────────────────────── -->
<div class="tab-content" id="ai-tab">
  <div class="placeholder">
    <h2>AI Insights</h2>
    <p>Select a branch on the Graph or Timeline tab to generate an AI-powered summary.<br>This feature will be available when an AI provider is configured.</p>
  </div>
</div>

<!-- Tooltip -->
<div id="tooltip"></div>

<script>
// ── Constants ───────────────────────────────────────────────────────
const DATA = {{GRAPH_DATA}};
const commitMap = {};
DATA.commits.forEach(c => { commitMap[c.h] = c; });

const LANE_W  = DATA.metadata.lane_width;
const MARGIN_L = DATA.metadata.margin_left;
const ROW_H   = DATA.metadata.row_height;
const MARGIN_T = DATA.metadata.margin_top;

// Server mode detection (injected by server.py)
const isServerMode = typeof window.__SERVER_MODE__ !== 'undefined' && window.__SERVER_MODE__;
const API_BASE = isServerMode ? `http://127.0.0.1:${window.__SERVER_PORT__||8765}` : '';

// Theme toggle
(function initTheme() {
  const saved = localStorage.getItem('git-graph-theme');
  if (saved === 'light') document.documentElement.dataset.theme = 'light';
})();

// ── Tab Switching ───────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab + '-tab').classList.add('active');
    if (btn.dataset.tab === 'graph') updateMinimap();
  });
});

// ── Helper ──────────────────────────────────────────────────────────
function escHtml(s) { if (!s) return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString(); } catch { return iso; } }
function fmtDateShort(iso) { if (!iso) return ''; try { const d=new Date(iso); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0'); } catch { return iso; } }
function statusDot(status) { return `<span class="dot ${status}"></span>`; }

// ═══════════════════════════════════════════════════════════════════
// TAB 1: Overview
// ═══════════════════════════════════════════════════════════════════
function renderOverview() {
  // Metric cards
  const cards = document.getElementById('metric-cards');
  const zCount = (DATA.status_counts.zombie_merged || 0) + (DATA.status_counts.zombie_abandoned || 0);
  cards.innerHTML = [
    { v: DATA.metadata.total_commits, l: 'Commits' },
    { v: DATA.metadata.total_branches, l: 'Branches' },
    { v: DATA.author_stats.length, l: 'Authors' },
    { v: zCount, l: 'Zombies' },
  ].map(c => `<div class="metric-card"><div class="value">${c.v}</div><div class="label">${c.l}</div></div>`).join('');

  // Health gauge
  const score = DATA.repo_health_score;
  const r = 36, circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  const color = score >= 70 ? 'var(--healthy)' : score >= 40 ? 'var(--aging)' : 'var(--zombie-abandoned)';
  document.getElementById('health-gauge').innerHTML = `
    <div class="health-ring">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle class="bg-ring" cx="50" cy="50" r="${r}"/>
        <circle class="fg-ring" cx="50" cy="50" r="${r}"
          stroke="${color}" stroke-dasharray="${circ}" stroke-dashoffset="${offset}"/>
      </svg>
      <div class="score-text">${score}<span style="font-size:14px;color:var(--text-secondary)">/100</span></div>
    </div>
    <div>
      <div style="font-weight:600;font-size:16px;">Repository Health</div>
      <div style="color:var(--text-secondary);font-size:12px;margin-top:4px;">
        ${Object.entries(DATA.status_counts).map(([k,v]) =>
          `${v} ${k.replace(/_/g,' ')}`).join(' &middot; ') || 'No data'}
      </div>
    </div>`;

  // Quick actions
  const qa = document.getElementById('quick-actions');
  let qaHtml = '<h3>Quick Actions</h3>';
  const zombies = DATA.health.filter(h => h.st === 'zombie_merged' || h.st === 'zombie_abandoned');
  const stale = DATA.health.filter(h => h.st === 'merged_stale');
  qaHtml += `<div class="action-item">${statusDot('zombie_merged')} ${zombies.length} zombie branches (safe to delete)</div>`;
  qaHtml += `<div class="action-item">${statusDot('merged_stale')} ${stale.length} merged-stale branches (can delete)</div>`;
  qaHtml += `<div class="action-item">${statusDot('zombie_abandoned')} ${DATA.health.filter(h=>h.st==='zombie_abandoned').length} abandoned branches (needs review)</div>`;
  qa.innerHTML = qaHtml;

  // Top branches (by score, healthy/aging only)
  const top = DATA.health.filter(h => h.st === 'healthy' || h.st === 'aging').slice(0, 8);
  document.getElementById('top-branches').innerHTML = `
    <h3>Top Branches</h3>
    ${top.map(h => `<div class="branch-row">
      ${statusDot(h.st)} <span class="name">${escHtml(h.n)}</span>
      <span style="color:var(--text-secondary);font-size:10px">${h.cc} commits &middot; ${h.ac} authors &middot; score ${h.sc}</span>
    </div>`).join('')}`;

  // Needs attention (zombies + stale)
  const attn = DATA.health.filter(h => ['zombie_merged','zombie_abandoned','merged_stale'].includes(h.st)).slice(0, 10);
  document.getElementById('needs-attention').innerHTML = `
    <h3>Needs Attention</h3>
    ${attn.map(h => `<div class="branch-row">
      ${statusDot(h.st)} <span class="name">${escHtml(h.n)}</span>
      <span style="color:var(--text-secondary);font-size:10px">
        ${h.st==='zombie_merged'?'Merged Zombie':h.st==='zombie_abandoned'?'Abandoned':'Merged Stale'}
        &middot; ${h.ds}d inactive
        ${h.wn&&h.wn.length? '&middot; '+h.wn.join(', ') : ''}
      </span>
    </div>`).join('')}`;
}

// ═══════════════════════════════════════════════════════════════════
// TAB 2: Graph (DAG)
// ═══════════════════════════════════════════════════════════════════
let highlightedBranch = null, panX = 0, panY = 0, scale = 1;
let isDragging = false, dragStartX = 0, dragStartY = 0, panStartX = 0, panStartY = 0;

function cx(lane) { return MARGIN_L + lane * LANE_W; }
function cy(row)  { return MARGIN_T + row * ROW_H; }

function renderGraph() {
  const svg = document.getElementById('graph-svg');
  const W = MARGIN_L + (DATA.metadata.total_lanes + 1) * LANE_W + 300;
  const H = MARGIN_T + (DATA.metadata.total_rows + 1) * ROW_H + 60;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);
  svg.innerHTML = '';

  const rootG = document.createElementNS('http://www.w3.org/2000/svg','g');
  rootG.setAttribute('id','root-g');
  svg.appendChild(rootG);

  // Date markers
  const dmG = document.createElementNS('http://www.w3.org/2000/svg','g');
  rootG.appendChild(dmG);
  (DATA.date_markers||[]).forEach(dm => {
    const text = document.createElementNS('http://www.w3.org/2000/svg','text');
    text.setAttribute('x', 6);
    text.setAttribute('y', cy(dm.r) + 4);
    text.setAttribute('class', 'date-marker');
    text.textContent = dm.label;
    dmG.appendChild(text);
    // Ticks
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1', MARGIN_L - 50);
    line.setAttribute('x2', MARGIN_L - 5);
    line.setAttribute('y1', cy(dm.r));
    line.setAttribute('y2', cy(dm.r));
    line.setAttribute('stroke', 'var(--border)');
    line.setAttribute('stroke-width', '0.5');
    dmG.appendChild(line);
  });

  // Edges
  const edgeG = document.createElementNS('http://www.w3.org/2000/svg','g');
  rootG.appendChild(edgeG);
  DATA.edges.forEach(e => {
    const path = document.createElementNS('http://www.w3.org/2000/svg','path');
    const x1 = cx(e.fl), y1 = cy(commitMap[e.f]?.r ?? 0);
    const x2 = cx(e.tl), y2 = cy(commitMap[e.to]?.r ?? 0);
    const yMid = (y1 + y2) / 2;
    const d = e.fl === e.tl
      ? `M ${x1} ${y1} L ${x2} ${y2}`
      : `M ${x1} ${y1} C ${x1} ${yMid} ${x2} ${yMid} ${x2} ${y2}`;
    path.setAttribute('d', d);
    path.setAttribute('data-from', e.f);
    path.setAttribute('data-to', e.to);
    path.classList.add('edge-line');
    if (e.k === 'merge') path.classList.add('edge-merge');
    if (e.k === 'fork')  path.classList.add('edge-fork');
    edgeG.appendChild(path);
  });

  // Commits
  const commitG = document.createElementNS('http://www.w3.org/2000/svg','g');
  rootG.appendChild(commitG);
  DATA.commits.forEach(c => {
    const circle = document.createElementNS('http://www.w3.org/2000/svg','circle');
    circle.setAttribute('cx', cx(c.l));
    circle.setAttribute('cy', cy(c.r));
    circle.setAttribute('r', 5);
    circle.setAttribute('data-hash', c.h);
    let cls = 'commit-circle ';
    if (c.hd) cls += 'commit-head';
    else if (c.ph && c.ph.length > 1) cls += 'commit-merge';
    else cls += 'commit-normal';
    circle.setAttribute('class', cls);
    circle.addEventListener('click', ev => { ev.stopPropagation(); showCommitDetail(c.h); });
    circle.addEventListener('mouseenter', ev => showTooltip(ev, c));
    circle.addEventListener('mouseleave', hideTooltip);
    circle.addEventListener('mousemove', ev => moveTooltip(ev, c));
    commitG.appendChild(circle);
  });

  // Branch labels
  const labelG = document.createElementNS('http://www.w3.org/2000/svg','g');
  rootG.appendChild(labelG);
  const labelOffsets = {};
  DATA.branches.forEach(b => {
    const commit = commitMap[b.h];
    if (!commit) return;
    const lane = b.l ?? commit.l;
    const lx = cx(lane) + 10;
    const off = labelOffsets[lane] || 0;
    const ly = cy(commit.r) + off * 14 - 3;
    // Background pill
    const rect = document.createElementNS('http://www.w3.org/2000/svg','rect');
    const textEl = document.createElementNS('http://www.w3.org/2000/svg','text');
    textEl.textContent = b.n;
    textEl.setAttribute('x', lx + 4);
    textEl.setAttribute('y', ly + 8);
    textEl.setAttribute('data-branch', b.n);
    textEl.setAttribute('class', 'branch-label-pill');
    const hStat = (DATA.health||[]).find(h => h.n === b.n);
    const st = hStat ? hStat.st : 'healthy';
    textEl.setAttribute('fill',
      st==='healthy'?'var(--healthy)':st==='aging'?'var(--aging)':
      st==='zombie_merged'?'var(--zombie-merged)':st==='zombie_abandoned'?'var(--zombie-abandoned)':'var(--merged-stale)');
    // Approximate rect size
    const approxW = b.n.length * 6 + 12;
    rect.setAttribute('x', lx);
    rect.setAttribute('y', ly);
    rect.setAttribute('width', approxW);
    rect.setAttribute('height', 13);
    rect.setAttribute('rx', 3);
    rect.setAttribute('fill', 'var(--bg-primary)');
    rect.setAttribute('opacity', '0.85');
    labelG.appendChild(rect);
    labelG.appendChild(textEl);
    textEl.addEventListener('click', ev => { ev.stopPropagation(); toggleBranchHighlight(b.n); });
    textEl.style.pointerEvents = 'auto';
    labelG.appendChild(textEl);
    labelOffsets[lane] = (labelOffsets[lane] || 0) + 1;
  });

  fitToScreen();
}

function toggleBranchHighlight(name) {
  const wasSelected = highlightedBranch === name;
  highlightedBranch = wasSelected ? null : name;
  applyHighlight();
  updateLegendSelection();
  if (!wasSelected && highlightedBranch) {
    panToBranch(highlightedBranch);
  }
}

function panToBranch(branchName) {
  // Find the branch tip commit coordinates
  const branch = DATA.branches.find(b => b.n === branchName);
  if (!branch) return;
  const tipCommit = commitMap[branch.h];
  if (!tipCommit) return;

  const targetX = cx(tipCommit.l);
  const targetY = cy(tipCommit.r);

  const container = document.getElementById('graph-container');
  const viewW = container.clientWidth;
  const viewH = container.clientHeight;

  // Target pan: center the commit in viewport
  const targetPanX = -(targetX * scale) + viewW / 2;
  const targetPanY = -(targetY * scale) + viewH / 3;

  // Smooth animate
  const startPanX = panX, startPanY = panY;
  const startTime = performance.now();
  const duration = 300; // ms

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function animate(now) {
    const elapsed = now - startTime;
    const t = Math.min(1, elapsed / duration);
    const eased = easeInOutCubic(t);
    panX = startPanX + (targetPanX - startPanX) * eased;
    panY = startPanY + (targetPanY - startPanY) * eased;
    applyTransform();
    if (t < 1) {
      requestAnimationFrame(animate);
    } else {
      updateMinimap();
    }
  }

  requestAnimationFrame(animate);
}

function applyHighlight() {
  const circles = document.querySelectorAll('.commit-circle');
  const labels = document.querySelectorAll('.branch-label-pill');
  const edges = document.querySelectorAll('.edge-line');
  if (!highlightedBranch) {
    circles.forEach(c => c.classList.remove('dimmed'));
    labels.forEach(l => l.classList.remove('dimmed'));
    edges.forEach(e => e.classList.remove('dimmed'));
    return;
  }
  const branchCommits = new Set();
  DATA.commits.forEach(c => { if (c.b && c.b.includes(highlightedBranch)) branchCommits.add(c.h); });
  circles.forEach(c => {
    c.classList.toggle('dimmed', !branchCommits.has(c.getAttribute('data-hash')));
  });
  labels.forEach(l => {
    l.classList.toggle('dimmed', l.getAttribute('data-branch') !== highlightedBranch);
  });
  edges.forEach(e => {
    const from = e.getAttribute('data-from'), to = e.getAttribute('data-to');
    e.classList.toggle('dimmed', !branchCommits.has(from) && !branchCommits.has(to));
  });
}

function buildLegend() {
  const list = document.getElementById('legend-list');
  const healthMap = {};
  (DATA.health||[]).forEach(h => { healthMap[h.n] = h; });
  DATA.branches.forEach(b => {
    const h = healthMap[b.n];
    const st = h ? h.st : 'healthy';
    const isZ = st === 'zombie_merged' || st === 'zombie_abandoned';
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.setAttribute('data-branch', b.n);
    item.innerHTML = `${statusDot(st)} <span class="name">${escHtml(b.n)}</span>${isZ?' <span class="zombie-tag">(Z)</span>':''}`;
    item.addEventListener('click', () => toggleBranchHighlight(b.n));
    list.appendChild(item);
  });
}

function updateLegendSelection() {
  document.querySelectorAll('.legend-item').forEach(item => {
    item.classList.toggle('selected', item.getAttribute('data-branch') === highlightedBranch);
  });
}

// Pan/zoom
function applyTransform() {
  const g = document.getElementById('root-g');
  if (g) g.setAttribute('transform', `translate(${panX},${panY}) scale(${scale})`);
}

function fitToScreen() {
  const container = document.getElementById('graph-container');
  const H = MARGIN_T + (DATA.metadata.total_rows + 1) * ROW_H + 60;
  scale = Math.max(0.15, Math.min(1, container.clientHeight / H * 0.85));
  panX = 40; panY = 10;
  applyTransform();
}

// Minimap
function updateMinimap() {
  const ms = document.getElementById('minimap-svg');
  const mw = 180, mh = 120;
  ms.setAttribute('viewBox', `0 0 ${mw} ${mh}`);
  ms.setAttribute('width', mw); ms.setAttribute('height', mh);
  ms.innerHTML = '';
  const scaleX = mw / (MARGIN_L + (DATA.metadata.total_lanes + 1) * LANE_W + 100);
  const scaleY = mh / (MARGIN_T + (DATA.metadata.total_rows + 1) * ROW_H + 60);
  const s = Math.min(scaleX, scaleY);

  // Mini commits
  const mg = document.createElementNS('http://www.w3.org/2000/svg','g');
  DATA.commits.forEach(c => {
    const dot = document.createElementNS('http://www.w3.org/2000/svg','circle');
    dot.setAttribute('cx', cx(c.l) * s);
    dot.setAttribute('cy', cy(c.r) * s);
    dot.setAttribute('r', 1.2);
    dot.setAttribute('fill', 'var(--text-secondary)');
    mg.appendChild(dot);
  });
  ms.appendChild(mg);

  // Viewport rect
  const container = document.getElementById('graph-container');
  const vr = document.createElementNS('http://www.w3.org/2000/svg','rect');
  vr.setAttribute('x', -panX / scale * s);
  vr.setAttribute('y', -panY / scale * s);
  vr.setAttribute('width', container.clientWidth / scale * s);
  vr.setAttribute('height', container.clientHeight / scale * s);
  vr.setAttribute('class', 'viewport-rect');
  ms.appendChild(vr);
}

// Detail panel
function showCommitDetail(hash) {
  const c = commitMap[hash];
  if (!c) return;
  const panel = document.getElementById('detail-panel');
  const body = document.getElementById('panel-body');
  const branchBadges = (c.b||[]).map(bn => {
    const h = healthLookup[bn];
    const st = h ? h.st : 'healthy';
    const stLabel = st === 'zombie_merged' ? 'merged-zombie' : st === 'zombie_abandoned' ? 'abandoned' : st;
    return `<span class="badge badge-${st}">${escHtml(bn)}${st!=='healthy'&&st!=='aging'? ' ('+stLabel+')' : ''}</span>`;
  }).join(' ');
  const parentLinks = (c.ph||[]).map(ph => commitMap[ph]
    ? `<a class="parent-link" href="#" data-hash="${ph}">${ph}</a>`
    : `<span style="color:var(--text-secondary)">${ph}</span>`).join(', ') || '<span style="color:var(--text-secondary)">(root)</span>';
  body.innerHTML = `
    <div class="field"><div class="field-label">Hash</div><div class="field-value hash">${c.h}</div></div>
    <div class="field"><div class="field-label">Subject</div><div class="field-value">${escHtml(c.s)}</div></div>
    <div class="field"><div class="field-label">Author</div><div class="field-value">${escHtml(c.a)}</div></div>
    <div class="field"><div class="field-label">Date</div><div class="field-value">${fmtDate(c.t)}</div></div>
    <div class="field"><div class="field-label">Parents</div><div class="field-value">${parentLinks}</div></div>
    ${c.b&&c.b.length?`<div class="field"><div class="field-label">Branches</div><div class="field-value">${branchBadges}</div></div>`:''}
    ${c.rf&&c.rf.length?`<div class="field"><div class="field-label">Tags</div><div class="field-value">${c.rf.map(t=>escHtml(t)).join(', ')}</div></div>`:''}
    <div class="field"><div class="field-label">Full Message</div><div class="field-value message">${escHtml(c.fm||c.s)}</div></div>
    <div class="field"><div class="field-label">Changed Files</div><div id="changed-files-container"></div></div>`;
  panel.classList.add('visible');
  panel.querySelectorAll('.parent-link').forEach(link => {
    link.addEventListener('click', ev => { ev.preventDefault(); const h = link.dataset.hash; if (h && commitMap[h]) showCommitDetail(h); });
  });
  // Fetch changed files if in server mode
  loadChangedFiles(c.h);
}

function hideDetail() { document.getElementById('detail-panel').classList.remove('visible'); }

// ── Changed Files & Diff Viewer ─────────────────────────────────────
async function loadChangedFiles(hash) {
  const container = document.getElementById('changed-files-container');
  if (!container) return;
  if (!isServerMode) {
    container.innerHTML = '<div class="server-hint">Server mode not active. Run with <code>--serve</code> to view changed files and diffs.</div>';
    return;
  }
  container.innerHTML = '<span style="color:var(--text-secondary);font-size:11px">Loading...</span>';
  try {
    const resp = await fetch(`${API_BASE}/api/files/${hash}`);
    const data = await resp.json();
    if (data.error) { container.innerHTML = `<span style="color:var(--zombie-abandoned)">${escHtml(data.error)}</span>`; return; }
    renderChangedFiles(data.files, hash, container);
  } catch (e) {
    container.innerHTML = '<span style="color:var(--zombie-abandoned)">Failed to load changed files</span>';
  }
}

function renderChangedFiles(files, hash, container) {
  if (!files || files.length === 0) {
    container.innerHTML = '<span style="color:var(--text-secondary);font-size:11px">No changed files (merge commit or empty)</span>';
    return;
  }
  container.innerHTML = '<div class="changed-files">' + files.map(f => `
    <div class="changed-file" data-file="${escHtml(f.path)}" onclick="toggleFileDiff('${hash}','${escHtml(f.path.replace(/'/g,"\\'"))}',this)" title="${escHtml(f.path)}">
      <span class="cf-status ${f.status}">${f.status}</span>
      <span class="cf-path">${escHtml(f.path)}</span>
      <span class="cf-stats">+${f.added} -${f.deleted}</span>
    </div>
  `).join('') + '</div>';
}

async function toggleFileDiff(hash, filePath, rowEl) {
  const existing = rowEl.nextElementSibling;
  if (existing && existing.classList.contains('diff-viewer')) {
    existing.remove();
    return;
  }
  // Remove any other open diffs
  document.querySelectorAll('.diff-viewer').forEach(d => d.remove());
  const diffDiv = document.createElement('div');
  diffDiv.className = 'diff-viewer';
  diffDiv.innerHTML = '<div class="diff-content"><span style="color:var(--text-secondary)">Loading diff...</span></div>';
  rowEl.after(diffDiv);
  try {
    const resp = await fetch(`${API_BASE}/api/diff/${hash}?file=${encodeURIComponent(filePath)}`);
    const data = await resp.json();
    if (data.error) { diffDiv.innerHTML = `<span style="color:var(--zombie-abandoned);padding:8px">${escHtml(data.error)}</span>`; return; }
    diffDiv.innerHTML = renderDiff(data.diff, filePath);
  } catch (e) {
    diffDiv.innerHTML = '<span style="color:var(--zombie-abandoned);padding:8px">Failed to load diff</span>';
  }
}

function renderDiff(diffText, filePath) {
  if (!diffText || !diffText.trim()) {
    return '<div class="diff-content"><span style="color:var(--text-secondary);padding:8px;display:block">No changes (binary file or empty diff)</span></div>';
  }
  const lines = diffText.split('\n');
  let html = `<div class="diff-file-header"><span>${escHtml(filePath)}</span></div><div class="diff-content">`;
  for (const line of lines) {
    let cls = '';
    if (line.startsWith('@@')) cls = 'diff-hunk';
    else if (line.startsWith('+')) cls = 'diff-add';
    else if (line.startsWith('-')) cls = 'diff-del';
    else if (line.startsWith('---') || line.startsWith('+++')) cls = 'diff-header-line';
    html += `<div class="diff-line ${cls}">${escHtml(line)||'&nbsp;'}</div>`;
  }
  html += '</div>';
  return html;
}

// Tooltip
let tooltipCommit = null;
const healthLookup = {};
(DATA.health||[]).forEach(h => { healthLookup[h.n] = h; });

function showTooltip(ev, c) {
  tooltipCommit = c;
  const tt = document.getElementById('tooltip');
  let html = `<div class="tt-hash">${c.h}</div>`;
  html += `<div class="tt-subject">${escHtml(c.s)}</div>`;
  html += `<div class="tt-meta">${escHtml(c.a)} &middot; ${fmtDate(c.t)}</div>`;
  if (c.b && c.b.length > 0) {
    html += `<div class="tt-branches">${c.b.map(bn => {
      const h = healthLookup[bn];
      const st = h ? h.st : 'healthy';
      return `<span class="tt-branch-tag ${st}">${statusDot(st)} ${escHtml(bn)}</span>`;
    }).join('')}</div>`;
  }
  if (c.rf && c.rf.length > 0) {
    html += `<div class="tt-branches" style="margin-top:2px">${c.rf.map(t => `<span class="tt-branch-tag healthy">&#x1f3f7; ${escHtml(t)}</span>`).join('')}</div>`;
  }
  tt.innerHTML = html;
  tt.classList.add('visible');
  positionTooltip(ev);
}
function moveTooltip(ev) { if (tooltipCommit) positionTooltip(ev); }
function positionTooltip(ev) {
  const tt = document.getElementById('tooltip');
  let tx = ev.clientX + 14, ty = ev.clientY - 10;
  const tr = tt.getBoundingClientRect();
  if (tx + tr.width > window.innerWidth - 10) tx = ev.clientX - tr.width - 14;
  if (ty + tr.height > window.innerHeight - 10) ty = ev.clientY - tr.height - 10;
  tt.style.left = Math.max(10, tx) + 'px';
  tt.style.top = Math.max(10, ty) + 'px';
}
function hideTooltip() { tooltipCommit = null; document.getElementById('tooltip').classList.remove('visible'); }

// Search
let searchMatches = [], searchIdx = 0;
function doSearch() {
  const q = document.getElementById('graph-search').value.trim().toLowerCase();
  searchMatches = []; searchIdx = 0;
  document.querySelectorAll('.commit-circle').forEach(c => c.classList.remove('dimmed'));
  document.getElementById('match-count').textContent = '';
  if (!q) return;
  document.querySelectorAll('.commit-circle').forEach(c => {
    const hash = c.getAttribute('data-hash');
    const cm = commitMap[hash];
    if (!cm) return;
    const matches = cm.h.toLowerCase().includes(q) || cm.s.toLowerCase().includes(q) || cm.a.toLowerCase().includes(q);
    if (matches) searchMatches.push(c); else c.classList.add('dimmed');
  });
  document.getElementById('match-count').textContent = searchMatches.length ? `${searchMatches.length} matches` : 'No matches';
}

// ═══════════════════════════════════════════════════════════════════
// TAB 3: Timeline
// ═══════════════════════════════════════════════════════════════════
function renderTimeline() {
  // Heatmap
  const hm = DATA.heatmap || [];
  const grid = document.getElementById('heatmap-grid');
  const labels = document.getElementById('heatmap-labels');
  if (hm.length === 0) { grid.innerHTML = '<span style="color:var(--text-secondary)">No activity data</span>'; }
  else {
    const maxC = Math.max(...hm.map(h => h.commits), 1);
    let cellsHtml = '', lblHtml = '';
    const showLabels = hm.length <= 26;
    hm.forEach((h, i) => {
      const intensity = Math.round(h.commits / maxC * 4);
      const colors = ['var(--bg-tertiary)', '#0e4429', '#006d32', '#26a641', '#39d353'];
      cellsHtml += `<div class="heatmap-cell" style="background:${colors[intensity]}" title="${h.period}: ${h.commits} commits, ${h.authors} authors"></div>`;
      if (showLabels && (i === 0 || i === hm.length - 1 || i % Math.ceil(hm.length/6) === 0)) lblHtml += `<span>${h.period}</span>`;
      else if (!showLabels) {
        if (i === 0) lblHtml += `<span>${h.period}</span>`;
        if (i === hm.length - 1) lblHtml += `<span>${h.period}</span>`;
      }
    });
    grid.innerHTML = cellsHtml;
    labels.innerHTML = lblHtml;
  }

  // Fork/merge timeline SVG
  const tl = DATA.timeline;
  const container = document.getElementById('timeline-graph-container');
  if (!tl || !tl.branches || tl.branches.length === 0) {
    if (container) container.innerHTML = '<span style="color:var(--text-secondary);padding:20px;display:block">No timeline data</span>';
    return;
  }

  const showMerged = document.getElementById('tl-merged-toggle')?.checked ?? true;
  const branches = tl.branches.filter(b => showMerged || !b.mg);
  const rowH = 26, topPad = 32, leftPad = 160, rightPad = 40;
  const W = container.clientWidth || 900;
  const H = topPad + branches.length * rowH + 20;

  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);

  const g = document.createElementNS('http://www.w3.org/2000/svg','g');
  svg.appendChild(g);

  // Date ruler
  const plotW = W - leftPad - rightPad;
  const months = [];
  const dMin = new Date(tl.date_min), dMax = new Date(tl.date_max);
  const totalMs = dMax - dMin;
  let cursor = new Date(dMin.getFullYear(), dMin.getMonth(), 1);
  while (cursor <= dMax) {
    months.push(new Date(cursor));
    cursor.setMonth(cursor.getMonth() + 1);
  }
  months.forEach(m => {
    const x = leftPad + ((m - dMin) / totalMs) * plotW;
    const tick = document.createElementNS('http://www.w3.org/2000/svg','line');
    tick.setAttribute('x1', x); tick.setAttribute('x2', x);
    tick.setAttribute('y1', 0); tick.setAttribute('y2', H);
    tick.setAttribute('stroke', 'var(--border)'); tick.setAttribute('stroke-width','0.5');
    g.appendChild(tick);
    const lbl = document.createElementNS('http://www.w3.org/2000/svg','text');
    lbl.setAttribute('x', x + 3); lbl.setAttribute('y', 14);
    lbl.setAttribute('fill', 'var(--text-secondary)'); lbl.setAttribute('font-size','10');
    lbl.setAttribute('font-family', 'var(--font-body)');
    lbl.textContent = m.toISOString().slice(0,7);
    g.appendChild(lbl);
  });

  // Branch rows
  branches.forEach((b, i) => {
    const y = topPad + i * rowH;
    const sx = leftPad + b.sx * plotW;
    const ex = leftPad + b.ex * plotW;

    // Branch name label
    const nameLbl = document.createElementNS('http://www.w3.org/2000/svg','text');
    nameLbl.setAttribute('x', leftPad - 6); nameLbl.setAttribute('y', y + 5);
    nameLbl.setAttribute('text-anchor', 'end');
    nameLbl.setAttribute('fill', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    nameLbl.setAttribute('font-size','10'); nameLbl.setAttribute('font-family','var(--font-mono)');
    nameLbl.textContent = b.n;
    nameLbl.style.cursor = 'pointer';
    nameLbl.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelector('.tab-btn[data-tab="graph"]').classList.add('active');
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.getElementById('graph-tab').classList.add('active');
      setTimeout(() => toggleBranchHighlight(b.n), 100);
    });
    g.appendChild(nameLbl);

    // Lifetime line
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1', sx); line.setAttribute('x2', ex);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    line.setAttribute('stroke', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    line.setAttribute('stroke-width', '2'); line.setAttribute('stroke-linecap','round');
    if (b.mg) line.setAttribute('stroke-dasharray', '6 3');
    line.setAttribute('opacity', '0.6');
    g.appendChild(line);

    // Start dot (fork point)
    const sDot = document.createElementNS('http://www.w3.org/2000/svg','circle');
    sDot.setAttribute('cx', sx); sDot.setAttribute('cy', y);
    sDot.setAttribute('r', b.pb ? 4 : 5);
    sDot.setAttribute('fill', b.pb ? 'var(--bg-primary)' : b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':'var(--zombie-merged)');
    sDot.setAttribute('stroke', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    sDot.setAttribute('stroke-width', '2');
    sDot.setAttribute('data-hash', b.sh);
    g.appendChild(sDot);

    // End dot (tip)
    const eDot = document.createElementNS('http://www.w3.org/2000/svg','circle');
    eDot.setAttribute('cx', ex); eDot.setAttribute('cy', y);
    eDot.setAttribute('r', 5);
    eDot.setAttribute('fill', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    eDot.setAttribute('data-hash', b.eh);
    g.appendChild(eDot);

    // Fork line: diagonal from parent branch to this branch's start
    if (b.pb) {
      const pBranch = branches.find(br => br.n === b.pb);
      if (pBranch) {
        const py = topPad + pBranch.row * rowH;
        // Find parent commit X: use the start X of child (parent commit is just before)
        const px = Math.max(leftPad, sx - 2);
        const forkLine = document.createElementNS('http://www.w3.org/2000/svg','path');
        const cy = (py + y) / 2;
        forkLine.setAttribute('d', `M ${px} ${py} C ${px} ${cy} ${sx} ${cy} ${sx} ${y}`);
        forkLine.setAttribute('stroke', 'var(--text-secondary)');
        forkLine.setAttribute('stroke-width', '1');
        forkLine.setAttribute('stroke-dasharray', '3 2');
        forkLine.setAttribute('fill', 'none');
        forkLine.setAttribute('opacity', '0.4');
        g.appendChild(forkLine);
      }
    }
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

// ═══════════════════════════════════════════════════════════════════
// TAB 4: Authors
// ═══════════════════════════════════════════════════════════════════
function renderAuthors() {
  const au = DATA.author_stats || [];
  const maxC = Math.max(...au.map(a => a.cc), 1);
  document.getElementById('author-bars').innerHTML = au.map(a => `
    <div class="author-bar-row">
      <span class="aname">${escHtml(a.n)}</span>
      <div class="abar-wrap">
        <div class="abar" style="width:${a.cc/maxC*100}%"></div>
      </div>
      <span class="acount">${a.cc} commits (${a.pc}%)</span>
    </div>`).join('');

  const bf = DATA.bus_factor_warnings || [];
  const bfDiv = document.getElementById('bus-factor-list');
  if (bf.length === 0) {
    bfDiv.innerHTML = '<span style="color:var(--text-secondary)">No bus factor warnings detected</span>';
  } else {
    bfDiv.innerHTML = bf.map(w => `
      <div class="bf-warning">
        <span class="bf-icon">!</span>
        <div>
          <div class="bf-file">${escHtml(w.fp)}</div>
          <div class="bf-detail">${escHtml(w.da)}: ${w.dp}% &middot; ${w.ta} authors &middot; Bus Factor = ${w.bf}</div>
        </div>
      </div>`).join('');
  }
}

// ═══════════════════════════════════════════════════════════════════
// Event Wiring
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  renderOverview();
  buildLegend();
  renderGraph();
  renderTimeline();
  renderAuthors();

  // Theme toggle
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const el = document.documentElement;
    const isLight = el.dataset.theme === 'light';
    if (isLight) {
      delete el.dataset.theme;
      localStorage.setItem('git-graph-theme', 'dark');
    } else {
      el.dataset.theme = 'light';
      localStorage.setItem('git-graph-theme', 'light');
    }
  });

  // Graph interaction handlers
  const container = document.getElementById('graph-container');
  container.addEventListener('wheel', ev => {
    ev.preventDefault();
    const delta = ev.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.min(5, Math.max(0.1, scale * delta));
    const rect = container.getBoundingClientRect();
    panX = (ev.clientX - rect.left) - ((ev.clientX - rect.left) - panX) * (newScale / scale);
    panY = (ev.clientY - rect.top) - ((ev.clientY - rect.top) - panY) * (newScale / scale);
    scale = newScale;
    applyTransform();
    updateMinimap();
  });
  container.addEventListener('mousedown', ev => {
    if (ev.target !== container && ev.target !== document.getElementById('graph-svg') && ev.target.tagName !== 'g') return;
    isDragging = true; dragStartX = ev.clientX; dragStartY = ev.clientY;
    panStartX = panX; panStartY = panY;
    container.style.cursor = 'grabbing';
  });
  window.addEventListener('mousemove', ev => {
    if (!isDragging) return;
    panX = panStartX + (ev.clientX - dragStartX);
    panY = panStartY + (ev.clientY - dragStartY);
    applyTransform();
    updateMinimap();
  });
  window.addEventListener('mouseup', () => {
    isDragging = false;
    document.getElementById('graph-container').style.cursor = 'grab';
  });
  document.getElementById('btn-fit').addEventListener('click', () => { fitToScreen(); updateMinimap(); });
  document.getElementById('btn-reset').addEventListener('click', () => { scale = 1; panX = 0; panY = 0; applyTransform(); updateMinimap(); });
  document.getElementById('panel-close').addEventListener('click', hideDetail);
  document.getElementById('graph-search').addEventListener('input', doSearch);

  // Keyboard
  window.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') {
      hideDetail();
      highlightedBranch = null;
      applyHighlight();
      updateLegendSelection();
      document.getElementById('graph-search').value = '';
      doSearch();
    }
    if (ev.key === 'f' && !ev.ctrlKey && !ev.metaKey && document.activeElement === document.body) {
      fitToScreen(); updateMinimap();
    }
    if (ev.key === '=' || ev.key === '+') {
      ev.preventDefault();
      scale = Math.min(5, scale * 1.2);
      applyTransform(); updateMinimap();
    }
    if (ev.key === '-') {
      ev.preventDefault();
      scale = Math.max(0.1, scale * 0.85);
      applyTransform(); updateMinimap();
    }
  });

  // Minimap click to navigate
  document.getElementById('minimap-svg').addEventListener('click', ev => {
    const rect = ev.target.getBoundingClientRect();
    const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
    const s = Math.min(180 / (MARGIN_L + (DATA.metadata.total_lanes+1)*LANE_W+100),
                       120 / (MARGIN_T + (DATA.metadata.total_rows+1)*ROW_H+60));
    const container = document.getElementById('graph-container');
    panX = -(mx / s) + container.clientWidth / 2 / scale;
    panY = -(my / s) + container.clientHeight / 2 / scale;
    applyTransform();
    updateMinimap();
  });
});
</script>
</body>
</html>"""
