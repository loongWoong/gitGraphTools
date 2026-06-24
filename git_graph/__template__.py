"""HTML template for the git repository intelligence dashboard.

3-tab layout: Overview | Graph | Insights
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

/* ── Sub-Navigation Pills ──────────────────────────────────────── */
.sub-nav {
  display: flex; gap: 4px; padding: 8px 16px;
  background: var(--bg-secondary); border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.sub-nav-btn {
  padding: 4px 12px; border-radius: 14px;
  border: 1px solid var(--border); background: none;
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
  font-family: var(--font-body); white-space: nowrap;
}
.sub-nav-btn:hover { color: var(--text-primary); border-color: var(--text-secondary); }
.sub-nav-btn.active { background: var(--text-link); border-color: var(--text-link); color: #fff; }

/* ── Insights Sidebar ──────────────────────────────────────────── */
#insights-sidebar {
  width: 160px; background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  overflow-y: auto; flex-shrink: 0; padding: 8px 0;
}
.insight-nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; cursor: pointer; font-size: 12px;
  color: var(--text-secondary); transition: background 0.1s;
  user-select: none; border-left: 2px solid transparent;
}
.insight-nav-item:hover { background: var(--bg-tertiary); color: var(--text-primary); }
.insight-nav-item.active {
  background: rgba(88,166,255,0.08); color: var(--text-link);
  border-left-color: var(--text-link);
}
.insight-panel { display: none; flex: 1; overflow-y: auto; }
.insight-panel.active { display: block; }

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
.action-dot {
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

/* ── DORA Cards (Overview) ─────────────────────────────────────── */
.dora-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.dora-metric-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 16px;
  text-align: center;
  position: relative;
}
.dora-metric-card .dmc-value {
  font-size: 30px; font-weight: 700;
  font-family: var(--font-mono); color: var(--text-link);
}
.dora-metric-card .dmc-label {
  font-size: 11px; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px;
}
.dora-metric-card .dmc-sub {
  font-size: 11px; color: var(--text-secondary); margin-top: 4px;
}
.dmc-tier {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 10px; font-weight: 600; margin-top: 6px; text-transform: uppercase;
}
.dmc-tier.elite { background: rgba(35,134,54,0.15); color: var(--healthy); }
.dmc-tier.high { background: rgba(88,166,255,0.15); color: var(--text-link); }
.dmc-tier.medium { background: rgba(210,153,34,0.15); color: var(--aging); }
.dmc-tier.low { background: rgba(248,81,73,0.15); color: var(--zombie-abandoned); }
.dmc-confidence {
  font-size: 9px; color: var(--text-secondary); margin-top: 4px;
  opacity: 0.7;
}

/* ── Delivery Pipeline (Overview) ──────────────────────────────── */
.delivery-pipeline {
  display: flex; gap: 0; padding: 8px 16px;
  border-radius: var(--radius); overflow: hidden;
}
.pipeline-stage {
  flex: 1; text-align: center; padding: 16px 12px;
  cursor: pointer; transition: background 0.15s; position: relative;
  border-right: 1px solid var(--border);
}
.pipeline-stage:last-child { border-right: none; }
.pipeline-stage:hover { background: var(--bg-tertiary); }
.pipeline-stage .ps-count { font-size: 28px; font-weight: 700; }
.pipeline-stage .ps-label { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.pipeline-stage .ps-arrow {
  position: absolute; right: -10px; top: 50%; transform: translateY(-50%);
  font-size: 14px; color: var(--text-secondary); z-index: 1; pointer-events: none;
}
/* Pipeline stage expanded list */
.pipeline-detail {
  padding: 0 16px 16px;
  display: none;
}
.pipeline-detail.open { display: block; }
.pipeline-detail .pd-item {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 10px; font-size: 12px; border-radius: 4px;
  cursor: pointer;
}
.pipeline-detail .pd-item:hover { background: var(--bg-tertiary); }
.pipeline-detail .pd-name { font-family: var(--font-mono); font-size: 11px; flex: 1; }
.pipeline-detail .pd-meta { font-size: 10px; color: var(--text-secondary); }

/* ── Pulse Grid (Overview) ─────────────────────────────────────── */
.pulse-week-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 8px;
}
.pulse-week-cell {
  background: var(--bg-tertiary); border-radius: var(--radius);
  padding: 14px; text-align: center;
}
.pulse-week-cell .pw-date { font-size: 10px; color: var(--text-secondary); margin-bottom: 4px; }
.pulse-week-cell .pw-commits { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.pulse-week-cell .pw-meta { font-size: 10px; color: var(--text-secondary); margin-top: 2px; }

/* ── DORA Details Panel (Overview expandable) ──────────────────── */
#dora-details { display: none; }
#dora-details.open { display: contents; }
.lead-time-histogram { display: flex; align-items: flex-end; gap: 2px; padding: 12px 16px 0; height: 140px; }
.hist-bar { flex: 1; border-radius: 3px 3px 0 0; min-width: 3px; transition: opacity 0.15s; }
.hist-bar:hover { opacity: 1 !important; }
.hist-labels { display: flex; justify-content: space-between; padding: 4px 16px 8px; font-size: 9px; color: var(--text-secondary); }
.pr-merge-bars { display: flex; gap: 24px; padding: 16px; align-items: flex-end; height: 140px; }
.pr-merge-bar-wrap { flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.pr-merge-bar { width: 100%; max-width: 60px; border-radius: 4px 4px 0 0; transition: height 0.5s ease; }
.pr-merge-bar.merge { background: var(--healthy); }
.pr-merge-bar.squash { background: var(--text-link); }
.pr-merge-bar.rebase { background: var(--aging); }
.pr-merge-value { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-top: 4px; }
.pr-merge-label { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }

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

/* ── Timeline (in Graph sub-view) ───────────────────────────────── */
.timeline-wrap { padding: 24px; gap: 24px; }

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

/* ── Author Bars ───────────────────────────────────────────────── */
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

/* ── Conflict Alerts ──────────────────────────────────── */
.conflict-alert {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-left: 3px solid var(--aging);
  border-radius: var(--radius);
  padding: 12px 16px;
  margin-bottom: 8px;
}
.conflict-alert.high-risk { border-left-color: var(--zombie-abandoned); background: #f8514910; }
.conflict-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.conflict-branches { font-family: var(--font-mono); font-size: 13px; }
.conflict-score { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.conflict-score.risky { background: #f8514933; color: var(--zombie-abandoned); }
.conflict-files { font-size: 11px; color: var(--text-secondary); }

/* ── AI: NL Query ─────────────────────────────────────────── */
.nl-query-box { display: flex; gap: 8px; margin: 16px 0; }
.nl-input {
  flex: 1; padding: 10px 14px;
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: var(--radius); color: var(--text-primary);
  font-size: 13px; font-family: var(--font-body);
}
.nl-input:focus { outline: none; border-color: var(--text-link); }
.nl-btn {
  padding: 10px 18px;
  background: var(--text-link); color: #fff; border: none;
  border-radius: var(--radius); font-size: 13px; cursor: pointer;
  font-weight: 500;
}
.nl-results { margin-top: 12px; }
.nl-result-item {
  padding: 8px 12px; border-bottom: 1px solid var(--border);
  font-size: 13px; color: var(--text-primary);
}

/* ── Topology Graph ─────────────────────────────────── */
.topo-container { flex: 1; overflow: auto; position: relative; padding: 24px; }
#topo-svg { min-width: 100%; min-height: 100%; }
.topo-node {
  cursor: pointer; transition: opacity 0.2s;
  stroke-width: 2;
}
.topo-node:hover { stroke-width: 3; }
.topo-node.healthy { fill: rgba(35,134,54,0.1); stroke: var(--healthy); }
.topo-node.aging { fill: rgba(210,153,34,0.1); stroke: var(--aging); }
.topo-node.zombie_merged { fill: rgba(137,87,229,0.1); stroke: var(--zombie-merged); }
.topo-node.zombie_abandoned { fill: rgba(248,81,73,0.1); stroke: var(--zombie-abandoned); }
.topo-node.merged_stale { fill: rgba(110,118,129,0.1); stroke: var(--merged-stale); }
.topo-node.main-branch { fill: rgba(88,166,255,0.15); stroke: var(--text-link); stroke-width: 2.5; }
.topo-node.faded { opacity: 0.25; }
.topo-edge { stroke: var(--border); stroke-width: 1.5; fill: none; marker-end: url(#topo-arrow); }
.topo-edge.highlight { stroke: var(--text-link); stroke-width: 2.5; }
.topo-edge.faded { opacity: 0.15; }
.topo-label { font-size: 10px; font-family: var(--font-mono); fill: var(--text-primary); pointer-events: none; }
.topo-info {
  font-size: 11px; color: var(--text-secondary); padding: 6px 14px;
  border-top: 1px solid var(--border); min-height: 28px;
}
.topo-info strong { color: var(--text-primary); }

/* ── Cleanup List ─────────────────────────────────────── */
.cleanup-category { margin-bottom: 12px; }
.cleanup-category .cc-header {
  font-size: 10px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px; padding: 6px 12px;
  display: flex; align-items: center; gap: 8px;
}
.cc-count {
  font-size: 10px; color: var(--text-secondary);
  background: var(--bg-tertiary); padding: 1px 6px; border-radius: 8px;
}
.cleanup-row {
  display: flex; align-items: center; padding: 8px 12px;
  border-bottom: 1px solid var(--border); gap: 12px;
  font-size: 12px;
}
.cleanup-row .safe-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.cleanup-row .safe-dot.safe { background: var(--healthy); }
.cleanup-row .safe-dot.warn { background: var(--aging); }
.cleanup-row .cl-name { font-family: var(--font-mono); font-size: 13px; font-weight: 500; flex: 1; }
.cleanup-row .cl-reason { color: var(--text-secondary); flex: 2; }
.cleanup-row .cl-cmd {
  font-family: var(--font-mono); font-size: 10px;
  color: var(--text-secondary); background: var(--bg-tertiary);
  padding: 3px 8px; border-radius: 4px; cursor: pointer;
}
.btn-cleanup-all {
  margin: 8px 12px; padding: 8px 16px;
  background: var(--healthy); color: #fff; border: none;
  border-radius: var(--radius); font-size: 12px; cursor: pointer; font-weight: 500;
}

/* ── Command Palette ──────────────────────────────────── */
.palette-overlay {
  display: none; position: fixed; inset: 0;
  background: #00000099; z-index: 9999;
  justify-content: center; padding-top: 15vh;
}
.palette-overlay.open { display: flex; }
.palette-box {
  width: 600px; max-height: 400px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 16px 48px #00000066;
  display: flex; flex-direction: column; overflow: hidden;
}
.palette-input {
  padding: 14px 18px; font-size: 15px;
  background: transparent; border: none; border-bottom: 1px solid var(--border);
  color: var(--text-primary); font-family: var(--font-body); outline: none;
}
.palette-results { flex: 1; overflow-y: auto; }
.palette-group { padding: 4px 0; }
.palette-group-label {
  padding: 6px 18px; font-size: 10px; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 1px; font-weight: 600;
}
.palette-result {
  padding: 8px 18px; font-size: 13px; color: var(--text-primary);
  cursor: pointer; display: flex; justify-content: space-between; align-items: center;
}
.palette-result.selected { background: var(--bg-tertiary); }
.palette-result .pr-shortcut { font-size: 10px; color: var(--text-secondary); }

/* ── Keyboard Shortcuts Modal ─────────────────────────── */
.shortcuts-modal {
  display: none; position: fixed; inset: 0;
  background: #00000099; z-index: 10000;
  justify-content: center; align-items: center;
}
.shortcuts-modal.open { display: flex; }
.shortcuts-box {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px; padding: 24px;
  max-width: 500px; width: 90%; max-height: 70vh; overflow-y: auto;
}
.shortcuts-box h2 { font-size: 16px; margin-bottom: 16px; color: var(--text-primary); }
.shortcuts-table { width: 100%; border-collapse: collapse; }
.shortcuts-table td { padding: 6px 0; font-size: 13px; color: var(--text-primary); border-bottom: 1px solid var(--border); }
.shortcuts-table td:first-child {
  font-family: var(--font-mono); font-size: 12px;
  color: var(--text-link); font-weight: 500; width: 140px;
}

/* ── Live Reload Notification ─────────────────────────── */
#live-notify {
  display: none; position: fixed; top: 0; left: 0; right: 0;
  background: var(--text-link); color: #fff; text-align: center;
  padding: 8px; font-size: 12px; cursor: pointer; z-index: 9998;
}

/* ── Multi-Repo Compare ───────────────────────────────── */
.compare-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px; padding: 16px;
}
.compare-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}
.compare-card h3 { font-size: 15px; color: var(--text-link); margin-bottom: 12px; }
.compare-card .cm-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; }
.compare-card .cm-row .cmlabel { color: var(--text-secondary); }
.compare-card .cm-row .cmvalue { color: var(--text-primary); }

/* ── Risk banner ───────────────────────────────────────── */
.risk-banner {
  padding: 10px 16px; margin-bottom: 0;
  border-radius: var(--radius);
}
.risk-item {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 8px; font-size: 11px; border-radius: 4px; margin-bottom: 2px;
}
.risk-item.high { background: rgba(248,81,73,0.08); }
.risk-item.medium { background: rgba(210,153,34,0.06); }
.risk-item.low { background: rgba(88,166,255,0.04); }
.risk-sev { font-size: 12px; flex-shrink: 0; }
</style>
</head>
<body>

<!-- ── Tab Navigation ──────────────────────────────────────────── -->
<div id="tab-nav">
  <button class="tab-btn active" data-tab="overview">Overview</button>
  <button class="tab-btn" data-tab="graph">Graph</button>
  <button class="tab-btn" data-tab="insights">Insights</button>
  <button class="tab-btn" id="compare-tab-btn" style="display:none" data-tab="compare">Compare</button>
  <span style="flex:1"></span>
  <button id="theme-toggle" title="Toggle light/dark theme" style="background:none;border:1px solid var(--border);color:var(--text-secondary);cursor:pointer;padding:4px 10px;border-radius:var(--radius);font-size:14px;">&#x263C;</button>
</div>

<!-- ══════════════════════════════════════════════════════════════ -->
<!-- TAB 1: Overview                                                 -->
<!-- ══════════════════════════════════════════════════════════════ -->
<div class="tab-content active" id="overview-tab">

  <!-- Repo Health + Quick Actions row -->
  <div class="overview-row">
    <div class="health-gauge" id="health-gauge"></div>
    <div class="section-card quick-actions" id="quick-actions"></div>
  </div>

  <!-- DORA Metrics row -->
  <div class="section-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <h3 style="margin-bottom:0">Delivery Performance (DORA)</h3>
      <button id="dora-details-toggle" class="nl-btn" style="padding:4px 12px;font-size:11px;background:var(--bg-tertiary);color:var(--text-secondary);border:1px solid var(--border);">
        View Details
      </button>
    </div>
    <div class="dora-row" id="dora-metrics" style="margin-top:12px;"></div>
    <div id="dora-details" style="margin-top:12px;border-top:1px solid var(--border);padding-top:16px;">
      <div class="overview-row">
        <div class="section-card"><h3>Lead Time Distribution</h3><div class="lead-time-histogram" id="lt-histogram"></div><div class="hist-labels" id="lt-hist-labels"></div></div>
        <div class="section-card"><h3>PR Merge Methods</h3><div class="pr-merge-bars" id="pr-merge-chart"></div></div>
      </div>
    </div>
  </div>

  <!-- Activity Pulse -->
  <div class="section-card">
    <h3>Activity Pulse</h3>
    <div class="pulse-week-grid" id="pulse-week-grid"></div>
  </div>

  <!-- Branch Delivery Pipeline -->
  <div class="section-card">
    <h3>Branch Delivery Pipeline</h3>
    <div class="delivery-pipeline" id="delivery-pipeline"></div>
    <div class="pipeline-detail" id="pipeline-detail"></div>
  </div>

  <!-- Risk Warnings row -->
  <div class="section-card" id="risk-section" style="display:none;">
    <h3>Risk Branches</h3>
    <div id="risk-banner"></div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════ -->
<!-- TAB 2: Graph (with sub-views: DAG / Timeline / Lifecycle)      -->
<!-- ══════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="graph-tab">
  <!-- Sub-navigation -->
  <div class="sub-nav" id="graph-sub-nav" style="display:none;">
    <button class="sub-nav-btn active" data-sub="dag">DAG</button>
    <button class="sub-nav-btn" data-sub="timeline">Timeline</button>
    <button class="sub-nav-btn" data-sub="lifecycle">Lifecycle</button>
  </div>

  <!-- DAG sub-view -->
  <div class="graph-sub" id="graph-sub-dag" style="display:flex;flex-direction:row;flex:1;">
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

  <!-- Timeline sub-view -->
  <div class="graph-sub" id="graph-sub-timeline" style="display:none;flex:1;overflow:auto;flex-direction:column;">
    <div class="section-card" style="flex:1;display:flex;flex-direction:column;min-height:0;margin:24px 24px 12px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
        <h3>Branch Fork &amp; Merge Timeline</h3>
        <label style="font-size:11px;color:var(--text-secondary);cursor:pointer">
          <input type="checkbox" id="tl-merged-toggle" checked onchange="renderTimeline()"> Show merged
        </label>
      </div>
      <div id="timeline-graph-container" style="flex:1;overflow:auto;position:relative;min-height:0;background:var(--bg-primary);border:1px solid var(--border);border-radius:var(--radius)"></div>
    </div>
    <div class="section-card" style="margin:0 24px 24px;">
      <h3>Commit Activity Heatmap</h3>
      <div class="heatmap-grid" id="heatmap-grid"></div>
      <div class="heatmap-labels" id="heatmap-labels"></div>
    </div>
  </div>

  <!-- Lifecycle sub-view -->
  <div class="graph-sub" id="graph-sub-lifecycle" style="display:none;flex:1;overflow:auto;padding:24px;">
    <div class="section-card">
      <h3>Branch Lifetime Overview</h3>
      <div class="lifetime-bars" id="lifetime-bars"></div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════ -->
<!-- TAB 3: Insights (sidebar + panels)                              -->
<!-- ══════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="insights-tab" style="flex-direction:row;">
  <div id="insights-sidebar">
    <div class="insight-nav-item active" data-insight="authors">&#x1F464; Authors</div>
    <div class="insight-nav-item" data-insight="topology">&#x1F310; Topology</div>
    <div class="insight-nav-item" data-insight="ai">&#x1F4A1; AI Analysis</div>
    <div class="insight-nav-item" data-insight="cleanup">&#x1F9F9; Cleanup</div>
  </div>

  <!-- Authors panel -->
  <div class="insight-panel active" id="insight-authors" style="padding:24px;">
    <div class="section-card">
      <h3>Author Contributions</h3>
      <div id="author-bars"></div>
    </div>
    <div class="section-card" style="margin-top:16px;">
      <h3>Bus Factor Warnings</h3>
      <div id="bus-factor-list"></div>
    </div>
  </div>

  <!-- Topology panel -->
  <div class="insight-panel" id="insight-topology" style="display:flex;flex-direction:column;">
    <div class="sub-nav" style="border-bottom:1px solid var(--border);">
      <input type="text" id="topo-search" placeholder="Filter branches..." style="background:var(--bg-primary);border:1px solid var(--border);color:var(--text-primary);padding:4px 10px;border-radius:var(--radius);font-size:11px;width:180px;outline:none;" oninput="filterTopo()">
      <span style="flex:1"></span>
      <span style="font-size:11px;color:var(--text-secondary);">Click node to go to Graph &middot; Hover to explore</span>
    </div>
    <div class="topo-container" id="topo-container">
      <svg id="topo-svg"></svg>
    </div>
    <div class="topo-info" id="topo-info">Hover over a branch node to see its relationships.</div>
  </div>

  <!-- AI Analysis panel -->
  <div class="insight-panel" id="insight-ai" style="padding:24px;">
    <div class="section-card">
      <h3>Ask About Your Repository</h3>
      <div class="nl-query-box">
        <input class="nl-input" id="nl-input" placeholder="e.g. who committed most, branches not updated, conflict risk, safe to delete, hotspot files..." />
        <button class="nl-btn" id="nl-search-btn">Ask</button>
      </div>
      <div id="nl-results" class="nl-results"></div>
    </div>
    <div class="section-card" style="margin-top:16px">
      <h3>Merge Conflict Risks</h3>
      <div id="conflict-risks"></div>
    </div>
    <div class="section-card" style="margin-top:16px">
      <h3>Branch Summaries</h3>
      <div id="branch-summaries"></div>
    </div>
    <div class="section-card" style="margin-top:16px">
      <h3>Release Notes Draft</h3>
      <pre id="release-notes" style="font-size:12px;color:var(--text-secondary);white-space:pre-wrap;max-height:300px;overflow-y:auto;padding:12px;background:var(--bg-primary);border-radius:var(--radius);"></pre>
      <button id="copy-rn-btn" class="nl-btn" style="margin-top:8px">Copy Release Notes</button>
    </div>
  </div>

  <!-- Cleanup panel -->
  <div class="insight-panel" id="insight-cleanup" style="padding:24px;">
    <div class="section-card">
      <h3>Safe Deletion Candidates</h3>
      <div id="cleanup-list"></div>
    </div>
  </div>
</div>

<!-- ── Compare Tab (hidden unless --compare) ─────────────────── -->
<div class="tab-content" id="compare-tab">
  <div style="padding:16px;overflow-y:auto;flex:1">
    <div class="compare-grid" id="compare-grid"></div>
  </div>
</div>

<!-- Command Palette -->
<div class="palette-overlay" id="palette-overlay">
  <div class="palette-box">
    <input class="palette-input" id="palette-input" placeholder="Search branches, commits, authors, views..." />
    <div class="palette-results" id="palette-results"></div>
  </div>
</div>

<!-- Keyboard Shortcuts Modal -->
<div class="shortcuts-modal" id="shortcuts-modal">
  <div class="shortcuts-box">
    <h2>Keyboard Shortcuts</h2>
    <table class="shortcuts-table">
      <tr><td>1 / 2 / 3</td><td>Switch tabs (1=Overview, 2=Graph, 3=Insights)</td></tr>
      <tr><td>Ctrl+K / Cmd+K</td><td>Open command palette</td></tr>
      <tr><td>Escape</td><td>Close palette / Clear selection</td></tr>
      <tr><td>g o</td><td>Go to Overview</td></tr>
      <tr><td>g g</td><td>Go to Graph</td></tr>
      <tr><td>g t</td><td>Go to Timeline (in Graph)</td></tr>
      <tr><td>g a</td><td>Go to Authors (in Insights)</td></tr>
      <tr><td>g i</td><td>Go to AI Analysis (in Insights)</td></tr>
      <tr><td>?</td><td>Show this help</td></tr>
      <tr><td>/</td><td>Focus search (Graph view)</td></tr>
      <tr><td>F</td><td>Fit graph to screen</td></tr>
      <tr><td>+ / -</td><td>Zoom in / out</td></tr>
      <tr><td>Shift+J / Shift+K</td><td>Cycle branch highlight</td></tr>
    </table>
  </div>
</div>

<!-- Live Reload Notification -->
<div id="live-notify">Repository updated — click to refresh</div>

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

// ── Helpers ──────────────────────────────────────────────────────────
function escHtml(s) { if (!s) return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString(); } catch { return iso; } }
function fmtDateShort(iso) { if (!iso) return ''; try { const d=new Date(iso); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0'); } catch { return iso; } }
function statusDot(status) { return `<span class="dot ${status}"></span>`; }
function daysAgo(iso) { if (!iso) return ''; try { const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000); return d === 0 ? 'today' : d === 1 ? '1d ago' : d + 'd ago'; } catch { return ''; } }

const healthLookup = {};
(DATA.health||[]).forEach(h => { healthLookup[h.n] = h; });

// ═══════════════════════════════════════════════════════════════════
// TAB SWITCHING
// ═══════════════════════════════════════════════════════════════════
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const btn = document.querySelector(`[data-tab="${name}"]`);
  const tab = document.getElementById(name + '-tab');
  if (btn) btn.classList.add('active');
  if (tab) tab.classList.add('active');

  if (name === 'graph') {
    document.getElementById('graph-sub-nav').style.display = 'flex';
    switchGraphSub('dag');
  } else {
    const subNav = document.getElementById('graph-sub-nav');
    if (subNav) subNav.style.display = 'none';
  }

  if (name === 'overview') { renderHealthGauge(); renderDORAOverview(); renderPulseGrid(); renderDeliveryPipeline(); renderRiskBanner(); }
  if (name === 'insights') switchInsight('authors');
  if (name === 'compare') renderComparison();
}

// ── Graph Sub-Navigation ────────────────────────────────────────────
function switchGraphSub(name) {
  document.querySelectorAll('#graph-sub-nav .sub-nav-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`#graph-sub-nav [data-sub="${name}"]`);
  if (btn) btn.classList.add('active');
  document.querySelectorAll('.graph-sub').forEach(c => c.style.display = 'none');
  const panel = document.getElementById('graph-sub-' + name);
  if (panel) panel.style.display = name === 'dag' ? 'flex' : (name === 'timeline' ? 'flex' : 'block');
  if (name === 'dag') updateMinimap();
  if (name === 'timeline') renderTimeline();
  if (name === 'lifecycle') renderLifecycle();
}

document.querySelectorAll('#graph-sub-nav .sub-nav-btn').forEach(btn => {
  btn.addEventListener('click', () => switchGraphSub(btn.dataset.sub));
});

// ── Insights Sidebar ────────────────────────────────────────────────
function switchInsight(name) {
  document.querySelectorAll('.insight-nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.insight-panel').forEach(c => c.classList.remove('active'));
  const nav = document.querySelector(`.insight-nav-item[data-insight="${name}"]`);
  const panel = document.getElementById('insight-' + name);
  if (nav) nav.classList.add('active');
  if (panel) panel.classList.add('active');
  if (name === 'authors') renderAuthors();
  if (name === 'topology') renderTopology();
  if (name === 'ai') { renderConflictRisks(); renderAISummaries(); }
  if (name === 'cleanup') renderCleanupSuggestions();
}

document.querySelectorAll('.insight-nav-item').forEach(item => {
  item.addEventListener('click', () => switchInsight(item.dataset.insight));
});

// ═══════════════════════════════════════════════════════════════════
// OVERVIEW: Health Gauge + Quick Actions
// ═══════════════════════════════════════════════════════════════════
function renderHealthGauge() {
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
      <div style="color:var(--text-secondary);font-size:12px;margin-top:2px;">
        ${DATA.metadata.total_commits} commits &middot; ${DATA.metadata.total_branches} branches &middot; ${DATA.author_stats.length} authors
      </div>
    </div>`;

  // Quick actions
  const qa = document.getElementById('quick-actions');
  let qaHtml = '<h3>Quick Actions</h3>';
  const zombies = DATA.health.filter(h => h.st === 'zombie_merged' || h.st === 'zombie_abandoned');
  const stale = DATA.health.filter(h => h.st === 'merged_stale');
  const aging = DATA.health.filter(h => h.st === 'aging');
  qaHtml += `<div class="action-item" onclick="switchTab('insights');switchInsight('cleanup')" style="cursor:pointer;">${statusDot('zombie_merged')} ${zombies.length} zombie branches (safe to delete)</div>`;
  qaHtml += `<div class="action-item" onclick="switchTab('insights');switchInsight('cleanup')" style="cursor:pointer;">${statusDot('merged_stale')} ${stale.length} merged-stale branches (can delete)</div>`;
  qaHtml += `<div class="action-item" onclick="switchTab('insights');switchInsight('ai')" style="cursor:pointer;">${statusDot('aging')} ${aging.length} aging branches &middot; ${zombies.filter(h=>h.st==='zombie_abandoned').length} abandoned</div>`;
  qaHtml += `<div class="action-item">${statusDot('healthy')} ${DATA.health.filter(h=>h.st==='healthy').length} healthy branches</div>`;
  qa.innerHTML = qaHtml;
}

// ═══════════════════════════════════════════════════════════════════
// OVERVIEW: DORA Metrics with confidence
// ═══════════════════════════════════════════════════════════════════
function computeConfidence() {
  const dr = DATA.dr || {};
  const localBranches = (DATA.branches || []).filter(b => b.k === 'local' && !['main','master','develop'].includes(b.n));
  const mergedBranches = localBranches.filter(b => healthLookup[b.n] && healthLookup[b.n].mg);
  const totalB = localBranches.length || 1;
  const ltConf = Math.round(mergedBranches.length / totalB * 100);
  const dfConf = dr.df > 0 ? 80 : 10;
  const cfrConf = dr.cfr > 0 ? 60 : 10;
  const mttrConf = dr.mttr > 0 ? 50 : 0;
  return { lt: ltConf, df: dfConf, cfr: cfrConf, mttr: mttrConf };
}

function doraTier(metric, value) {
  // DORA 2024 benchmarks: Elite / High / Medium / Low
  if (metric === 'df') return value >= 7 ? 'elite' : value >= 1 ? 'high' : value >= 0.25 ? 'medium' : 'low';
  if (metric === 'lt') return value < 1 ? 'elite' : value < 24 ? 'high' : value < 168 ? 'medium' : 'low';
  if (metric === 'cfr') return value < 5 ? 'elite' : value < 10 ? 'high' : value < 15 ? 'medium' : 'low';
  if (metric === 'mttr') return value < 1 ? 'elite' : value < 24 ? 'high' : value < 168 ? 'medium' : 'low';
  return 'medium';
}

function renderDORAOverview() {
  const dr = DATA.dr || {};
  const lt = dr.lt || {};
  const cfrPct = (dr.cfr || 0) * 100;
  const conf = computeConfidence();

  const metrics = [
    { v: dr.df || 0, l: 'Deployment Frequency', s: 'deploys/week', t: doraTier('df', dr.df || 0), c: conf.df },
    { v: (lt.med || 0) + 'h', l: 'Lead Time (median)', s: 'P75: ' + (lt.p75 || 0) + 'h', t: doraTier('lt', lt.med || 0), c: conf.lt },
    { v: cfrPct.toFixed(1) + '%', l: 'Change Failure Rate', s: 'revert/hotfix ratio', t: doraTier('cfr', cfrPct), c: conf.cfr },
    { v: (dr.mttr || 0) + 'h', l: 'Mean Time to Recovery', s: 'avg recovery time', t: doraTier('mttr', dr.mttr || 0), c: conf.mttr },
  ];

  document.getElementById('dora-metrics').innerHTML = metrics.map(m => `
    <div class="dora-metric-card">
      <div class="dmc-value">${m.v}</div>
      <div class="dmc-label">${m.l}</div>
      <div class="dmc-sub">${m.s}</div>
      <span class="dmc-tier ${m.t}">${m.t}</span>
      <div class="dmc-confidence">confidence: ~${m.c}%</div>
    </div>`).join('');

  // Details panel (histogram + PR merge)
  const raw = lt.raw || [];
  const histDiv = document.getElementById('lt-histogram');
  const histLabels = document.getElementById('lt-hist-labels');
  if (raw.length > 1) {
    const bins = 10;
    const maxV = Math.max(...raw, 1);
    const bucketSize = maxV / bins;
    const buckets = new Array(bins).fill(0);
    raw.forEach(v => { const idx = Math.min(bins - 1, Math.floor(v / bucketSize)); buckets[idx]++; });
    const maxB = Math.max(...buckets, 1);
    histDiv.innerHTML = buckets.map((b, i) => {
      const h = Math.max(4, b / maxB * 120);
      const tier = doraTier('lt', (i + 0.5) * bucketSize);
      const color = tier === 'elite' ? 'var(--healthy)' : tier === 'high' ? 'var(--text-link)' : tier === 'medium' ? 'var(--aging)' : 'var(--zombie-abandoned)';
      return `<div class="hist-bar" style="height:${h}px;background:${color};opacity:0.7" title="${Math.round(i*bucketSize)}-${Math.round((i+1)*bucketSize)}h: ${b} branches"></div>`;
    }).join('');
    const step = Math.max(1, Math.round(maxV / 4));
    histLabels.innerHTML = `<span>0h</span><span>${step}h</span><span>${step*2}h</span><span>${step*3}h</span><span>${maxV}h</span>`;
  } else {
    histDiv.innerHTML = '<p style="padding:16px;color:var(--text-secondary);font-size:12px;">Insufficient data for histogram.</p>';
    histLabels.innerHTML = '';
  }

  // PR merge chart
  const pr = DATA.pr || {}, mm = pr.merge_methods || {};
  const total = Math.max(1, (mm.merge || 0) + (mm.squash || 0) + (mm.rebase || 0));
  document.getElementById('pr-merge-chart').innerHTML = `
    <div class="pr-merge-bar-wrap"><div class="pr-merge-bar merge" style="height:${(mm.merge||0)/total*100}%"></div><div class="pr-merge-value">${mm.merge||0}</div><div class="pr-merge-label">Merge</div></div>
    <div class="pr-merge-bar-wrap"><div class="pr-merge-bar squash" style="height:${(mm.squash||0)/total*100}%"></div><div class="pr-merge-value">${mm.squash||0}</div><div class="pr-merge-label">Squash</div></div>
    <div class="pr-merge-bar-wrap"><div class="pr-merge-bar rebase" style="height:${(mm.rebase||0)/total*100}%"></div><div class="pr-merge-value">${mm.rebase||0}</div><div class="pr-merge-label">Rebase</div></div>`;
}

// DORA details toggle
let doraDetailsOpen = false;

// ── OVERVIEW: Pulse Grid ────────────────────────────────────────────
function renderPulseGrid() {
  const pu = DATA.pu || {}, ws = pu.ws || {};
  const weeks = Object.keys(ws).sort();
  const grid = document.getElementById('pulse-week-grid');
  if (!weeks.length) {
    grid.innerHTML = '<p style="padding:16px;color:var(--text-secondary);">No pulse data available.</p>';
    return;
  }
  grid.innerHTML = weeks.slice(-6).reverse().map(w => {
    const d = ws[w] || {};
    return `<div class="pulse-week-cell">
      <div class="pw-date">${w.replace('W',' Week ')}</div>
      <div class="pw-commits">${d.commits || 0}</div>
      <div class="pw-meta">${d.branches || 0} branches &middot; ${d.authors || 0} authors</div>
    </div>`;
  }).join('');
}

// ── OVERVIEW: Delivery Pipeline ─────────────────────────────────────
let activePipelineStage = null;

function renderDeliveryPipeline() {
  const localBranches = (DATA.branches || []).filter(b =>
    b.k === 'local' && !['main', 'master', 'develop', 'dev'].includes(b.n)
  );
  const excludeMain = b => !['main', 'master', 'develop', 'dev'].includes(b.n);

  // Classify branches by git status
  const active = [];   // healthy, not merged, recently active (<7d)
  const stale = [];    // aging (>7d inactive)
  const review = [];   // healthy, not merged, but older (likely in review)
  const merged = [];   // merged but not deleted

  DATA.health.forEach(h => {
    if (!excludeMain(h.n)) return;
    const branch = DATA.branches.find(b => b.n === h.n);
    if (!branch) return;

    if (h.mg) { merged.push({...h, kind: branch.k}); }
    else if (h.st === 'zombie_abandoned') { stale.push({...h, kind: branch.k}); }
    else if (h.st === 'aging') { stale.push({...h, kind: branch.k}); }
    else if (h.ds > 3) { review.push({...h, kind: branch.k}); }  // healthy but not touched >3 days
    else { active.push({...h, kind: branch.k}); }
  });

  const stages = [
    { id: 'active', label: 'Active', count: active.length, items: active, color: 'var(--healthy)' },
    { id: 'stale', label: 'Stale', count: stale.length, items: stale, color: 'var(--aging)' },
    { id: 'review', label: 'In Review', count: review.length, items: review, color: 'var(--text-link)' },
    { id: 'merged', label: 'Merged', count: merged.length, items: merged, color: 'var(--zombie-merged)' },
  ];

  document.getElementById('delivery-pipeline').innerHTML = stages.map((s, i) =>
    `<div class="pipeline-stage" data-stage="${s.id}" onclick="togglePipelineStage('${s.id}')" style="background:var(--bg-secondary);">
      <div class="ps-count" style="color:${s.color}">${s.count}</div>
      <div class="ps-label">${s.label}</div>
      ${i < stages.length - 1 ? '<span class="ps-arrow">→</span>' : ''}
    </div>`
  ).join('');

  if (activePipelineStage) {
    const detail = document.getElementById('pipeline-detail');
    detail.classList.add('open');
    showPipelineDetail(activePipelineStage);
  }
}

function togglePipelineStage(stageId) {
  const detail = document.getElementById('pipeline-detail');
  if (activePipelineStage === stageId) {
    detail.classList.remove('open');
    activePipelineStage = null;
  } else {
    activePipelineStage = stageId;
    showPipelineDetail(stageId);
    detail.classList.add('open');
  }
}

function showPipelineDetail(stageId) {
  const stages = {
    active: [], stale: [], review: [], merged: []
  };
  const excludeMain = b => !['main', 'master', 'develop', 'dev'].includes(b.n);

  DATA.health.forEach(h => {
    if (!excludeMain(h.n)) return;
    const branch = DATA.branches.find(b => b.n === h.n);
    if (!branch) return;
    if (h.mg) stages.merged.push({...h, kind: branch.k});
    else if (h.st === 'zombie_abandoned') stages.stale.push({...h, kind: branch.k});
    else if (h.st === 'aging') stages.stale.push({...h, kind: branch.k});
    else if (h.ds > 3) stages.review.push({...h, kind: branch.k});
    else stages.active.push({...h, kind: branch.k});
  });

  const items = stages[stageId] || [];
  const detail = document.getElementById('pipeline-detail');
  if (!items.length) {
    detail.innerHTML = '<p style="padding:12px;color:var(--text-secondary);">No branches in this stage.</p>';
    return;
  }
  detail.innerHTML = items.map(h => `
    <div class="pd-item" onclick="switchTab('graph');setTimeout(function(){toggleBranchHighlight('${escHtml(h.n)}')},200)">
      ${statusDot(h.st)} <span class="pd-name">${escHtml(h.n)}</span>
      <span class="pd-meta">${h.cc || 0} commits &middot; ${daysAgo(h.ld)} &middot; ${h.ac || 0} authors</span>
    </div>`).join('');
}

// ── OVERVIEW: Risk Banner ───────────────────────────────────────────
function renderRiskBanner() {
  const rb = (DATA.pu && DATA.pu.rb) || [];
  const section = document.getElementById('risk-section');
  const banner = document.getElementById('risk-banner');
  if (!rb.length) { section.style.display = 'none'; return; }
  section.style.display = '';
  banner.innerHTML = rb.slice(0, 8).map(r => {
    const sevEmoji = r.severity === 'high' ? '&#x1F534;' : r.severity === 'medium' ? '&#x1F7E0;' : '&#x1F7E1;';
    return `<div class="risk-item ${r.severity}">
      <span class="risk-sev">${sevEmoji}</span>
      <b>${escHtml(r.n)}</b>: ${escHtml(r.reason)}
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════════════════════════
// GRAPH: DAG (existing code, preserved)
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
    const lane = commit.l;
    const lx = cx(lane) + 10;
    const off = labelOffsets[lane] || 0;
    const ly = cy(commit.r) + off * 14 - 3;
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
    labelOffsets[lane] = (labelOffsets[lane] || 0) + 1;
  });

  fitToScreen();
}

function toggleBranchHighlight(name) {
  const wasSelected = highlightedBranch === name;
  highlightedBranch = wasSelected ? null : name;
  applyHighlight();
  updateLegendSelection();
  if (!wasSelected && highlightedBranch) { panToBranch(highlightedBranch); }
}

function panToBranch(branchName) {
  const branch = DATA.branches.find(b => b.n === branchName);
  if (!branch) return;
  const tipCommit = commitMap[branch.h];
  if (!tipCommit) return;
  const targetX = cx(tipCommit.l), targetY = cy(tipCommit.r);
  const container = document.getElementById('graph-container');
  const viewW = container.clientWidth, viewH = container.clientHeight;
  const targetPanX = -(targetX * scale) + viewW / 2;
  const targetPanY = -(targetY * scale) + viewH / 3;
  const startPanX = panX, startPanY = panY;
  const startTime = performance.now();
  const duration = 300;
  function easeInOutCubic(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function animate(now) {
    const elapsed = now - startTime;
    const t = Math.min(1, elapsed / duration);
    const eased = easeInOutCubic(t);
    panX = startPanX + (targetPanX - startPanX) * eased;
    panY = startPanY + (targetPanY - startPanY) * eased;
    applyTransform();
    if (t < 1) requestAnimationFrame(animate); else updateMinimap();
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
  circles.forEach(c => { c.classList.toggle('dimmed', !branchCommits.has(c.getAttribute('data-hash'))); });
  labels.forEach(l => { l.classList.toggle('dimmed', l.getAttribute('data-branch') !== highlightedBranch); });
  edges.forEach(e => {
    const from = e.getAttribute('data-from'), to = e.getAttribute('data-to');
    e.classList.toggle('dimmed', !branchCommits.has(from) && !branchCommits.has(to));
  });
}

function buildLegend() {
  const list = document.getElementById('legend-list');
  DATA.branches.forEach(b => {
    const h = healthLookup[b.n];
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

function updateMinimap() {
  const ms = document.getElementById('minimap-svg');
  const mw = 180, mh = 120;
  ms.setAttribute('viewBox', `0 0 ${mw} ${mh}`);
  ms.setAttribute('width', mw); ms.setAttribute('height', mh);
  ms.innerHTML = '';
  const scaleX = mw / (MARGIN_L + (DATA.metadata.total_lanes + 1) * LANE_W + 100);
  const scaleY = mh / (MARGIN_T + (DATA.metadata.total_rows + 1) * ROW_H + 60);
  const s = Math.min(scaleX, scaleY);
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
  const container = document.getElementById('graph-container');
  const vr = document.createElementNS('http://www.w3.org/2000/svg','rect');
  vr.setAttribute('x', -panX / scale * s);
  vr.setAttribute('y', -panY / scale * s);
  vr.setAttribute('width', container.clientWidth / scale * s);
  vr.setAttribute('height', container.clientHeight / scale * s);
  vr.setAttribute('class', 'viewport-rect');
  ms.appendChild(vr);
}

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
  loadChangedFiles(c.h);
}

function hideDetail() { document.getElementById('detail-panel').classList.remove('visible'); }

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
  if (existing && existing.classList.contains('diff-viewer')) { existing.remove(); return; }
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

let tooltipCommit = null;
function showTooltip(ev, c) {
  tooltipCommit = c;
  const tt = document.getElementById('tooltip');
  let html = `<div class="tt-hash">${c.h}</div>`;
  html += `<div class="tt-subject">${escHtml(c.s)}</div>`;
  html += `<div class="tt-meta">${escHtml(c.a)} &middot; ${fmtDate(c.t)}</div>`;
  if (c.b && c.b.length > 0) {
    html += `<div class="tt-branches">${c.b.map(bn => {
      const h = healthLookup[bn]; const st = h ? h.st : 'healthy';
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
    if (cm.h.toLowerCase().includes(q) || cm.s.toLowerCase().includes(q) || cm.a.toLowerCase().includes(q)) searchMatches.push(c);
    else c.classList.add('dimmed');
  });
  document.getElementById('match-count').textContent = searchMatches.length ? `${searchMatches.length} matches` : 'No matches';
}

// ═══════════════════════════════════════════════════════════════════
// GRAPH: Timeline sub-view
// ═══════════════════════════════════════════════════════════════════
function renderTimeline() {
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

  const plotW = W - leftPad - rightPad;
  const dMin = new Date(tl.date_min), dMax = new Date(tl.date_max);
  const totalMs = dMax - dMin;
  let cursor = new Date(dMin.getFullYear(), dMin.getMonth(), 1);
  while (cursor <= dMax) {
    const m = new Date(cursor);
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
    cursor.setMonth(cursor.getMonth() + 1);
  }

  branches.forEach((b, i) => {
    const y = topPad + i * rowH;
    const sx = leftPad + b.sx * plotW;
    const ex = leftPad + b.ex * plotW;

    const nameLbl = document.createElementNS('http://www.w3.org/2000/svg','text');
    nameLbl.setAttribute('x', leftPad - 6); nameLbl.setAttribute('y', y + 5);
    nameLbl.setAttribute('text-anchor', 'end');
    nameLbl.setAttribute('fill', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    nameLbl.setAttribute('font-size','10'); nameLbl.setAttribute('font-family','var(--font-mono)');
    nameLbl.textContent = b.n;
    nameLbl.style.cursor = 'pointer';
    nameLbl.addEventListener('click', () => {
      switchTab('graph');
      setTimeout(() => toggleBranchHighlight(b.n), 200);
    });
    g.appendChild(nameLbl);

    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1', sx); line.setAttribute('x2', ex);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    line.setAttribute('stroke', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    line.setAttribute('stroke-width', '2'); line.setAttribute('stroke-linecap','round');
    if (b.mg) line.setAttribute('stroke-dasharray', '6 3');
    line.setAttribute('opacity', '0.6');
    g.appendChild(line);

    const sDot = document.createElementNS('http://www.w3.org/2000/svg','circle');
    sDot.setAttribute('cx', sx); sDot.setAttribute('cy', y);
    sDot.setAttribute('r', b.pb ? 4 : 5);
    sDot.setAttribute('fill', b.pb ? 'var(--bg-primary)' : b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':'var(--zombie-merged)');
    sDot.setAttribute('stroke', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    sDot.setAttribute('stroke-width', '2');
    sDot.setAttribute('data-hash', b.sh);
    g.appendChild(sDot);

    const eDot = document.createElementNS('http://www.w3.org/2000/svg','circle');
    eDot.setAttribute('cx', ex); eDot.setAttribute('cy', y);
    eDot.setAttribute('r', 5);
    eDot.setAttribute('fill', b.st==='healthy'?'var(--healthy)':b.st==='aging'?'var(--aging)':b.st.includes('zombie')?'var(--zombie-merged)':'var(--merged-stale)');
    eDot.setAttribute('data-hash', b.eh);
    g.appendChild(eDot);

    if (b.pb) {
      const pBranch = branches.find(br => br.n === b.pb);
      if (pBranch) {
        const py = topPad + pBranch.row * rowH;
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
// GRAPH: Lifecycle sub-view
// ═══════════════════════════════════════════════════════════════════
function renderLifecycle() {
  const bl = DATA.branch_lifetimes || [];
  const container = document.getElementById('lifetime-bars');
  if (!bl.length) { container.innerHTML = '<p style="color:var(--text-secondary);padding:12px;">No branch lifetime data.</p>'; return; }
  const sorted = [...bl].filter(b => b.n && !['main','master','develop','dev'].includes(b.n)).sort((a,b) => (a.d || 0) - (b.d || 0));
  const maxD = Math.max(...sorted.map(b => b.d || 0), 1);
  container.innerHTML = sorted.map(b =>
    `<div class="lifetime-row">
      <span class="lname" onclick="switchTab('graph');setTimeout(function(){toggleBranchHighlight('${escHtml(b.n)}')},200);">${escHtml(b.n)}</span>
      <div class="lbar-wrap"><div class="lbar ${b.st||'healthy'}" style="width:${(b.d||0)/maxD*100}%"></div></div>
      <span class="ldur">${b.d||0}d</span>
    </div>`
  ).join('');
}

// ═══════════════════════════════════════════════════════════════════
// INSIGHTS: Authors
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
// INSIGHTS: Topology (Branch Relationships)
// ═══════════════════════════════════════════════════════════════════
let topoUpstream = {}, topoDownstream = {};
let topoNodes = [], topoEdges = [];

function renderTopology() {
  const dg = DATA.dg || {};
  topoNodes = dg.ns || [];
  topoEdges = dg.es || [];

  if (!topoNodes.length) {
    document.getElementById('topo-container').innerHTML = '<p style="padding:24px;color:var(--text-secondary);">No branch relationship data available. This requires at least one fork/merge relationship in the repo.</p>';
    document.getElementById('topo-info').innerHTML = 'No topology data.';
    return;
  }

  // Precompute upstream/downstream for O(1) hover
  topoUpstream = {};
  topoDownstream = {};
  topoEdges.forEach(e => {
    (topoUpstream[e.to] = topoUpstream[e.to] || []).push(e.f);
    (topoDownstream[e.f] = topoDownstream[e.f] || []).push(e.to);
  });

  drawTopoGraph(topoNodes, topoEdges);
}

function drawTopoGraph(nodes, edges) {
  const svg = document.getElementById('topo-svg');
  const container = document.getElementById('topo-container');
  const NODE_W = 130, NODE_H = 30, H_GAP = 50, V_GAP = 16, MARGIN = 24;

  // BFS layout
  const children = {}; nodes.forEach(n => { children[n.n] = n.ch || []; });
  const hasParent = new Set(edges.map(e => e.to));
  const roots = nodes.filter(n => !hasParent.has(n.n)).map(n => n.n);
  if (!roots.length) roots.push(nodes[0].n);

  const layers = [], visited = new Set();
  let current = roots;
  while (current.length > 0) {
    layers.push(current);
    const next = [];
    current.forEach(n => { visited.add(n); (children[n] || []).forEach(c => { if (!visited.has(c)) next.push(c); }); });
    current = [...new Set(next)];
  }
  const maxNodes = Math.max(...layers.map(l => l.length), 1);
  const totalW = maxNodes * (NODE_W + H_GAP) + MARGIN * 2;
  const totalH = layers.length * (NODE_H + V_GAP) + MARGIN * 2;
  svg.setAttribute('viewBox', `0 0 ${totalW} ${totalH}`);
  svg.innerHTML = '';

  let svgInner = '<defs><marker id="topo-arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="var(--border)"/></marker></defs>';

  const positions = {};
  const nodeMap = {};
  nodes.forEach(n => { nodeMap[n.n] = n; });

  layers.forEach((layer, li) => {
    const y = MARGIN + li * (NODE_H + V_GAP);
    const layerW = layer.length * (NODE_W + H_GAP);
    const startX = Math.max(MARGIN, (totalW - layerW) / 2);
    layer.forEach((name, ni) => {
      positions[name] = { x: startX + ni * (NODE_W + H_GAP), y };
    });
  });

  // Edges
  edges.forEach(e => {
    if (positions[e.f] && positions[e.to]) {
      const fx = positions[e.f].x + NODE_W / 2, fy = positions[e.f].y + NODE_H;
      const tx = positions[e.to].x + NODE_W / 2, ty = positions[e.to].y;
      svgInner += `<path class="topo-edge" data-from="${escHtml(e.f)}" data-to="${escHtml(e.to)}" d="M${fx},${fy} C${fx},${(fy+ty)/2} ${tx},${(fy+ty)/2} ${tx},${ty}"/>`;
    }
  });

  // Nodes
  nodes.forEach(n => {
    const pos = positions[n.n];
    if (!pos) return;
    const h = healthLookup[n.n] || {};
    const st = h.st || 'healthy';
    const isMain = n.k === 'main' || ['main','master','develop'].includes(n.n);
    svgInner += `<rect class="topo-node ${st}${isMain?' main-branch':''}" data-node="${escHtml(n.n)}" x="${pos.x}" y="${pos.y}" width="${NODE_W}" height="${NODE_H}" rx="6"
      onmouseenter="topoHover('${escHtml(n.n)}')" onmouseleave="topoUnhover()"
      onclick="switchTab('graph');setTimeout(function(){toggleBranchHighlight('${escHtml(n.n)}')},200)"/>`;
    svgInner += `<text class="topo-label" x="${pos.x + NODE_W/2}" y="${pos.y + NODE_H/2 + 4}" text-anchor="middle">${escHtml(n.n)}</text>`;
  });

  svg.innerHTML = svgInner;
  document.getElementById('topo-info').innerHTML = `${nodes.length} branches, ${edges.length} relationships. Hover to explore.`;
}

function getRelated(nodeName) {
  const up = new Set();
  const down = new Set();
  function walkUp(n) { if (topoUpstream[n]) topoUpstream[n].forEach(p => { if (!up.has(p)) { up.add(p); walkUp(p); } }); }
  function walkDown(n) { if (topoDownstream[n]) topoDownstream[n].forEach(c => { if (!down.has(c)) { down.add(c); walkDown(c); } }); }
  walkUp(nodeName);
  walkDown(nodeName);
  return { up, down };
}

function topoHover(nodeName) {
  const related = getRelated(nodeName);
  const svg = document.getElementById('topo-svg');
  svg.querySelectorAll('.topo-node').forEach(n => {
    const name = n.getAttribute('data-node');
    if (name === nodeName) return; // keep focused node
    n.classList.toggle('faded', !related.up.has(name) && !related.down.has(name));
  });
  svg.querySelectorAll('.topo-edge').forEach(e => {
    const from = e.getAttribute('data-from'), to = e.getAttribute('data-to');
    const isRelated = (from === nodeName || to === nodeName || related.up.has(from) || related.down.has(to) || related.up.has(to) || related.down.has(from));
    e.classList.toggle('highlight', isRelated);
    e.classList.toggle('faded', !isRelated);
  });
  document.getElementById('topo-info').innerHTML = `<strong>${escHtml(nodeName)}</strong> &mdash; upstream: ${related.up.size} branches, downstream: ${related.down.size} branches`;
}

function topoUnhover() {
  const svg = document.getElementById('topo-svg');
  svg.querySelectorAll('.topo-node').forEach(n => n.classList.remove('faded'));
  svg.querySelectorAll('.topo-edge').forEach(e => { e.classList.remove('highlight', 'faded'); });
  document.getElementById('topo-info').innerHTML = `${topoNodes.length} branches, ${topoEdges.length} relationships. Hover to explore.`;
}

function filterTopo() {
  const q = (document.getElementById('topo-search')?.value || '').trim().toLowerCase();
  const svg = document.getElementById('topo-svg');
  if (!q) {
    svg.querySelectorAll('.topo-node').forEach(n => n.classList.remove('faded'));
    svg.querySelectorAll('.topo-edge').forEach(e => e.classList.remove('faded'));
    return;
  }
  svg.querySelectorAll('.topo-node').forEach(n => {
    const name = n.getAttribute('data-node') || '';
    n.classList.toggle('faded', !name.toLowerCase().includes(q));
  });
  svg.querySelectorAll('.topo-edge').forEach(e => e.classList.add('faded'));
}

// ═══════════════════════════════════════════════════════════════════
// INSIGHTS: AI Analysis
// ═══════════════════════════════════════════════════════════════════
function renderConflictRisks() {
  const cr = DATA.cr || [];
  document.getElementById('conflict-risks').innerHTML = cr.length ? cr.map(c => {
    const isHigh = c.rs > 0.5;
    return `<div class="conflict-alert ${isHigh ? 'high-risk' : ''}"><div class="conflict-header"><span class="conflict-branches">${escHtml(c.b1)} &#x2194; ${escHtml(c.b2)}</span><span class="conflict-score ${isHigh ? 'risky' : ''}">${(c.rs * 100).toFixed(0)}%</span></div>${c.sf && c.sf.length ? '<div class="conflict-files">Shared: ' + c.sf.map(escHtml).join(', ') + '</div>' : ''}</div>`;
  }).join('') : '<p style="color:var(--text-secondary);padding:8px;">All clear! No active branch pairs with risk.</p>';
}

function renderAISummaries() {
  const bs = DATA.bs || {};
  const items = Object.entries(bs).slice(0, 10);
  document.getElementById('branch-summaries').innerHTML = items.length ? items.map(([name, summary]) => `<div class="conflict-alert" style="border-left-color:var(--text-link);"><div class="conflict-branches">${escHtml(name)}</div><div class="conflict-files" style="margin-top:4px;">${escHtml(summary)}</div></div>`).join('') : '<p style="color:var(--text-secondary);padding:8px;">No branches to summarize.</p>';
  document.getElementById('release-notes').textContent = DATA.rn || 'No release notes available.';
  document.getElementById('copy-rn-btn').onclick = () => navigator.clipboard.writeText(DATA.rn || '').then(() => alert('Release notes copied!')).catch(() => {});
}

function processNLQuery(text) {
  const lower = text.toLowerCase().trim(), res = document.getElementById('nl-results');
  if (lower.includes('who commit') || lower.includes('most commit') || lower.includes('top author')) {
    res.innerHTML = '<b>Top Authors:</b><br>' + (DATA.author_stats || []).slice(0, 5).map(a => `${escHtml(a.n)}: ${a.cc} commits (${a.pc}%)`).join('<br>');
  } else if (lower.includes('branch') && (lower.includes('not updated') || lower.includes('inactive') || lower.includes('stale'))) {
    const stale = (DATA.health || []).filter(h => h.ds > 14 && !['main', 'master', 'develop'].includes(h.n));
    res.innerHTML = `<b>${stale.length} inactive branches (>14 days):</b><br>` + stale.map(h => `${escHtml(h.n)}: ${h.ds} days`).join('<br>');
  } else if (lower.includes('conflict')) { swInsight('ai'); }
  else if (lower.includes('safe to delete') || lower.includes('cleanup')) { swInsight('cleanup'); }
  else if (lower.includes('hotspot') || lower.includes('churn') || lower.includes('dora') || lower.includes('deploy')) { switchTab('overview'); }
  else if (lower.includes('release note')) { swInsight('ai'); }
  else if (lower.includes('depend') || lower.includes('topology')) { swInsight('topology'); }
  else { res.innerHTML = '<b>Try:</b><br>&bull; "who committed most"<br>&bull; "branches not updated"<br>&bull; "conflict risk"<br>&bull; "safe to delete"<br>&bull; "hotspot files"<br>&bull; "DORA metrics"<br>&bull; "release notes"'; }
}

function swInsight(name) { switchTab('insights'); setTimeout(() => switchInsight(name), 50); }

// ═══════════════════════════════════════════════════════════════════
// INSIGHTS: Cleanup
// ═══════════════════════════════════════════════════════════════════
function renderCleanupSuggestions() {
  const cl = DATA.cl || [];
  if (!cl.length) {
    document.getElementById('cleanup-list').innerHTML = '<p style="padding:12px;color:var(--text-secondary);">All good. No cleanup needed.</p>';
    return;
  }
  const safe = cl.filter(c => c.safe);
  const needsReview = cl.filter(c => !c.safe);
  let html = '';
  if (safe.length) {
    html += `<div class="cleanup-category"><div class="cc-header">&#x2705; Safe to Delete <span class="cc-count">${safe.length}</span></div>`;
    html += safe.map(c => `<div class="cleanup-row"><span class="safe-dot safe"></span><span class="cl-name">${escHtml(c.n)}</span><span class="cl-reason">${escHtml(c.reason)}</span><span class="cl-cmd" onclick="event.stopPropagation();navigator.clipboard.writeText('${c.cmd.replace(/'/g,"\\'")}')" title="Click to copy">${escHtml(c.cmd)}</span></div>`).join('');
    html += '</div>';
  }
  if (needsReview.length) {
    html += `<div class="cleanup-category"><div class="cc-header">&#x26A0;&#xFE0F; Needs Review <span class="cc-count">${needsReview.length}</span></div>`;
    html += needsReview.map(c => `<div class="cleanup-row"><span class="safe-dot warn"></span><span class="cl-name">${escHtml(c.n)}</span><span class="cl-reason">${escHtml(c.reason)}</span><span class="cl-cmd" onclick="event.stopPropagation();navigator.clipboard.writeText('${c.cmd.replace(/'/g,"\\'")}')" title="Click to copy">${escHtml(c.cmd)}</span></div>`).join('');
    html += '</div>';
  }
  html += `<button class="btn-cleanup-all" onclick="copyAllCleanup()">Copy All Safe Deletions (${safe.length})</button>`;
  document.getElementById('cleanup-list').innerHTML = html;
}

function copyAllCleanup() {
  const cmds = (DATA.cl || []).filter(c => c.safe).map(c => c.cmd).join('\n');
  if (cmds) navigator.clipboard.writeText(cmds).then(() => alert('Copied!')).catch(() => {});
}

function highlightBranch(name) { if (typeof toggleBranchHighlight === 'function') toggleBranchHighlight(name); }

function renderComparison() {
  const mc = DATA.mc || [];
  if (!mc.length) return;
  document.getElementById('compare-tab-btn').style.display = '';
  document.getElementById('compare-grid').innerHTML = mc.map(r => {
    const dr = r.dr || {};
    return `<div class="compare-card"><h3>${escHtml(r.n)}</h3><div class="cm-row"><span class="cmlabel">Commits</span><span class="cmvalue">${r.tc}</span></div><div class="cm-row"><span class="cmlabel">Branches</span><span class="cmvalue">${r.tb}</span></div><div class="cm-row"><span class="cmlabel">Health</span><span class="cmvalue">${r.hs}/100</span></div><div class="cm-row"><span class="cmlabel">Authors</span><span class="cmvalue">${r.aa}</span></div><div class="cm-row"><span class="cmlabel">Deploy Freq</span><span class="cmvalue">${dr.df || 0}/wk</span></div><div class="cm-row"><span class="cmlabel">Lead Time</span><span class="cmvalue">${dr.lt ? dr.lt.med : 0}h</span></div></div>`;
  }).join('');
}

function initLiveReload() {
  if (typeof isServerMode === 'undefined' || !isServerMode) return;
  try {
    const es = new EventSource('/api/watch');
    es.onmessage = (event) => {
      try { if (JSON.parse(event.data).type === 'refs_changed') { const el = document.getElementById('live-notify'); el.style.display = 'block'; el.onclick = () => location.reload(); } } catch (e) {}
    };
    es.onerror = () => { es.close(); };
  } catch (e) {}
}

// ═══════════════════════════════════════════════════════════════════
// EVENT WIRING
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  renderHealthGauge();
  renderDORAOverview();
  renderPulseGrid();
  renderDeliveryPipeline();
  renderRiskBanner();
  buildLegend();
  renderGraph();
  renderTimeline();
  renderLifecycle();
  renderAuthors();
  renderConflictRisks();
  renderAISummaries();
  renderCleanupSuggestions();
  initLiveReload();

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

  // DORA details toggle
  document.getElementById('dora-details-toggle').addEventListener('click', () => {
    doraDetailsOpen = !doraDetailsOpen;
    const details = document.getElementById('dora-details');
    const btn = document.getElementById('dora-details-toggle');
    if (doraDetailsOpen) {
      details.classList.add('open');
      btn.textContent = 'Hide Details';
    } else {
      details.classList.remove('open');
      btn.textContent = 'View Details';
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
      if (document.getElementById('palette-overlay').classList.contains('open')) { CommandPalette.close(); return; }
      if (document.getElementById('shortcuts-modal').classList.contains('open')) { document.getElementById('shortcuts-modal').classList.remove('open'); return; }
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
    const s = Math.min(180 / (MARGIN_L + (DATA.metadata.total_lanes+1)*LANE_W+100), 120 / (MARGIN_T + (DATA.metadata.total_rows+1)*ROW_H+60));
    const container = document.getElementById('graph-container');
    panX = -(mx / s) + container.clientWidth / 2 / scale;
    panY = -(my / s) + container.clientHeight / 2 / scale;
    applyTransform();
    updateMinimap();
  });

  // ── Command Palette + Keyboard Shortcuts ─────────
  document.addEventListener('keydown', function(e) {
    var ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && e.key === 'k') { e.preventDefault(); CommandPalette.open(); return; }
    if (e.key === 'Escape') {
      if (document.getElementById('palette-overlay').classList.contains('open')) { CommandPalette.close(); return; }
      if (document.getElementById('shortcuts-modal').classList.contains('open')) { document.getElementById('shortcuts-modal').classList.remove('open'); return; }
    }
    if (document.getElementById('palette-overlay').classList.contains('open')) {
      if (e.key === 'ArrowDown') { e.preventDefault(); CommandPalette.navigate(1); return; }
      if (e.key === 'ArrowUp') { e.preventDefault(); CommandPalette.navigate(-1); return; }
      if (e.key === 'Enter') { e.preventDefault(); CommandPalette.execute(CommandPalette._selectedIndex); return; }
    }
    if (!ctrl && !e.target.closest('input') && !e.target.closest('textarea') && !e.target.closest('[contenteditable]')) {
      var tabs = ['overview', 'graph', 'insights'];
      var num = parseInt(e.key);
      if (num >= 1 && num <= tabs.length) { e.preventDefault(); switchTab(tabs[num - 1]); return; }
      // g-key shortcuts
      if (e.key === 'o' && window._gKeyPressed) { e.preventDefault(); switchTab('overview'); window._gKeyPressed = false; return; }
      if (e.key === 'g' && window._gKeyPressed) { e.preventDefault(); switchTab('graph'); window._gKeyPressed = false; return; }
      if (e.key === 't' && window._gKeyPressed) { e.preventDefault(); switchTab('graph'); switchGraphSub('timeline'); window._gKeyPressed = false; return; }
      if (e.key === 'a' && window._gKeyPressed) { e.preventDefault(); switchTab('insights'); switchInsight('authors'); window._gKeyPressed = false; return; }
      if (e.key === 'i' && window._gKeyPressed) { e.preventDefault(); switchTab('insights'); switchInsight('ai'); window._gKeyPressed = false; return; }
      if (e.key === 'g') { window._gKeyPressed = true; setTimeout(() => { window._gKeyPressed = false; }, 800); return; }
    }
    if (!ctrl && e.key === '?' && !e.target.closest('input')) { e.preventDefault(); document.getElementById('shortcuts-modal').classList.add('open'); }
    if (e.key === '/' && !e.target.closest('input') && !e.target.closest('textarea')) { e.preventDefault(); switchTab('graph'); setTimeout(function() { var si = document.getElementById('graph-search'); if (si) si.focus(); }, 100); }
  });
  document.getElementById('palette-input').addEventListener('input', function(e) { CommandPalette.search(e.target.value); });
  document.getElementById('palette-overlay').addEventListener('click', function(e) { if (e.target === document.getElementById('palette-overlay')) CommandPalette.close(); });
  document.getElementById('shortcuts-modal').addEventListener('click', function(e) { if (e.target === document.getElementById('shortcuts-modal')) document.getElementById('shortcuts-modal').classList.remove('open'); });
  document.getElementById('nl-search-btn').addEventListener('click', function() { processNLQuery(document.getElementById('nl-input').value); });
  document.getElementById('nl-input').addEventListener('keydown', function(e) { if (e.key === 'Enter') processNLQuery(e.target.value); });
});
</script>
</body>
</html>"""
