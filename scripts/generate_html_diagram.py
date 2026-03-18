#!/usr/bin/env python3
"""
Azure Interactive Architecture Diagram Generator
서비스 목록과 연결 관계를 받아 인터랙티브 HTML 다이어그램을 생성한다.
Azure Well-Architected Framework 스타일 다이어그램.

사용법:
  python generate_html_diagram.py \
    --services '[{"id":"svc1","name":"서비스명","type":"타입","sku":"SKU","private":true,"details":["상세1"]}]' \
    --connections '[{"from":"svc1","to":"svc2","label":"연결설명","type":"api"}]' \
    --title "아키텍처 제목" \
    --output "archi_diagram_draft.html"
"""

import argparse
import json
import sys
from datetime import datetime

# Azure 서비스별 아이콘 SVG, 색상
# icon: 48x48 viewBox 기준 SVG path
SERVICE_ICONS = {
    "openai": {
        "icon_svg": '<circle cx="24" cy="24" r="18" fill="#0078D4"/><text x="24" y="30" text-anchor="middle" font-size="18" fill="white" font-weight="700">AI</text>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"
    },
    "ai_foundry": {
        "icon_svg": '<rect x="6" y="10" width="36" height="28" rx="4" fill="#0078D4"/><rect x="12" y="16" width="10" height="8" rx="2" fill="white" opacity="0.9"/><rect x="26" y="16" width="10" height="8" rx="2" fill="white" opacity="0.9"/><rect x="12" y="27" width="24" height="5" rx="2" fill="white" opacity="0.6"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"
    },
    "ai_hub": {
        "icon_svg": '<rect x="6" y="10" width="36" height="28" rx="4" fill="#0078D4"/><circle cx="24" cy="24" r="8" fill="white" opacity="0.9"/><circle cx="24" cy="24" r="4" fill="#0078D4"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"
    },
    "search": {
        "icon_svg": '<circle cx="20" cy="20" r="12" fill="none" stroke="#0078D4" stroke-width="3.5"/><line x1="29" y1="29" x2="40" y2="40" stroke="#0078D4" stroke-width="3.5" stroke-linecap="round"/><circle cx="20" cy="20" r="5" fill="#0078D4" opacity="0.3"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"
    },
    "aml": {
        "icon_svg": '<rect x="6" y="8" width="36" height="32" rx="4" fill="#0078D4"/><path d="M14 32 L20 18 L26 26 L32 14" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"
    },
    "storage": {
        "icon_svg": '<rect x="8" y="8" width="32" height="8" rx="3" fill="#0078D4"/><rect x="8" y="20" width="32" height="8" rx="3" fill="#0078D4" opacity="0.7"/><rect x="8" y="32" width="32" height="8" rx="3" fill="#0078D4" opacity="0.4"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Data"
    },
    "adls": {
        "icon_svg": '<rect x="8" y="8" width="32" height="8" rx="3" fill="#0078D4"/><rect x="8" y="20" width="32" height="8" rx="3" fill="#0078D4" opacity="0.7"/><rect x="8" y="32" width="32" height="8" rx="3" fill="#0078D4" opacity="0.4"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Data"
    },
    "fabric": {
        "icon_svg": '<polygon points="24,6 42,18 42,34 24,46 6,34 6,18" fill="#E8740C" opacity="0.9"/><text x="24" y="30" text-anchor="middle" font-size="14" fill="white" font-weight="700">F</text>',
        "color": "#E8740C", "bg": "#FEF3E8", "category": "Data"
    },
    "synapse": {
        "icon_svg": '<circle cx="24" cy="24" r="18" fill="#0078D4"/><path d="M15 24 L24 15 L33 24 L24 33 Z" fill="white" opacity="0.9"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Data"
    },
    "adf": {
        "icon_svg": '<rect x="6" y="12" width="36" height="24" rx="4" fill="#0078D4"/><path d="M16 24 L28 24 M24 18 L30 24 L24 30" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Data"
    },
    "keyvault": {
        "icon_svg": '<rect x="10" y="6" width="28" height="36" rx="4" fill="#E8A000"/><circle cx="24" cy="22" r="6" fill="white"/><rect x="22" y="26" width="4" height="10" rx="1" fill="white"/>',
        "color": "#E8A000", "bg": "#FEF7E0", "category": "Security"
    },
    "kv": {
        "icon_svg": '<rect x="10" y="6" width="28" height="36" rx="4" fill="#E8A000"/><circle cx="24" cy="22" r="6" fill="white"/><rect x="22" y="26" width="4" height="10" rx="1" fill="white"/>',
        "color": "#E8A000", "bg": "#FEF7E0", "category": "Security"
    },
    "vnet": {
        "icon_svg": '<rect x="6" y="6" width="36" height="36" rx="4" fill="none" stroke="#5C2D91" stroke-width="2.5"/><circle cx="16" cy="18" r="4" fill="#5C2D91"/><circle cx="32" cy="18" r="4" fill="#5C2D91"/><circle cx="24" cy="32" r="4" fill="#5C2D91"/><line x1="16" y1="18" x2="32" y2="18" stroke="#5C2D91" stroke-width="1.5"/><line x1="16" y1="18" x2="24" y2="32" stroke="#5C2D91" stroke-width="1.5"/><line x1="32" y1="18" x2="24" y2="32" stroke="#5C2D91" stroke-width="1.5"/>',
        "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"
    },
    "pe": {
        "icon_svg": '<circle cx="24" cy="24" r="14" fill="none" stroke="#5C2D91" stroke-width="2"/><circle cx="24" cy="24" r="6" fill="#5C2D91"/><line x1="24" y1="10" x2="24" y2="4" stroke="#5C2D91" stroke-width="2"/><line x1="24" y1="38" x2="24" y2="44" stroke="#5C2D91" stroke-width="2"/>',
        "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"
    },
    "nsg": {
        "icon_svg": '<rect x="8" y="8" width="32" height="32" rx="4" fill="#5C2D91"/><path d="M18 20 L24 14 L30 20 M18 28 L24 34 L30 28" stroke="white" stroke-width="2" fill="none"/>',
        "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"
    },
    "acr": {
        "icon_svg": '<rect x="8" y="10" width="32" height="28" rx="4" fill="#0078D4"/><rect x="14" y="16" width="20" height="16" rx="2" fill="white" opacity="0.3"/><text x="24" y="30" text-anchor="middle" font-size="12" fill="white" font-weight="600">ACR</text>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"
    },
    "aks": {
        "icon_svg": '<circle cx="24" cy="24" r="18" fill="#326CE5"/><text x="24" y="30" text-anchor="middle" font-size="16" fill="white" font-weight="700">K</text>',
        "color": "#326CE5", "bg": "#EBF0FC", "category": "Compute"
    },
    "appservice": {
        "icon_svg": '<rect x="8" y="8" width="32" height="32" rx="6" fill="#0078D4"/><polygon points="24,14 34,34 14,34" fill="white" opacity="0.9"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"
    },
    "appinsights": {
        "icon_svg": '<circle cx="24" cy="24" r="16" fill="#773ADC"/><path d="M16 28 L20 20 L24 24 L28 16 L32 22" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>',
        "color": "#773ADC", "bg": "#F0EAFA", "category": "Monitor"
    },
    "monitor": {
        "icon_svg": '<rect x="6" y="10" width="36" height="24" rx="4" fill="#773ADC"/><path d="M14 28 L20 20 L26 24 L34 16" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/><rect x="14" y="36" width="20" height="3" rx="1" fill="#773ADC" opacity="0.5"/>',
        "color": "#773ADC", "bg": "#F0EAFA", "category": "Monitor"
    },
    "vm": {
        "icon_svg": '<rect x="6" y="8" width="36" height="26" rx="3" fill="#0078D4"/><rect x="10" y="12" width="28" height="18" rx="1" fill="white" opacity="0.2"/><rect x="16" y="36" width="16" height="4" rx="1" fill="#0078D4"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"
    },
    "bastion": {
        "icon_svg": '<rect x="8" y="6" width="32" height="36" rx="4" fill="#5C2D91"/><rect x="14" y="12" width="20" height="14" rx="2" fill="white" opacity="0.3"/><circle cx="24" cy="34" r="4" fill="white" opacity="0.7"/>',
        "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"
    },
    "jumpbox": {
        "icon_svg": '<rect x="8" y="8" width="32" height="32" rx="4" fill="#5C2D91"/><text x="24" y="30" text-anchor="middle" font-size="14" fill="white" font-weight="600">JB</text>',
        "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"
    },
    "vpn": {
        "icon_svg": '<rect x="6" y="12" width="36" height="24" rx="4" fill="#5C2D91"/><path d="M16 24 L24 16 L32 24 L24 32 Z" fill="white" opacity="0.8"/>',
        "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"
    },
    "user": {
        "icon_svg": '<circle cx="24" cy="16" r="8" fill="#0078D4"/><path d="M10 42 Q10 30 24 30 Q38 30 38 42" fill="#0078D4"/>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "External"
    },
    "app": {
        "icon_svg": '<rect x="8" y="6" width="32" height="36" rx="6" fill="#666"/><rect x="14" y="12" width="20" height="20" rx="2" fill="white" opacity="0.3"/><circle cx="24" cy="40" r="2" fill="white" opacity="0.7"/>',
        "color": "#666666", "bg": "#F5F5F5", "category": "External"
    },
    "default": {
        "icon_svg": '<circle cx="24" cy="24" r="16" fill="#0078D4"/><text x="24" y="30" text-anchor="middle" font-size="14" fill="white" font-weight="600">?</text>',
        "color": "#0078D4", "bg": "#E8F4FD", "category": "Azure"
    },
}

CONNECTION_STYLES = {
    "api":      {"color": "#0078D4", "dash": "0"},
    "data":     {"color": "#0F9D58", "dash": "0"},
    "security": {"color": "#E8A000", "dash": "5,5"},
    "private":  {"color": "#5C2D91", "dash": "3,3"},
    "network":  {"color": "#5C2D91", "dash": "5,5"},
    "default":  {"color": "#999999", "dash": "0"},
}


def get_service_info(svc_type: str) -> dict:
    t = svc_type.lower().replace("-", "_").replace(" ", "_")
    return SERVICE_ICONS.get(t, SERVICE_ICONS["default"])


def generate_html(services: list, connections: list, title: str) -> str:
    nodes_js = json.dumps([{
        "id": svc["id"],
        "name": svc["name"],
        "type": svc.get("type", "default"),
        "sku": svc.get("sku", ""),
        "private": svc.get("private", True),
        "details": svc.get("details", []),
        "icon_svg": get_service_info(svc.get("type", "default"))["icon_svg"],
        "color": get_service_info(svc.get("type", "default"))["color"],
        "bg": get_service_info(svc.get("type", "default"))["bg"],
        "category": get_service_info(svc.get("type", "default"))["category"],
    } for svc in services], ensure_ascii=False)

    edges_js = json.dumps([{
        "from": conn["from"],
        "to": conn["to"],
        "label": conn.get("label", ""),
        "type": conn.get("type", "default"),
        "color": CONNECTION_STYLES.get(conn.get("type", "default"), CONNECTION_STYLES["default"])["color"],
        "dash": CONNECTION_STYLES.get(conn.get("type", "default"), CONNECTION_STYLES["default"])["dash"],
    } for conn in connections], ensure_ascii=False)

    pe_count = sum(1 for s in services if s.get("type", "default") == "pe")
    svc_count = len(services) - pe_count
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif; background: #f3f2f1; color: #323130; }}

  .header {{
    background: white; border-bottom: 1px solid #edebe9;
    padding: 12px 24px; display: flex; align-items: center; gap: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .header-icon {{
    width: 32px; height: 32px; border-radius: 4px;
    background: linear-gradient(135deg, #0078D4, #00BCF2);
    display: flex; align-items: center; justify-content: center;
  }}
  .header-icon svg {{ width: 20px; height: 20px; }}
  .header h1 {{ font-size: 15px; font-weight: 600; color: #201f1e; }}
  .header .meta {{ font-size: 11px; color: #a19f9d; }}
  .header-right {{ margin-left: auto; display: flex; gap: 16px; align-items: center; }}
  .stat {{ font-size: 11px; color: #605e5c; }}
  .stat b {{ color: #323130; }}

  .container {{ display: flex; height: calc(100vh - 56px); }}

  .canvas-area {{
    flex: 1; position: relative; overflow: hidden;
    background: white;
    background-image:
      linear-gradient(#faf9f8 1px, transparent 1px),
      linear-gradient(90deg, #faf9f8 1px, transparent 1px);
    background-size: 24px 24px;
  }}
  #canvas {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}

  .toolbar {{
    position: absolute; top: 10px; left: 10px;
    display: flex; gap: 1px; z-index: 10;
    background: white; border: 1px solid #edebe9; border-radius: 6px;
    padding: 2px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  .tool-btn {{
    background: transparent; border: none; border-radius: 4px;
    padding: 5px 10px; font-size: 11px; cursor: pointer; color: #605e5c;
    font-family: inherit; transition: all 0.1s;
  }}
  .tool-btn:hover {{ background: #f3f2f1; color: #323130; }}
  .tool-sep {{ width: 1px; background: #edebe9; margin: 3px 1px; }}

  .zoom-indicator {{
    position: absolute; top: 10px; right: 286px;
    background: white; border: 1px solid #edebe9; border-radius: 4px;
    padding: 3px 8px; font-size: 10px; color: #a19f9d; z-index: 10;
  }}

  /* ── Sidebar ── */
  .sidebar {{
    width: 272px; background: #faf9f8; border-left: 1px solid #edebe9;
    overflow-y: auto; display: flex; flex-direction: column;
  }}
  .sidebar::-webkit-scrollbar {{ width: 3px; }}
  .sidebar::-webkit-scrollbar-thumb {{ background: #c8c6c4; border-radius: 3px; }}

  .sidebar-header {{
    padding: 12px 14px; border-bottom: 1px solid #edebe9;
    font-weight: 600; font-size: 12px; color: #605e5c;
    position: sticky; top: 0; background: #faf9f8; z-index: 1;
  }}
  .cat-label {{
    padding: 10px 14px 4px; font-size: 10px; color: #a19f9d;
    font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .service-card {{
    margin: 2px 6px; border: 1px solid #edebe9; border-radius: 6px;
    overflow: hidden; cursor: pointer; transition: all 0.1s;
    background: white;
  }}
  .service-card:hover {{ border-color: #c8c6c4; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .service-card.selected {{ border-color: #0078D4; box-shadow: 0 0 0 1px #0078D4; }}
  .service-card-header {{
    padding: 7px 10px; display: flex; align-items: center; gap: 8px;
  }}
  .sc-icon {{ width: 28px; height: 28px; flex-shrink: 0; }}
  .sc-icon svg {{ width: 28px; height: 28px; }}
  .service-name {{ font-size: 12px; font-weight: 600; color: #323130; }}
  .service-sku {{ font-size: 10px; color: #a19f9d; }}
  .service-card-body {{ padding: 2px 10px 6px; }}
  .service-detail {{ font-size: 10px; color: #605e5c; padding: 1px 0; }}
  .service-detail::before {{ content: "› "; color: #a19f9d; }}
  .private-badge {{
    font-size: 9px; background: #f3eef9; color: #5C2D91;
    border-radius: 3px; padding: 1px 5px; margin-left: auto;
    border: 1px solid #e0d4f5;
  }}

  .legend {{
    padding: 10px 14px; border-top: 1px solid #edebe9; margin-top: auto;
  }}
  .legend-title {{ font-size: 10px; font-weight: 600; color: #a19f9d; margin-bottom: 5px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 10px; color: #605e5c; margin-bottom: 2px; }}
  .legend-line {{ width: 18px; height: 2px; border-radius: 1px; }}
  .legend-line-dash {{ width: 18px; height: 0; border-top: 2px dashed; }}

  /* ── SVG styles ── */
  .node {{ cursor: grab; pointer-events: all; }}
  .node:active {{ cursor: grabbing; }}
  .node .node-bg {{ pointer-events: all; }}
  .node.selected .node-bg {{ stroke: #0078D4; stroke-width: 2.5; }}
  .node.selected {{ filter: drop-shadow(0 0 6px rgba(0,120,212,0.4)); }}

  .subnet-rect {{
    rx: 6; ry: 6;
  }}
  .subnet-label {{
    font-size: 11px; font-weight: 600; font-family: 'Segoe UI', sans-serif;
  }}

  .status-bar {{
    position: absolute; bottom: 10px; left: 10px;
    background: white; border: 1px solid #edebe9; border-radius: 4px;
    padding: 4px 10px; font-size: 10px; color: #a19f9d;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}

  .tooltip {{
    position: absolute; background: white; color: #323130;
    border: 1px solid #edebe9; padding: 8px 12px;
    border-radius: 6px; font-size: 11px; pointer-events: none;
    white-space: nowrap; z-index: 100; display: none;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  }}
  .tooltip strong {{ color: #201f1e; }}
  .tooltip-detail {{ color: #605e5c; margin-top: 1px; font-size: 10px; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">
    <svg viewBox="0 0 24 24"><path d="M12 2L2 7v10l10 5 10-5V7L12 2z" fill="white" opacity="0.9"/></svg>
  </div>
  <div>
    <h1>{title}</h1>
    <div class="meta">Azure Architecture &middot; {generated_at}</div>
  </div>
  <div class="header-right">
    <div class="stat"><b>{svc_count}</b> Services</div>
    <div class="stat"><b>{pe_count}</b> Private Endpoints</div>
    <div class="stat"><b>{len(connections)}</b> Connections</div>
  </div>
</div>

<div class="container">
  <div class="canvas-area">
    <div class="toolbar">
      <button class="tool-btn" onclick="fitToScreen()">Fit</button>
      <div class="tool-sep"></div>
      <button class="tool-btn" onclick="zoomIn()">+</button>
      <button class="tool-btn" onclick="zoomOut()">&minus;</button>
      <div class="tool-sep"></div>
      <button class="tool-btn" onclick="resetZoom()">Reset</button>
    </div>
    <div class="zoom-indicator" id="zoom-level">100%</div>
    <svg id="canvas">
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#0078D4" opacity="0.5"/>
        </marker>
        <marker id="arr-data" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#0F9D58" opacity="0.5"/>
        </marker>
        <marker id="arr-sec" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#E8A000" opacity="0.5"/>
        </marker>
        <marker id="arr-pe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#5C2D91" opacity="0.5"/>
        </marker>
        <filter id="shadow">
          <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.08"/>
        </filter>
      </defs>
      <g id="diagram-root"></g>
    </svg>
    <div id="tooltip" class="tooltip"></div>
    <div class="status-bar">Drag nodes &middot; Scroll to zoom &middot; Drag empty space to pan</div>
  </div>

  <div class="sidebar">
    <div class="sidebar-header">Resources</div>
    <div id="service-list"></div>
    <div class="legend">
      <div class="legend-title">Connection Types</div>
      <div class="legend-item"><div class="legend-line" style="background:#0078D4;"></div> API</div>
      <div class="legend-item"><div class="legend-line" style="background:#0F9D58;"></div> Data</div>
      <div class="legend-item"><div class="legend-line-dash" style="border-color:#E8A000;"></div> Security</div>
      <div class="legend-item"><div class="legend-line-dash" style="border-color:#5C2D91;"></div> Private Endpoint</div>
    </div>
  </div>
</div>

<script>
const NODES = {nodes_js};
const EDGES = {edges_js};

// ── Node sizing ──
const SVC_W = 120, SVC_H = 100;  // service node (icon above, name below)
const PE_W = 90, PE_H = 70;      // pe node (smaller)
const GAP = 40;

// ── Layout: Category Group Box style ──
// Each category gets a labeled box, services arranged in a grid inside.
// Groups arranged in 2D: main service groups on top, bottom groups below.
// PE nodes in a separate PE subnet group.

const positions = {{}};
const peNodes = NODES.filter(n => n.type === 'pe');
const mainNodes = NODES.filter(n => n.type !== 'pe');

// Category grouping
const bottomCategories = ['Network', 'External', 'Monitor'];
const catOrder = ['AI', 'Data', 'Security', 'Compute', 'Azure'];

const catGroups = {{}};
mainNodes.forEach(n => {{
  const cat = n.category || 'Azure';
  if (!catGroups[cat]) catGroups[cat] = [];
  catGroups[cat].push(n);
}});

// Group box layout parameters
const GROUP_PAD = 20;         // padding inside group box
const GROUP_TITLE_H = 28;    // height for group title bar
const GROUP_GAP = 30;        // gap between group boxes
const COLS_PER_GROUP = 3;    // max columns in a group grid
const CELL_W = SVC_W + 16;   // cell width in grid
const CELL_H = SVC_H + 24;   // cell height in grid

// Calculate group box dimensions
function groupDimensions(nodeCount) {{
  const cols = Math.min(nodeCount, COLS_PER_GROUP);
  const rows = Math.ceil(nodeCount / COLS_PER_GROUP);
  const w = cols * CELL_W + GROUP_PAD * 2;
  const h = rows * CELL_H + GROUP_PAD + GROUP_TITLE_H;
  return {{ w, h, cols, rows }};
}}

// Store group box positions for rendering
const groupBoxes = [];

// ── Place main service groups in a flowing grid ──
const serviceGroups = catOrder.filter(cat => catGroups[cat] && catGroups[cat].length > 0
  && !bottomCategories.includes(cat));

let gx = 60, gy = 140;  // starting position for service groups
let rowMaxH = 0;
let rowStartX = 60;
const MAX_ROW_W = Math.max(1200, serviceGroups.length * 300);  // rough max width before wrapping

serviceGroups.forEach(cat => {{
  const nodes = catGroups[cat];
  const dim = groupDimensions(nodes.length);

  // Wrap to next row if too wide
  if (gx + dim.w > rowStartX + MAX_ROW_W && gx > rowStartX) {{
    gx = rowStartX;
    gy += rowMaxH + GROUP_GAP;
    rowMaxH = 0;
  }}

  // Place nodes inside group grid
  nodes.forEach((n, i) => {{
    const col = i % dim.cols;
    const row = Math.floor(i / dim.cols);
    positions[n.id] = {{
      x: gx + GROUP_PAD + col * CELL_W + (CELL_W - SVC_W) / 2,
      y: gy + GROUP_TITLE_H + row * CELL_H + (CELL_H - SVC_H) / 2
    }};
  }});

  groupBoxes.push({{
    cat, x: gx, y: gy, w: dim.w, h: dim.h,
    color: nodes[0]?.color || '#0078D4'
  }});

  gx += dim.w + GROUP_GAP;
  rowMaxH = Math.max(rowMaxH, dim.h);
}});

// ── Place bottom groups (Network, External, Monitor) ──
const bottomGroupY = gy + rowMaxH + GROUP_GAP + 20;
let bgx = 60;
bottomCategories.forEach(cat => {{
  const nodes = catGroups[cat];
  if (!nodes || nodes.length === 0) return;
  const dim = groupDimensions(nodes.length);

  nodes.forEach((n, i) => {{
    const col = i % dim.cols;
    const row = Math.floor(i / dim.cols);
    positions[n.id] = {{
      x: bgx + GROUP_PAD + col * CELL_W + (CELL_W - SVC_W) / 2,
      y: bottomGroupY + GROUP_TITLE_H + row * CELL_H + (CELL_H - SVC_H) / 2
    }};
  }});

  groupBoxes.push({{
    cat, x: bgx, y: bottomGroupY, w: dim.w, h: dim.h,
    color: nodes[0]?.color || '#666',
    isBottom: true
  }});

  bgx += dim.w + GROUP_GAP;
}});

// ── PE nodes: in PE subnet group above service groups ──
const PE_Y = 40;
if (peNodes.length > 0) {{
  const peDim = groupDimensions(peNodes.length);
  // Use wider PE layout (more columns)
  const peCols = Math.min(peNodes.length, 6);
  const peRows = Math.ceil(peNodes.length / peCols);
  const peCellW = PE_W + 16;
  const peCellH = PE_H + 12;
  const peBoxW = peCols * peCellW + GROUP_PAD * 2;
  const peBoxH = peRows * peCellH + GROUP_PAD + GROUP_TITLE_H;

  peNodes.forEach((pe, i) => {{
    const col = i % peCols;
    const row = Math.floor(i / peCols);
    positions[pe.id] = {{
      x: 60 + GROUP_PAD + col * peCellW + (peCellW - PE_W) / 2,
      y: PE_Y + GROUP_TITLE_H + row * peCellH + (peCellH - PE_H) / 2
    }};
  }});

  groupBoxes.push({{
    cat: 'Private Endpoints', x: 60, y: PE_Y, w: peBoxW, h: peBoxH,
    color: '#5C2D91', isPE: true
  }});

  // Shift service groups down if PE group exists
  const peBottom = PE_Y + peBoxH + GROUP_GAP;
  if (peBottom > 140) {{
    const shift = peBottom - 140;
    // Shift all non-PE positions down
    NODES.forEach(n => {{
      if (n.type !== 'pe' && positions[n.id]) {{
        positions[n.id].y += shift;
      }}
    }});
    // Shift group boxes down
    groupBoxes.forEach(gb => {{
      if (!gb.isPE) gb.y += shift;
    }});
  }}
}}

// ── Node → Group mapping (for edge routing) ──
const nodeGroupMap = {{}};
groupBoxes.forEach((gb, idx) => {{
  NODES.forEach(n => {{
    const pos = positions[n.id];
    if (!pos) return;
    const nw = n.type === 'pe' ? PE_W : SVC_W;
    const nh = n.type === 'pe' ? PE_H : SVC_H;
    const ncx = pos.x + nw / 2;
    const ncy = pos.y + nh / 2;
    if (ncx >= gb.x && ncx <= gb.x + gb.w && ncy >= gb.y && ncy <= gb.y + gb.h) {{
      nodeGroupMap[n.id] = idx;
    }}
  }});
}});
// Routing corridor margins (outside all group boxes)
const _rightMarginBase = groupBoxes.length > 0 ? Math.max(...groupBoxes.map(g => g.x + g.w)) + 40 : 800;
const _leftMarginBase = groupBoxes.length > 0 ? Math.min(...groupBoxes.map(g => g.x)) - 40 : -40;

// ── State ──
let dragging = null, dragOffX = 0, dragOffY = 0;
let viewTransform = {{ x: 0, y: 0, scale: 1 }};
let isPanning = false, panSX = 0, panSY = 0, panSTx = 0, panSTy = 0;
let _routeCounter = 0;

// ── Bidirectional highlight ──
function selectNode(nodeId) {{
  // Clear all selections
  document.querySelectorAll('.node').forEach(n => n.classList.remove('selected'));
  document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
  // Highlight diagram node
  const svgNode = document.querySelector(`.node[data-id="${{nodeId}}"]`);
  if (svgNode) svgNode.classList.add('selected');
  // Highlight sidebar card
  const card = document.getElementById('card-' + nodeId);
  if (card) {{ card.classList.add('selected'); card.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }}); }}
}}

function markerFor(type) {{
  if (type === 'data') return 'arr-data';
  if (type === 'security') return 'arr-sec';
  if (type === 'private') return 'arr-pe';
  return 'arr';
}}

function renderDiagram() {{
  const root = document.getElementById('diagram-root');
  root.innerHTML = '';
  _routeCounter = 0;  // reset stagger counter each render

  // ── Draw VNet boundary around non-bottom groups ──
  const privateGroups = groupBoxes.filter(gb => !gb.isBottom);
  if (privateGroups.length > 0) {{
    const hasPrivateNodes = NODES.some(n => n.private && n.type !== 'pe');
    if (hasPrivateNodes) {{
      const vx = Math.min(...privateGroups.map(g => g.x)) - 16;
      const vy = Math.min(...privateGroups.map(g => g.y)) - 36;
      const vRight = Math.max(...privateGroups.map(g => g.x + g.w)) + 16;
      const vBottom = Math.max(...privateGroups.map(g => g.y + g.h)) + 16;

      const vr = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      vr.setAttribute('x', vx); vr.setAttribute('y', vy);
      vr.setAttribute('width', vRight - vx); vr.setAttribute('height', vBottom - vy);
      vr.setAttribute('fill', '#f8f7ff'); vr.setAttribute('stroke', '#5C2D91');
      vr.setAttribute('stroke-width', '2'); vr.setAttribute('stroke-dasharray', '8,4');
      vr.setAttribute('rx', '12');
      root.appendChild(vr);

      const vl = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      vl.innerHTML = `<svg x="${{vx + 10}}" y="${{vy + 6}}" width="20" height="20" viewBox="0 0 48 48">
        <rect x="6" y="6" width="36" height="36" rx="4" fill="none" stroke="#5C2D91" stroke-width="3"/>
        <circle cx="16" cy="18" r="3" fill="#5C2D91"/><circle cx="32" cy="18" r="3" fill="#5C2D91"/><circle cx="24" cy="32" r="3" fill="#5C2D91"/>
      </svg>
      <text x="${{vx + 34}}" y="${{vy + 20}}" font-size="12" font-weight="600" fill="#5C2D91" font-family="Segoe UI, sans-serif">Virtual Network</text>`;
      root.appendChild(vl);
    }}
  }}

  // ── Draw category group boxes ──
  groupBoxes.forEach(gb => {{
    const gr = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    gr.setAttribute('x', gb.x); gr.setAttribute('y', gb.y);
    gr.setAttribute('width', gb.w); gr.setAttribute('height', gb.h);
    gr.setAttribute('rx', '8');
    gr.setAttribute('fill', gb.isPE ? '#f3eef9' : 'white');
    gr.setAttribute('stroke', gb.isPE ? '#d4b8ff' : '#e1dfdd');
    gr.setAttribute('stroke-width', '1');
    if (gb.isPE) gr.setAttribute('stroke-dasharray', '4,4');
    root.appendChild(gr);

    // Title bar
    const titleBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    titleBar.setAttribute('x', gb.x); titleBar.setAttribute('y', gb.y);
    titleBar.setAttribute('width', gb.w); titleBar.setAttribute('height', GROUP_TITLE_H);
    titleBar.setAttribute('rx', '8');
    titleBar.setAttribute('fill', gb.color);
    titleBar.setAttribute('opacity', '0.1');
    root.appendChild(titleBar);
    // Bottom corners of title bar (square)
    const titleFill = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    titleFill.setAttribute('x', gb.x); titleFill.setAttribute('y', gb.y + GROUP_TITLE_H - 8);
    titleFill.setAttribute('width', gb.w); titleFill.setAttribute('height', '8');
    titleFill.setAttribute('fill', gb.color); titleFill.setAttribute('opacity', '0.1');
    root.appendChild(titleFill);

    // Color accent line
    const accent = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    accent.setAttribute('x', gb.x); accent.setAttribute('y', gb.y);
    accent.setAttribute('width', gb.w); accent.setAttribute('height', '3');
    accent.setAttribute('rx', '8'); accent.setAttribute('fill', gb.color);
    root.appendChild(accent);

    // Group label
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', gb.x + 12); label.setAttribute('y', gb.y + 18);
    label.setAttribute('font-size', '11'); label.setAttribute('font-weight', '600');
    label.setAttribute('fill', gb.color); label.setAttribute('font-family', 'Segoe UI, sans-serif');
    label.textContent = gb.cat;
    root.appendChild(label);
  }});

  // ── Edge routing (obstacle-free) ──
  // Compute global bounds: the absolute bottom of ALL nodes
  function getGlobalBounds() {{
    let minY = Infinity, maxY = -Infinity;
    NODES.forEach(n => {{
      const pos = positions[n.id];
      if (!pos) return;
      const h = n.type === 'pe' ? PE_H : SVC_H;
      if (pos.y < minY) minY = pos.y;
      if (pos.y + h > maxY) maxY = pos.y + h;
    }});
    return {{ minY, maxY }};
  }}

  function getNodeBox(node) {{
    const pos = positions[node.id];
    if (!pos) return null;
    const w = node.type === 'pe' ? PE_W : SVC_W;
    const h = node.type === 'pe' ? PE_H : SVC_H;
    return {{ x: pos.x, y: pos.y, w, h, cx: pos.x + w/2, cy: pos.y + h/2 }};
  }}

  // Check if direct line between two nodes crosses ANY other node
  function hasObstacle(fromId, toId, x1, y1, x2, y2) {{
    for (const n of NODES) {{
      if (n.id === fromId || n.id === toId) continue;
      const pos = positions[n.id];
      if (!pos) continue;
      const w = n.type === 'pe' ? PE_W : SVC_W;
      const h = n.type === 'pe' ? PE_H : SVC_H;
      const pad = 6;
      const left = pos.x - pad, right = pos.x + w + pad;
      const top = pos.y - pad, bottom = pos.y + h + pad;
      // Liang-Barsky line clipping
      const dx = x2 - x1, dy = y2 - y1;
      let tmin = 0, tmax = 1;
      const edges = [[-dx, x1 - left], [dx, right - x1], [-dy, y1 - top], [dy, bottom - y1]];
      let hit = true;
      for (const [p, q] of edges) {{
        if (Math.abs(p) < 0.001) {{ if (q < 0) {{ hit = false; break; }} }}
        else {{
          const t = q / p;
          if (p < 0) {{ if (t > tmin) tmin = t; }}
          else {{ if (t < tmax) tmax = t; }}
          if (tmin > tmax) {{ hit = false; break; }}
        }}
      }}
      if (hit && tmin < tmax) return true;
    }}
    return false;
  }}

  // Border point: exit/enter at edge of rectangle
  function borderExit(box, side) {{
    // side: 'top', 'bottom', 'left', 'right'
    if (side === 'top') return {{ x: box.cx, y: box.y }};
    if (side === 'bottom') return {{ x: box.cx, y: box.y + box.h }};
    if (side === 'left') return {{ x: box.x, y: box.cy }};
    if (side === 'right') return {{ x: box.x + box.w, y: box.cy }};
  }}

  // Check if a line segment hits any group box (for edge routing)
  function hitsGroupBox(x1, y1, x2, y2, skipGroupIndices) {{
    for (let gi = 0; gi < groupBoxes.length; gi++) {{
      if (skipGroupIndices.includes(gi)) continue;
      const gb = groupBoxes[gi];
      const pad = 4;
      const left = gb.x - pad, right = gb.x + gb.w + pad;
      const top = gb.y - pad, bottom = gb.y + gb.h + pad;
      const dx = x2 - x1, dy = y2 - y1;
      let tmin = 0, tmax = 1;
      const edges = [[-dx, x1 - left], [dx, right - x1], [-dy, y1 - top], [dy, bottom - y1]];
      let hit = true;
      for (const [p, q] of edges) {{
        if (Math.abs(p) < 0.001) {{ if (q < 0) {{ hit = false; break; }} }}
        else {{
          const t = q / p;
          if (p < 0) {{ if (t > tmin) tmin = t; }}
          else {{ if (t < tmax) tmax = t; }}
          if (tmin > tmax) {{ hit = false; break; }}
        }}
      }}
      if (hit && tmin < tmax) return true;
    }}
    return false;
  }}

  // Find gap between adjacent groups (same row)
  function findGapBetween(gi1, gi2) {{
    if (gi1 < 0 || gi2 < 0) return null;
    const g1 = groupBoxes[gi1], g2 = groupBoxes[gi2];
    // Same row: Y ranges overlap
    const yOverlap = g1.y < g2.y + g2.h && g2.y < g1.y + g1.h;
    if (!yOverlap) return null;
    // Gap between them
    if (g1.x + g1.w < g2.x) return {{ x: (g1.x + g1.w + g2.x) / 2 }};
    if (g2.x + g2.w < g1.x) return {{ x: (g2.x + g2.w + g1.x) / 2 }};
    return null;
  }}

  // Build orthogonal path with rounded corners
  function buildOrthoPath(pts) {{
    let d = `M ${{pts[0].x}} ${{pts[0].y}}`;
    const radius = 6;
    for (let i = 1; i < pts.length - 1; i++) {{
      const prev = pts[i-1], curr = pts[i], next = pts[i+1];
      const dx1 = curr.x - prev.x, dy1 = curr.y - prev.y;
      const dx2 = next.x - curr.x, dy2 = next.y - curr.y;
      const len1 = Math.sqrt(dx1*dx1 + dy1*dy1);
      const len2 = Math.sqrt(dx2*dx2 + dy2*dy2);
      if (len1 < 1 || len2 < 1) {{ d += ` L ${{curr.x}} ${{curr.y}}`; continue; }}
      const r = Math.min(radius, len1/2, len2/2);
      const bx = curr.x - (dx1/len1)*r, by = curr.y - (dy1/len1)*r;
      const ax = curr.x + (dx2/len2)*r, ay = curr.y + (dy2/len2)*r;
      d += ` L ${{bx}} ${{by}} Q ${{curr.x}} ${{curr.y}} ${{ax}} ${{ay}}`;
    }}
    d += ` L ${{pts[pts.length-1].x}} ${{pts[pts.length-1].y}}`;
    return d;
  }}

  // ── Edges (rendered FIRST — nodes render on top, covering crossings) ──
  // Orthogonal routing only: horizontal/vertical segments with right-angle turns.
  // Like Azure official architecture diagrams.
  EDGES.forEach(edge => {{
    const fn = NODES.find(n => n.id === edge.from);
    const tn = NODES.find(n => n.id === edge.to);
    if (!fn || !tn) return;
    const fromBox = getNodeBox(fn);
    const toBox = getNodeBox(tn);
    if (!fromBox || !toBox) return;

    const isPeEdge = edge.type === 'private';
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    let pts, labelX, labelY;

    if (isPeEdge) {{
      // PE → direct vertical
      const sx = fromBox.cx, sy = fromBox.y + fromBox.h;
      const ex = toBox.cx, ey = toBox.y;
      pts = [{{x: sx, y: sy}}, {{x: ex, y: ey}}];
    }} else {{
      // Orthogonal routing: determine exit/entry sides
      const dx = toBox.cx - fromBox.cx;
      const dy = toBox.cy - fromBox.cy;
      let exitSide, entrySide;

      if (Math.abs(dx) >= Math.abs(dy)) {{
        exitSide = dx >= 0 ? 'right' : 'left';
        entrySide = dx >= 0 ? 'left' : 'right';
      }} else {{
        exitSide = dy >= 0 ? 'bottom' : 'top';
        entrySide = dy >= 0 ? 'top' : 'bottom';
      }}

      const sp = borderExit(fromBox, exitSide);
      const ep = borderExit(toBox, entrySide);
      const stagger = (_routeCounter % 5 - 2) * 6;
      _routeCounter++;

      if (exitSide === 'right' || exitSide === 'left') {{
        if (Math.abs(sp.y - ep.y) < 8) {{
          pts = [sp, ep]; // straight horizontal
        }} else {{
          const midX = (sp.x + ep.x) / 2 + stagger;
          pts = [sp, {{x: midX, y: sp.y}}, {{x: midX, y: ep.y}}, ep];
        }}
      }} else {{
        if (Math.abs(sp.x - ep.x) < 8) {{
          pts = [sp, ep]; // straight vertical
        }} else {{
          const midY = (sp.y + ep.y) / 2 + stagger;
          pts = [sp, {{x: sp.x, y: midY}}, {{x: ep.x, y: midY}}, ep];
        }}
      }}
    }}

    // Render path
    path.setAttribute('d', pts.length <= 2
      ? `M ${{pts[0].x}} ${{pts[0].y}} L ${{pts[pts.length-1].x}} ${{pts[pts.length-1].y}}`
      : buildOrthoPath(pts));
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', isPeEdge ? '#5C2D91' : '#8a8886');
    path.setAttribute('stroke-width', isPeEdge ? '1' : '1.2');
    path.setAttribute('stroke-dasharray', edge.dash || '0');
    path.setAttribute('marker-end', `url(#${{markerFor(edge.type)}})`);
    path.setAttribute('opacity', isPeEdge ? '0.5' : '0.65');
    root.appendChild(path);

    // Label on middle segment
    const mid = Math.floor(pts.length / 2);
    labelX = (pts[Math.max(0,mid-1)].x + pts[Math.min(pts.length-1,mid)].x) / 2;
    labelY = (pts[Math.max(0,mid-1)].y + pts[Math.min(pts.length-1,mid)].y) / 2;

    if (edge.label) {{
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const r = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      const bw = edge.label.length * 5.5 + 10;
      r.setAttribute('x', labelX-bw/2); r.setAttribute('y', labelY-7);
      r.setAttribute('width', bw); r.setAttribute('height', 14);
      r.setAttribute('rx', '3'); r.setAttribute('fill', 'white');
      r.setAttribute('stroke', '#d2d0ce'); r.setAttribute('stroke-width', '0.5');
      r.setAttribute('opacity', '0.92');
      t.setAttribute('x', labelX); t.setAttribute('y', labelY+3);
      t.setAttribute('text-anchor', 'middle'); t.setAttribute('font-size', '8');
      t.setAttribute('fill', '#605e5c'); t.setAttribute('font-family', 'Segoe UI, sans-serif');
      t.textContent = edge.label;
      g.appendChild(r); g.appendChild(t);
      root.appendChild(g);
    }}
  }});

  // ── Nodes (rendered LAST — on top of edges, covering crossing points) ──
  NODES.forEach(node => {{
    const pos = positions[node.id];
    if (!pos) return;
    const isPe = node.type === 'pe';
    const nw = isPe ? PE_W : SVC_W;
    const nh = isPe ? PE_H : SVC_H;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'node');
    g.setAttribute('data-id', node.id);
    g.setAttribute('transform', `translate(${{pos.x}},${{pos.y}})`);

    // Card background — full clickable area
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('class', 'node-bg');
    rect.setAttribute('width', nw); rect.setAttribute('height', nh);
    rect.setAttribute('rx', '8'); rect.setAttribute('fill', 'white');
    rect.setAttribute('stroke', '#edebe9'); rect.setAttribute('stroke-width', '1');
    rect.setAttribute('filter', 'url(#shadow)');
    g.appendChild(rect);

    // Color accent bar at top
    const accent = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    accent.setAttribute('width', nw); accent.setAttribute('height', '3');
    accent.setAttribute('rx', '8'); accent.setAttribute('fill', node.color);
    accent.setAttribute('opacity', '0.7');
    g.appendChild(accent);

    // Icon (SVG)
    const iconSize = isPe ? 28 : 36;
    const iconX = (nw - iconSize) / 2;
    const iconY = isPe ? 10 : 12;
    const iconG = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    iconG.setAttribute('x', iconX); iconG.setAttribute('y', iconY);
    iconG.setAttribute('width', iconSize); iconG.setAttribute('height', iconSize);
    iconG.setAttribute('viewBox', '0 0 48 48');
    iconG.innerHTML = node.icon_svg;
    g.appendChild(iconG);

    // Name
    const name = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    name.setAttribute('x', nw/2); name.setAttribute('y', isPe ? 52 : 60);
    name.setAttribute('text-anchor', 'middle');
    name.setAttribute('font-size', isPe ? '9' : '10');
    name.setAttribute('font-weight', '600'); name.setAttribute('fill', '#323130');
    name.setAttribute('font-family', 'Segoe UI, sans-serif');
    const maxC = isPe ? 12 : 16;
    name.textContent = node.name.length > maxC ? node.name.substring(0, maxC-1) + '..' : node.name;
    g.appendChild(name);

    // SKU label
    if (!isPe && node.sku) {{
      const sku = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      sku.setAttribute('x', nw/2); sku.setAttribute('y', 72);
      sku.setAttribute('text-anchor', 'middle');
      sku.setAttribute('font-size', '9'); sku.setAttribute('fill', '#a19f9d');
      sku.setAttribute('font-family', 'Segoe UI, sans-serif');
      sku.textContent = node.sku;
      g.appendChild(sku);
    }}

    if (isPe && node.details.length > 0) {{
      const det = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      det.setAttribute('x', nw/2); det.setAttribute('y', 63);
      det.setAttribute('text-anchor', 'middle');
      det.setAttribute('font-size', '8'); det.setAttribute('fill', '#a19f9d');
      det.setAttribute('font-family', 'Segoe UI, sans-serif');
      det.textContent = node.details[0];
      g.appendChild(det);
    }}

    // Category label below
    if (!isPe) {{
      const cat = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      cat.setAttribute('x', nw/2); cat.setAttribute('y', nh + 14);
      cat.setAttribute('text-anchor', 'middle');
      cat.setAttribute('font-size', '9'); cat.setAttribute('fill', node.color);
      cat.setAttribute('font-weight', '600');
      cat.setAttribute('font-family', 'Segoe UI, sans-serif');
      cat.textContent = node.category;
      g.appendChild(cat);
    }}

    // Private badge on card
    if (node.private && !isPe) {{
      const badge = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const br = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      br.setAttribute('x', nw - 8); br.setAttribute('y', '4');
      br.setAttribute('width', '6'); br.setAttribute('height', '6');
      br.setAttribute('rx', '3'); br.setAttribute('fill', '#5C2D91');
      br.setAttribute('opacity', '0.6');
      badge.appendChild(br);
      g.appendChild(badge);
    }}

    // ── Events: drag vs click separation ──
    let _dragStartX = 0, _dragStartY = 0, _didDrag = false;
    g.addEventListener('mousedown', e => {{
      if (e.button !== 0) return;
      dragging = node.id;
      _didDrag = false;
      _dragStartX = e.clientX; _dragStartY = e.clientY;
      const svgPt = getSVGPoint(e);
      dragOffX = svgPt.x - pos.x; dragOffY = svgPt.y - pos.y;
      e.stopPropagation(); e.preventDefault();
    }});
    g.addEventListener('mousemove', e => {{
      if (dragging === node.id) {{
        const dx = Math.abs(e.clientX - _dragStartX);
        const dy = Math.abs(e.clientY - _dragStartY);
        if (dx > 3 || dy > 3) _didDrag = true;
      }}
    }});
    g.addEventListener('mouseup', e => {{
      if (!_didDrag && dragging === node.id) {{
        selectNode(node.id);
      }}
    }});
    g.addEventListener('mouseenter', e => {{
      const tt = document.getElementById('tooltip');
      const dets = node.details.map(d => `<div class="tooltip-detail">› ${{d}}</div>`).join('');
      tt.style.display = 'block';
      tt.innerHTML = `<strong>${{node.name}}</strong>${{node.sku ? `<div class="tooltip-detail">SKU: ${{node.sku}}</div>` : ''}}${{dets}}`;
    }});
    g.addEventListener('mousemove', e => {{
      const tt = document.getElementById('tooltip');
      tt.style.left = (e.clientX+12)+'px'; tt.style.top = (e.clientY-8)+'px';
    }});
    g.addEventListener('mouseleave', () => {{ document.getElementById('tooltip').style.display = 'none'; }});

    root.appendChild(g);
  }});

}}

function getSVGPoint(e) {{
  const svg = document.getElementById('canvas');
  const pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  return pt.matrixTransform(document.getElementById('diagram-root').getScreenCTM().inverse());
}}

document.getElementById('canvas').addEventListener('mousemove', e => {{
  if (!dragging) return;
  const p = getSVGPoint(e);
  positions[dragging].x = p.x - dragOffX;
  positions[dragging].y = p.y - dragOffY;
  renderDiagram();
}});
document.addEventListener('mouseup', () => {{ dragging = null; }});

// ── Pan & Zoom ──
function applyTransform() {{
  document.getElementById('diagram-root').setAttribute('transform',
    `translate(${{viewTransform.x}},${{viewTransform.y}}) scale(${{viewTransform.scale}})`);
  document.getElementById('zoom-level').textContent = Math.round(viewTransform.scale * 100) + '%';
}}
function fitToScreen() {{
  const svg = document.getElementById('canvas');
  const root = document.getElementById('diagram-root');
  root.setAttribute('transform', '');
  const bbox = root.getBBox();
  if (!bbox.width || !bbox.height) return;
  const w = svg.clientWidth, h = svg.clientHeight;
  const s = Math.min((w-60)/bbox.width, (h-60)/bbox.height, 1.5);
  if (s <= 0) return;
  viewTransform.scale = s;
  viewTransform.x = (w - bbox.width*s)/2 - bbox.x*s;
  viewTransform.y = (h - bbox.height*s)/2 - bbox.y*s;
  applyTransform();
}}
function zoomIn() {{ viewTransform.scale *= 1.25; applyTransform(); }}
function zoomOut() {{ viewTransform.scale *= 0.8; applyTransform(); }}
function resetZoom() {{ viewTransform = {{x:0,y:0,scale:1}}; applyTransform(); }}

document.getElementById('canvas').addEventListener('wheel', e => {{
  e.preventDefault();
  const f = e.deltaY < 0 ? 1.1 : 0.9;
  const rect = document.getElementById('canvas').getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const os = viewTransform.scale, ns = os * f;
  viewTransform.x = mx - (mx - viewTransform.x) * (ns/os);
  viewTransform.y = my - (my - viewTransform.y) * (ns/os);
  viewTransform.scale = ns;
  applyTransform();
}}, {{ passive: false }});

document.getElementById('canvas').addEventListener('mousedown', e => {{
  if (e.target.closest('.node')) return;
  isPanning = true;
  panSX = e.clientX; panSY = e.clientY;
  panSTx = viewTransform.x; panSTy = viewTransform.y;
  document.getElementById('canvas').style.cursor = 'grabbing';
  e.preventDefault();
}});
document.addEventListener('mousemove', e => {{
  if (isPanning) {{
    viewTransform.x = panSTx + (e.clientX - panSX);
    viewTransform.y = panSTy + (e.clientY - panSY);
    applyTransform();
  }}
}});
document.addEventListener('mouseup', () => {{
  if (isPanning) {{ isPanning = false; document.getElementById('canvas').style.cursor = ''; }}
}});

// ── Sidebar ──
function buildSidebar() {{
  const list = document.getElementById('service-list');
  const byCat = {{}};
  NODES.forEach(n => {{ if (!byCat[n.category]) byCat[n.category] = []; byCat[n.category].push(n); }});
  Object.entries(byCat).forEach(([cat, nodes]) => {{
    const cd = document.createElement('div');
    cd.className = 'cat-label'; cd.textContent = cat;
    list.appendChild(cd);
    nodes.forEach(node => {{
      const card = document.createElement('div');
      card.className = 'service-card'; card.id = 'card-' + node.id;
      card.innerHTML = `
        <div class="service-card-header">
          <div class="sc-icon"><svg viewBox="0 0 48 48">${{node.icon_svg}}</svg></div>
          <div>
            <div class="service-name">${{node.name}}</div>
            <div class="service-sku">${{node.sku || node.type}}</div>
          </div>
          ${{node.private ? '<span class="private-badge">Private</span>' : ''}}
        </div>
        ${{node.details.length > 0 ? `<div class="service-card-body">${{node.details.map(d => `<div class="service-detail">${{d}}</div>`).join('')}}</div>` : ''}}
      `;
      card.addEventListener('click', () => {{
        selectNode(node.id);
      }});
      list.appendChild(card);
    }});
  }});
}}

renderDiagram();
buildSidebar();
setTimeout(fitToScreen, 100);
</script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Azure Interactive Architecture Diagram Generator")
    parser.add_argument("--services", type=str, required=True)
    parser.add_argument("--connections", type=str, required=True)
    parser.add_argument("--title", type=str, default="Azure Architecture")
    parser.add_argument("--output", type=str, default="archi_diagram.html")
    args = parser.parse_args()

    try:
        services = json.loads(args.services)
        connections = json.loads(args.connections)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    html = generate_html(services, connections, args.title)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"SUCCESS: Interactive diagram saved to {args.output}")


if __name__ == "__main__":
    main()
