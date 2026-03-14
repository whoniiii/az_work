#!/usr/bin/env python3
"""
Azure Interactive Architecture Diagram Generator
서비스 목록과 연결 관계를 받아 인터랙티브 HTML 다이어그램을 생성한다.

사용법:
  python generate_html_diagram.py \
    --services '[{"id":"openai","name":"Azure OpenAI","type":"openai","sku":"S0","private":true,"details":["gpt-4o"]}]' \
    --connections '[{"from":"openai","to":"search","label":"벡터 검색","type":"api"}]' \
    --title "RAG 아키텍처" \
    --output "/path/to/architecture-draft.html"
"""

import argparse
import json
import sys
from datetime import datetime

# Azure 서비스별 아이콘 이모지 및 색상
SERVICE_ICONS = {
    "openai":       {"emoji": "🧠", "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"},
    "ai_foundry":   {"emoji": "🏭", "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"},
    "ai_hub":       {"emoji": "🏭", "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"},
    "search":       {"emoji": "🔍", "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"},
    "aml":          {"emoji": "⚗️",  "color": "#0078D4", "bg": "#E8F4FD", "category": "AI"},
    "storage":      {"emoji": "🗄️",  "color": "#0F9D58", "bg": "#E8F8F0", "category": "Data"},
    "adls":         {"emoji": "🏞️",  "color": "#0F9D58", "bg": "#E8F8F0", "category": "Data"},
    "fabric":       {"emoji": "🧵",  "color": "#0F9D58", "bg": "#E8F8F0", "category": "Data"},
    "synapse":      {"emoji": "⚡",  "color": "#0F9D58", "bg": "#E8F8F0", "category": "Data"},
    "adf":          {"emoji": "🔄",  "color": "#0F9D58", "bg": "#E8F8F0", "category": "Data"},
    "keyvault":     {"emoji": "🔐",  "color": "#E8A000", "bg": "#FEF7E0", "category": "Security"},
    "kv":           {"emoji": "🔐",  "color": "#E8A000", "bg": "#FEF7E0", "category": "Security"},
    "vnet":         {"emoji": "🌐",  "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"},
    "pe":           {"emoji": "🔒",  "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"},
    "nsg":          {"emoji": "🛡️",  "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"},
    "acr":          {"emoji": "📦",  "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"},
    "aks":          {"emoji": "☸️",  "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"},
    "appservice":   {"emoji": "🖥️",  "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"},
    "appinsights":  {"emoji": "📊",  "color": "#773ADC", "bg": "#F0EAFA", "category": "Monitor"},
    "monitor":      {"emoji": "📈",  "color": "#773ADC", "bg": "#F0EAFA", "category": "Monitor"},
    "vm":           {"emoji": "🖥️",  "color": "#0078D4", "bg": "#E8F4FD", "category": "Compute"},
    "bastion":      {"emoji": "🛡️",  "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"},
    "jumpbox":      {"emoji": "🛡️",  "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"},
    "vpn":          {"emoji": "🔗",  "color": "#5C2D91", "bg": "#F3EEF9", "category": "Network"},
    "adf":          {"emoji": "🔄",  "color": "#0F9D58", "bg": "#E8F8F0", "category": "Data"},
    "user":         {"emoji": "👤",  "color": "#666666", "bg": "#F5F5F5", "category": "External"},
    "app":          {"emoji": "💻",  "color": "#666666", "bg": "#F5F5F5", "category": "External"},
    "default":      {"emoji": "☁️",  "color": "#0078D4", "bg": "#E8F4FD", "category": "Azure"},
}

CONNECTION_STYLES = {
    "api":      {"color": "#0078D4", "dash": "0",      "label_bg": "#E8F4FD"},
    "data":     {"color": "#0F9D58", "dash": "0",      "label_bg": "#E8F8F0"},
    "security": {"color": "#E8A000", "dash": "5,5",    "label_bg": "#FEF7E0"},
    "network":  {"color": "#5C2D91", "dash": "5,5",    "label_bg": "#F3EEF9"},
    "default":  {"color": "#666666", "dash": "0",      "label_bg": "#F5F5F5"},
}


def get_service_info(svc_type: str) -> dict:
    t = svc_type.lower().replace("-", "_").replace(" ", "_")
    return SERVICE_ICONS.get(t, SERVICE_ICONS["default"])


def generate_html(services: list, connections: list, title: str) -> str:
    # 서비스 카테고리별 그룹화
    categories = {}
    for svc in services:
        info = get_service_info(svc.get("type", "default"))
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(svc)

    # 서비스 노드 JS 데이터
    nodes_js = json.dumps([{
        "id": svc["id"],
        "name": svc["name"],
        "type": svc.get("type", "default"),
        "sku": svc.get("sku", ""),
        "private": svc.get("private", True),
        "details": svc.get("details", []),
        "icon": get_service_info(svc.get("type", "default"))["emoji"],
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

    private_count = sum(1 for s in services if s.get("private", True))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Azure Architecture</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', -apple-system, sans-serif; background: #f0f2f5; color: #1a1a1a; }}

  .header {{
    background: linear-gradient(135deg, #0078D4 0%, #106EBE 100%);
    color: white; padding: 20px 28px; display: flex; align-items: center; gap: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }}
  .header h1 {{ font-size: 20px; font-weight: 600; }}
  .header .meta {{ font-size: 13px; opacity: 0.8; margin-top: 3px; }}
  .ms-logo {{ font-size: 28px; }}

  .badges {{
    display: flex; gap: 8px; margin-top: 8px;
  }}
  .badge {{
    background: rgba(255,255,255,0.2); border-radius: 12px;
    padding: 2px 10px; font-size: 12px;
  }}

  .container {{ display: flex; height: calc(100vh - 90px); }}

  /* Canvas area */
  .canvas-area {{
    flex: 1; position: relative; overflow: hidden; background: #fafafa;
    background-image: radial-gradient(circle, #ddd 1px, transparent 1px);
    background-size: 24px 24px;
    height: 100%;
  }}
  #canvas {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}

  /* Sidebar */
  .sidebar {{
    width: 300px; background: white; border-left: 1px solid #e0e0e0;
    overflow-y: auto; display: flex; flex-direction: column;
  }}
  .sidebar-header {{
    padding: 16px; border-bottom: 1px solid #e0e0e0; font-weight: 600;
    font-size: 14px; color: #333; background: #f8f9fa;
  }}

  .service-card {{
    margin: 8px; border: 1px solid #e0e0e0; border-radius: 8px;
    overflow: hidden; cursor: pointer; transition: all 0.15s;
  }}
  .service-card:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,0.1); transform: translateY(-1px); }}
  .service-card.selected {{ border-color: #0078D4; box-shadow: 0 0 0 2px rgba(0,120,212,0.2); }}

  .service-card-header {{
    padding: 10px 12px; display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid #f0f0f0;
  }}
  .service-icon {{ font-size: 20px; width: 32px; text-align: center; }}
  .service-name {{ font-size: 13px; font-weight: 600; }}
  .service-sku {{ font-size: 11px; color: #888; margin-top: 2px; }}
  .service-card-body {{ padding: 8px 12px; }}
  .service-detail {{
    font-size: 11px; color: #555; padding: 2px 0;
    display: flex; align-items: center; gap: 4px;
  }}
  .service-detail::before {{ content: "•"; color: #0078D4; }}
  .private-badge {{
    font-size: 10px; background: #f3eef9; color: #5C2D91;
    border-radius: 8px; padding: 1px 7px; margin-left: auto;
    border: 1px solid #d4b8ff;
  }}

  .legend {{
    padding: 12px 16px; border-top: 1px solid #e0e0e0;
    margin-top: auto;
  }}
  .legend-title {{ font-size: 12px; font-weight: 600; color: #555; margin-bottom: 8px; }}
  .legend-item {{
    display: flex; align-items: center; gap: 8px;
    font-size: 11px; color: #666; margin-bottom: 4px;
  }}
  .legend-line {{
    width: 24px; height: 2px;
  }}

  /* SVG styles */
  .node {{ cursor: pointer; }}
  .node-rect {{ rx: 10; ry: 10; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); transition: all 0.15s; }}
  .node-rect:hover {{ filter: drop-shadow(0 4px 12px rgba(0,0,0,0.2)); }}
  .edge-label {{
    font-size: 10px; fill: #555;
    background: white; padding: 2px 4px; border-radius: 3px;
  }}

  .category-label {{
    font-size: 11px; fill: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
  }}

  .vnet-rect {{
    fill: none; stroke: #5C2D91; stroke-width: 2; stroke-dasharray: 8,4;
    rx: 16; ry: 16;
  }}
  .vnet-label {{ font-size: 12px; fill: #5C2D91; font-weight: 600; }}

  .toolbar {{
    position: absolute; top: 12px; left: 12px; display: flex; gap: 6px; z-index: 10;
  }}
  .tool-btn {{
    background: white; border: 1px solid #ddd; border-radius: 6px;
    padding: 6px 12px; font-size: 12px; cursor: pointer; color: #333;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: all 0.15s;
  }}
  .tool-btn:hover {{ background: #f0f0f0; }}

  .status-bar {{
    position: absolute; bottom: 12px; left: 12px; right: 12px;
    background: white; border: 1px solid #e0e0e0; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; color: #555;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  .status-ok {{ color: #0F9D58; font-weight: 600; }}

  .tooltip {{
    position: absolute; background: #333; color: white; padding: 6px 10px;
    border-radius: 6px; font-size: 11px; pointer-events: none;
    white-space: nowrap; z-index: 100; display: none;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="ms-logo">☁️</div>
  <div>
    <h1>{title}</h1>
    <div class="meta">Azure Architecture Draft · 생성: {generated_at}</div>
    <div class="badges">
      <span class="badge">🔒 {private_count}/{len(services)} Private</span>
      <span class="badge">📦 {len(services)} 서비스</span>
      <span class="badge">🔗 {len(connections)} 연결</span>
    </div>
  </div>
</div>

<div class="container">
  <div class="canvas-area">
    <div class="toolbar">
      <button class="tool-btn" onclick="fitToScreen()">↔ 맞추기</button>
      <button class="tool-btn" onclick="zoomIn()">+ 확대</button>
      <button class="tool-btn" onclick="zoomOut()">- 축소</button>
      <button class="tool-btn" onclick="resetZoom()">↺ 리셋</button>
    </div>
    <svg id="canvas">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#0078D4" opacity="0.7"/>
        </marker>
        <marker id="arrow-data" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#0F9D58" opacity="0.7"/>
        </marker>
        <marker id="arrow-security" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#E8A000" opacity="0.7"/>
        </marker>
        <filter id="shadow">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.12"/>
        </filter>
      </defs>
      <g id="diagram-root">
        <!-- Diagram content will be inserted here by JS -->
      </g>
    </svg>
    <div id="tooltip" class="tooltip"></div>
    <div class="status-bar">
      <span>💡 노드를 드래그하거나 클릭하면 세부 정보를 볼 수 있습니다</span>
      <span class="status-ok">✅ 초안 완성 — 수정이 필요하면 Claude에게 말씀해주세요</span>
    </div>
  </div>

  <div class="sidebar">
    <div class="sidebar-header">📋 서비스 목록</div>
    <div id="service-list"></div>
    <div class="legend">
      <div class="legend-title">연결선 범례</div>
      <div class="legend-item">
        <div class="legend-line" style="background:#0078D4;"></div> API 호출
      </div>
      <div class="legend-item">
        <div class="legend-line" style="background:#0F9D58;"></div> 데이터 흐름
      </div>
      <div class="legend-item">
        <div class="legend-line" style="background:#E8A000; height:2px; background: repeating-linear-gradient(90deg,#E8A000 0,#E8A000 5px,transparent 5px,transparent 10px);"></div> 보안/키 참조
      </div>
    </div>
  </div>
</div>

<script>
const NODES_DATA = {nodes_js};
const EDGES_DATA = {edges_js};

// Layout: position nodes in a smart grid
const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 600;
const NODE_W = 160;
const NODE_H = 80;
const PADDING = 40;

// Group nodes by category
const categoryGroups = {{}};
NODES_DATA.forEach(n => {{
  if (!categoryGroups[n.category]) categoryGroups[n.category] = [];
  categoryGroups[n.category].push(n);
}});

// Assign positions
const positions = {{}};

// PE 노드는 연결된 리소스 바로 아래에 배치 — 나머지 노드 먼저 배치 후 처리
const peNodes = NODES_DATA.filter(n => n.type === 'pe');
const nonPeNodes = NODES_DATA.filter(n => n.type !== 'pe');

const catKeys = Object.keys(categoryGroups).filter(c =>
  nonPeNodes.some(n => n.category === c)
);
const cols = Math.ceil(Math.sqrt(nonPeNodes.length));

let xi = 0, yi = 0;
catKeys.forEach(cat => {{
  const nodes = nonPeNodes.filter(n => n.category === cat);
  nodes.forEach((n, i) => {{
    positions[n.id] = {{
      x: PADDING + (xi % cols) * (NODE_W + 60),
      y: PADDING + yi * (NODE_H + 50) + (yi > 0 ? 20 : 0),
    }};
    xi++;
    if (xi % cols === 0) yi++;
  }});
  yi++;
}});

// PE 노드: 연결된 리소스(edge의 to) 바로 아래에 배치
peNodes.forEach(pe => {{
  const edge = EDGES_DATA.find(e => e.from === pe.id || e.to === pe.id);
  const parentId = edge ? (edge.from === pe.id ? edge.to : edge.from) : null;
  const parentPos = parentId ? positions[parentId] : null;
  positions[pe.id] = parentPos
    ? {{ x: parentPos.x, y: parentPos.y + NODE_H + 30 }}
    : {{ x: PADDING + xi * (NODE_W + 60), y: PADDING }};
}});

// Dragging state
let dragging = null, dragOffX = 0, dragOffY = 0;
let viewTransform = {{ x: 0, y: 0, scale: 1 }};

function getMarkerForType(type) {{
  if (type === 'data') return 'arrow-data';
  if (type === 'security') return 'arrow-security';
  return 'arrow';
}}

function renderDiagram() {{
  const root = document.getElementById('diagram-root');
  root.innerHTML = '';

  // Detect private nodes for VNet boundary
  const privateNodes = NODES_DATA.filter(n => n.private);
  if (privateNodes.length > 0) {{
    const pxs = privateNodes.map(n => positions[n.id].x);
    const pys = privateNodes.map(n => positions[n.id].y);
    const minX = Math.min(...pxs) - 24;
    const minY = Math.min(...pys) - 40;
    const maxX = Math.max(...pxs) + NODE_W + 24;
    const maxY = Math.max(...pys) + NODE_H + 24;
    const vnet = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    vnet.setAttribute('x', minX); vnet.setAttribute('y', minY);
    vnet.setAttribute('width', maxX - minX); vnet.setAttribute('height', maxY - minY);
    vnet.setAttribute('class', 'vnet-rect');
    root.appendChild(vnet);
    const vnetLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    vnetLabel.setAttribute('x', minX + 12); vnetLabel.setAttribute('y', minY + 16);
    vnetLabel.setAttribute('class', 'vnet-label');
    vnetLabel.textContent = '🌐 Azure Virtual Network (Private)';
    root.appendChild(vnetLabel);
  }}

  // Draw edges first (behind nodes)
  EDGES_DATA.forEach(edge => {{
    const fromPos = positions[edge.from];
    const toPos = positions[edge.to];
    if (!fromPos || !toPos) return;

    const x1 = fromPos.x + NODE_W / 2;
    const y1 = fromPos.y + NODE_H / 2;
    const x2 = toPos.x + NODE_W / 2;
    const y2 = toPos.y + NODE_H / 2;

    // Curved path
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2 - 20;

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${{x1}} ${{y1}} Q ${{mx}} ${{my}} ${{x2}} ${{y2}}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', edge.color);
    path.setAttribute('stroke-width', '1.8');
    path.setAttribute('stroke-dasharray', edge.dash || '0');
    path.setAttribute('marker-end', `url(#${{getMarkerForType(edge.type)}})`);
    path.setAttribute('opacity', '0.75');
    root.appendChild(path);

    // Edge label
    if (edge.label) {{
      const labelG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', mx); text.setAttribute('y', my - 2);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('font-size', '10');
      text.setAttribute('fill', '#444');
      text.setAttribute('font-family', 'Segoe UI, sans-serif');
      text.textContent = edge.label;

      const bbox = {{ width: edge.label.length * 6.5 + 8, height: 16 }};
      rect.setAttribute('x', mx - bbox.width / 2); rect.setAttribute('y', my - 13);
      rect.setAttribute('width', bbox.width); rect.setAttribute('height', bbox.height);
      rect.setAttribute('rx', '4'); rect.setAttribute('fill', 'white');
      rect.setAttribute('stroke', '#e0e0e0'); rect.setAttribute('stroke-width', '1');
      labelG.appendChild(rect); labelG.appendChild(text);
      root.appendChild(labelG);
    }}
  }});

  // Draw nodes
  NODES_DATA.forEach(node => {{
    const pos = positions[node.id];
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('class', 'node');
    g.setAttribute('data-id', node.id);
    g.setAttribute('transform', `translate(${{pos.x}}, ${{pos.y}})`);

    // Node background
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('width', NODE_W); rect.setAttribute('height', NODE_H);
    rect.setAttribute('rx', '10'); rect.setAttribute('ry', '10');
    rect.setAttribute('fill', node.bg);
    rect.setAttribute('stroke', node.color);
    rect.setAttribute('stroke-width', '1.5');
    rect.setAttribute('filter', 'url(#shadow)');

    // Color accent bar at top
    const accent = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    accent.setAttribute('width', NODE_W); accent.setAttribute('height', '4');
    accent.setAttribute('rx', '10'); accent.setAttribute('fill', node.color);

    // Icon
    const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    icon.setAttribute('x', '16'); icon.setAttribute('y', '32');
    icon.setAttribute('font-size', '20');
    icon.textContent = node.icon;

    // Service name
    const name = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    name.setAttribute('x', '42'); name.setAttribute('y', '26');
    name.setAttribute('font-size', '11'); name.setAttribute('font-weight', '600');
    name.setAttribute('fill', '#1a1a1a');
    name.setAttribute('font-family', 'Segoe UI, sans-serif');
    name.textContent = node.name.length > 18 ? node.name.substring(0, 17) + '…' : node.name;

    // SKU
    const sku = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    sku.setAttribute('x', '42'); sku.setAttribute('y', '40');
    sku.setAttribute('font-size', '10'); sku.setAttribute('fill', '#666');
    sku.setAttribute('font-family', 'Segoe UI, sans-serif');
    sku.textContent = node.sku;

    // rect, accent 먼저 (배경) → 그 위에 텍스트들
    g.appendChild(rect); g.appendChild(accent);

    // Icon
    g.appendChild(icon);
    g.appendChild(name); g.appendChild(sku);

    // Private indicator
    if (node.private) {{
      const lockIcon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      lockIcon.setAttribute('x', NODE_W - 18); lockIcon.setAttribute('y', '26');
      lockIcon.setAttribute('font-size', '12'); lockIcon.setAttribute('fill', '#5C2D91');
      lockIcon.textContent = '🔒';
      g.appendChild(lockIcon);
    }}

    // Details (first 2)
    node.details.slice(0, 2).forEach((d, i) => {{
      const detail = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      detail.setAttribute('x', '12'); detail.setAttribute('y', `${{54 + i * 14}}`);
      detail.setAttribute('font-size', '9.5'); detail.setAttribute('fill', '#555');
      detail.setAttribute('font-family', 'Segoe UI, sans-serif');
      detail.textContent = '· ' + (d.length > 22 ? d.substring(0, 21) + '…' : d);
      g.appendChild(detail);
    }});

    // Drag events
    g.addEventListener('mousedown', e => {{
      dragging = node.id;
      const svgPt = getSVGPoint(e);
      dragOffX = svgPt.x - pos.x;
      dragOffY = svgPt.y - pos.y;
      e.preventDefault();
    }});

    // Tooltip
    g.addEventListener('mouseenter', e => {{
      const tooltip = document.getElementById('tooltip');
      const details = node.details.join('\\n• ');
      tooltip.style.display = 'block';
      tooltip.innerHTML = `<strong>${{node.icon}} ${{node.name}}</strong><br>SKU: ${{node.sku || 'N/A'}}<br>Private: ${{node.private ? '✅' : '❌'}}`;
    }});
    g.addEventListener('mousemove', e => {{
      const tooltip = document.getElementById('tooltip');
      tooltip.style.left = (e.clientX + 12) + 'px';
      tooltip.style.top = (e.clientY - 8) + 'px';
    }});
    g.addEventListener('mouseleave', () => {{
      document.getElementById('tooltip').style.display = 'none';
    }});

    // Click: highlight in sidebar
    g.addEventListener('click', () => {{
      document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
      const card = document.getElementById('card-' + node.id);
      if (card) {{
        card.classList.add('selected');
        card.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
      }}
    }});

    root.appendChild(g);
  }});
}}

function getSVGPoint(e) {{
  const svg = document.getElementById('canvas');
  const pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  const ctm = document.getElementById('diagram-root').getScreenCTM();
  return pt.matrixTransform(ctm.inverse());
}}

document.getElementById('canvas').addEventListener('mousemove', e => {{
  if (!dragging) return;
  const svgPt = getSVGPoint(e);
  positions[dragging].x = svgPt.x - dragOffX;
  positions[dragging].y = svgPt.y - dragOffY;
  renderDiagram();
}});
document.addEventListener('mouseup', () => {{ dragging = null; }});

// Zoom
function fitToScreen() {{
  const svg = document.getElementById('canvas');
  const root = document.getElementById('diagram-root');
  const bbox = root.getBBox();
  if (!bbox.width || !bbox.height) return;
  const w = svg.clientWidth || svg.getBoundingClientRect().width;
  const h = svg.clientHeight || svg.getBoundingClientRect().height;
  if (!w || !h) return;
  const scaleX = (w - 80) / bbox.width;
  const scaleY = (h - 100) / bbox.height;
  const scale = Math.min(scaleX, scaleY, 1.5);
  if (scale <= 0) return;
  const tx = (svg.clientWidth - bbox.width * scale) / 2 - bbox.x * scale;
  const ty = (svg.clientHeight - bbox.height * scale) / 2 - bbox.y * scale;
  root.setAttribute('transform', `translate(${{tx}},${{ty}}) scale(${{scale}})`);
}}
function zoomIn() {{ applyZoom(1.2); }}
function zoomOut() {{ applyZoom(0.8); }}
function resetZoom() {{ document.getElementById('diagram-root').setAttribute('transform', ''); }}
function applyZoom(factor) {{
  const root = document.getElementById('diagram-root');
  const transform = root.getAttribute('transform') || '';
  const match = transform.match(/scale\\(([^)]+)\\)/);
  const currentScale = match ? parseFloat(match[1]) : 1;
  const newScale = currentScale * factor;
  const newTransform = transform.replace(/scale\\([^)]+\\)/, '').trim() + ` scale(${{newScale}})`;
  root.setAttribute('transform', newTransform.trim());
}}

// Build sidebar
function buildSidebar() {{
  const list = document.getElementById('service-list');
  const byCat = {{}};
  NODES_DATA.forEach(n => {{
    if (!byCat[n.category]) byCat[n.category] = [];
    byCat[n.category].push(n);
  }});

  Object.entries(byCat).forEach(([cat, nodes]) => {{
    const catDiv = document.createElement('div');
    catDiv.style.cssText = 'padding:4px 12px 2px; font-size:11px; color:#888; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;';
    catDiv.textContent = cat;
    list.appendChild(catDiv);

    nodes.forEach(node => {{
      const card = document.createElement('div');
      card.className = 'service-card';
      card.id = 'card-' + node.id;
      card.style.borderLeftColor = node.color;
      card.style.borderLeftWidth = '3px';

      card.innerHTML = `
        <div class="service-card-header" style="background:${{node.bg}}">
          <div class="service-icon">${{node.icon}}</div>
          <div>
            <div class="service-name">${{node.name}}</div>
            <div class="service-sku">${{node.sku || ''}}</div>
          </div>
          ${{node.private ? '<span class="private-badge">🔒 Private</span>' : ''}}
        </div>
        ${{node.details.length > 0 ? `
        <div class="service-card-body">
          ${{node.details.map(d => `<div class="service-detail">${{d}}</div>`).join('')}}
        </div>` : ''}}
      `;
      card.addEventListener('click', () => {{
        document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        // Highlight node in canvas
        const nodeEl = document.querySelector(`[data-id="${{node.id}}"] rect`);
        if (nodeEl) {{
          nodeEl.style.strokeWidth = '3';
          setTimeout(() => nodeEl.style.strokeWidth = '1.5', 1500);
        }}
      }});
      list.appendChild(card);
    }});
  }});
}}

// Init
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
