#!/usr/bin/env python3
"""
Azure Architecture Diagram Generator
자연어에서 추출한 서비스/연결 정보를 받아 PNG 다이어그램을 생성한다.

사용법:
  python generate_diagram.py \
    --services '[{"name":"Azure OpenAI","type":"openai","private":true},{"name":"AI Search","type":"search","private":true}]' \
    --connections '[{"from":"Azure OpenAI","to":"AI Search","label":"벡터 검색"}]' \
    --title "RAG 아키텍처" \
    --output-path "/path/to/output/architecture"
"""

import argparse
import json
import sys
import os

def try_install_deps():
    """필요한 패키지를 설치한다."""
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "diagrams", "--break-system-packages", "-q"],
                   capture_output=True)
    try:
        subprocess.run(["apt-get", "install", "-y", "graphviz", "-q"],
                      capture_output=True, timeout=30)
    except Exception:
        pass


def get_node_class(service_type: str):
    """서비스 타입에 맞는 diagrams 노드 클래스를 반환한다."""
    mapping = {
        "openai": ("diagrams.azure.ml", "CognitiveServices"),
        "ai_foundry": ("diagrams.azure.ml", "MachineLearning"),
        "ai_hub": ("diagrams.azure.ml", "MachineLearning"),
        "aml": ("diagrams.azure.ml", "MachineLearning"),
        "search": ("diagrams.azure.analytics", "AnalysisServices"),
        "fabric": ("diagrams.azure.analytics", "SynapseAnalytics"),
        "synapse": ("diagrams.azure.analytics", "SynapseAnalytics"),
        "adf": ("diagrams.azure.analytics", "DataFactory"),
        "storage": ("diagrams.azure.storage", "DataLakeStorage"),
        "adls": ("diagrams.azure.storage", "DataLakeStorage"),
        "blob": ("diagrams.azure.storage", "BlobStorage"),
        "keyvault": ("diagrams.azure.security", "KeyVaults"),
        "kv": ("diagrams.azure.security", "KeyVaults"),
        "vnet": ("diagrams.azure.network", "VirtualNetworks"),
        "pe": ("diagrams.azure.network", "PrivateEndpoint"),
        "private_endpoint": ("diagrams.azure.network", "PrivateEndpoint"),
        "aad": ("diagrams.azure.identity", "ActiveDirectory"),
        "user": ("diagrams.azure.identity", "ActiveDirectory"),
        "acr": ("diagrams.azure.containers", "ContainerRegistries"),
        "aks": ("diagrams.azure.containers", "KubernetesServices"),
        "appservice": ("diagrams.azure.compute", "AppServices"),
        "eventhub": ("diagrams.azure.analytics", "EventHub"),
        "monitor": ("diagrams.azure.management", "Monitor"),
        "default": ("diagrams.azure.general", "Resourcegroups"),
    }
    t = service_type.lower().replace("-", "_").replace(" ", "_")
    module_name, class_name = mapping.get(t, mapping["default"])
    import importlib
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def generate_diagram(services: list, connections: list, title: str, output_path: str):
    """다이어그램을 생성하고 PNG 파일로 저장한다."""
    from diagrams import Diagram, Cluster, Edge

    graph_attr = {
        "fontsize": "14",
        "bgcolor": "white",
        "pad": "0.8",
        "splines": "ortho",
        "nodesep": "0.7",
        "ranksep": "1.0",
        "fontname": "Arial",
    }

    node_attr = {
        "fontsize": "10",
        "fontname": "Arial",
    }

    # Private 서비스와 Public 서비스 분리
    private_services = [s for s in services if s.get("private", True)]
    public_services = [s for s in services if not s.get("private", True)]

    with Diagram(
        title,
        filename=output_path,
        outformat="png",
        show=False,
        graph_attr=graph_attr,
        node_attr=node_attr,
        direction="LR",
    ):
        nodes = {}

        # Public 서비스 (VNet 밖)
        for svc in public_services:
            NodeClass = get_node_class(svc.get("type", "default"))
            nodes[svc["name"]] = NodeClass(svc["name"])

        # Private 서비스 (VNet 안)
        if private_services:
            with Cluster("Azure Virtual Network (Private)"):
                # Private Endpoint 서비스는 별도 클러스터로
                pe_services = [s for s in private_services if "private_endpoint" not in s.get("type", "")]
                for svc in pe_services:
                    NodeClass = get_node_class(svc.get("type", "default"))
                    nodes[svc["name"]] = NodeClass(svc["name"])

        # 연결 관계 그리기
        for conn in connections:
            from_name = conn.get("from", "")
            to_name = conn.get("to", "")
            label = conn.get("label", "")
            style = conn.get("style", "solid")
            color = conn.get("color", "black")

            if from_name in nodes and to_name in nodes:
                edge = Edge(
                    label=label,
                    style="dashed" if style == "dashed" else "solid",
                    color=color,
                )
                nodes[from_name] >> edge >> nodes[to_name]

    return output_path + ".png"


def main():
    parser = argparse.ArgumentParser(description="Azure Architecture Diagram Generator")
    parser.add_argument("--services", type=str, required=True, help="JSON array of services")
    parser.add_argument("--connections", type=str, required=True, help="JSON array of connections")
    parser.add_argument("--title", type=str, default="Azure Architecture", help="Diagram title")
    parser.add_argument("--output-path", type=str, required=True, help="Output file path (without extension)")
    args = parser.parse_args()

    try:
        services = json.loads(args.services)
        connections = json.loads(args.connections)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # 의존성 설치
    try_install_deps()

    try:
        output_file = generate_diagram(services, connections, args.title, args.output_path)
        print(f"SUCCESS: Diagram saved to {output_file}")
    except Exception as e:
        print(f"ERROR: Failed to generate diagram: {e}", file=sys.stderr)
        # Fallback: Mermaid 다이어그램 생성
        mermaid_path = args.output_path + ".mmd"
        generate_mermaid_fallback(services, connections, args.title, mermaid_path)
        print(f"FALLBACK: Mermaid diagram saved to {mermaid_path}")
        sys.exit(2)


def generate_mermaid_fallback(services, connections, title, output_path):
    """diagrams 실패 시 Mermaid 텍스트 다이어그램으로 폴백."""
    lines = [f"```mermaid", "graph LR"]
    private = [s for s in services if s.get("private", True)]
    public = [s for s in services if not s.get("private", True)]

    if private:
        lines.append('    subgraph VNet["Azure Virtual Network (Private)"]')
        for svc in private:
            node_id = svc["name"].replace(" ", "_").replace("-", "_")
            lines.append(f'        {node_id}["{svc["name"]}"]')
        lines.append("    end")

    for svc in public:
        node_id = svc["name"].replace(" ", "_").replace("-", "_")
        lines.append(f'    {node_id}(["{svc["name"]}"])')

    for conn in connections:
        from_id = conn["from"].replace(" ", "_").replace("-", "_")
        to_id = conn["to"].replace(" ", "_").replace("-", "_")
        label = conn.get("label", "")
        lines.append(f'    {from_id} -->|"{label}"| {to_id}')

    lines.append("```")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("\n".join(lines))

    return output_path


if __name__ == "__main__":
    main()
