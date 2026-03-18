---
name: azure-arch-builder
description: >
  Azure 멀티에이전트 아키텍처 설계 및 자동 배포 워크플로우. 자연어로 원하는 Azure 인프라를 말하면
  대화를 통해 아키텍처를 함께 확정하고, Bicep 생성 → 코드 리뷰 → 실제 Azure 배포까지
  단계별로 사용자 확인을 받으며 자동으로 진행한다.

  반드시 이 스킬을 사용해야 하는 경우:
  - "Azure에 X 만들어줘", "AI Search랑 Foundry 만들고 싶어", "RAG 아키텍처 구성해줘"
  - Azure 리소스 배포, Bicep 템플릿 생성, IaC 코드 생성
  - "프라이빗 엔드포인트 설정", "VNet 통합", "Azure 인프라 설계"
  - Microsoft Foundry, AI Search, OpenAI, Fabric, ADLS Gen2, AML 등 Azure AI/Data 서비스 조합
  - "Azure에 실제로 만들어줘", "az cli로 배포해줘", "리소스 그룹에 올려줘"
---

# Azure Architecture Builder — 멀티에이전트 오케스트레이션

자연어 → 대화형 설계 → Bicep 생성 → 코드 리뷰 → 실제 Azure 배포까지 이어지는 4단계 파이프라인.
모든 단계에서 사용자에게 확인을 받으며 진행한다.

## v1 Scope & Fallback

### v1 범위: Azure AI/Data-first

v1은 **Azure AI/Data 워크로드**에 특화한다:
- Microsoft Foundry (CognitiveServices/AIServices), Azure OpenAI 모델 배포
- Azure AI Search, ADLS Gen2, Key Vault
- Microsoft Fabric, Azure Data Factory
- VNet / Private Endpoint 네트워크 격리
- AML / AI Hub (사용자 명시 요청 시)

### 범위 밖 서비스 Fallback

v1 범위에 없는 서비스(VM, AKS, App Service, SQL Database 등)를 사용자가 요구할 경우:

1. **사용자에게 고지**: "이 서비스는 v1 기본 범위 밖이므로, MS Docs를 참조하여 best-effort로 생성합니다."
2. **MS Docs fetch**: `azure-dynamic-sources.md`의 URL 패턴으로 해당 서비스의 Bicep 레퍼런스 확인
3. **공통 패턴 적용**: `azure-common-patterns.md`의 PE/보안/명명 패턴 적용
4. **PE 매핑 확인**: `azure-dynamic-sources.md`의 PE DNS 통합 문서에서 groupId/DNS Zone 확인
5. **리뷰어에게 전달**: Bicep Reviewer가 `az bicep build`로 컴파일 검증

> 범위 밖이라고 거부하지 않는다. Fallback workflow로 처리하되, 품질 보장 수준이 다를 수 있음을 안내한다.

### Stable vs Dynamic 정보 처리 원칙

| 구분 | 정의 | 처리 방법 | 예시 |
|------|------|----------|------|
| **Stable** | 불변에 가까운 필수 속성, 패턴 | Reference 파일 우선 참조 | `isHnsEnabled: true`, PE 3종 세트, naming convention |
| **Dynamic** | 수시로 변경되는 값 | **항상 MS Docs fetch** | API version, 모델 가용성, SKU 목록, region 가용성 |

**Decision Rule:**
- Reference에 있는 정보라도, API version/SKU/region/모델명은 **항상 fetch**
- Reference에 있는 필수 속성/패턴은 **fetch 없이 참조 가능** (불변이므로)
- Reference에 없는 서비스는 **MS Docs fetch 후 공통 패턴 적용**

### MS Docs URL 탐색 원칙 — URL 직접 구성 금지

MS Docs URL은 수시로 변경되므로, **기억에서 URL 경로를 추측하여 구성하지 않는다.**

**절대 하지 말 것:**
- `https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/gpu-accelerated/overview` 같이 URL을 기억에서 조합하여 직접 fetch하는 것
- 404가 나면 경로를 살짝 바꿔서 재시도하는 것

**반드시 해야 할 것:**
1. `azure-dynamic-sources.md`에 해당 서비스의 URL 패턴이 있으면 → 그 패턴 사용
2. URL 패턴이 없으면 (v1 범위 밖 서비스 등) → **WebSearch로 올바른 URL을 먼저 찾는다**
   - 예: `WebSearch("Azure GPU VM sizes NCasT4 site:learn.microsoft.com")`
   - 검색 결과에서 실제 존재하는 URL을 확인한 후 WebFetch
3. fetch 중 404가 발생하면 → 즉시 WebSearch로 전환하여 올바른 URL 탐색

## 행동 원칙 (모든 Phase 공통)

### Deferred Tool 사전 로드 (최우선)

이 스킬은 `WebFetch`, `WebSearch`, `AskUserQuestion` 등 deferred tool을 빈번하게 사용한다.
**스킬 로드 직후, 다른 동작을 수행하기 전에** `ToolSearch`로 필요한 도구 스키마를 먼저 가져온다:

```
ToolSearch({ query: "select:WebFetch,WebSearch,AskUserQuestion", max_results: 3 })
```

스키마를 로드하지 않고 deferred tool을 호출하면 `Invalid tool parameters` 에러가 발생한다.
이 단계는 사용자에게 별도 안내 없이 자동으로 수행한다.

### 진행 상황 안내 필수

**모든 동작을 실행하기 전에, 사용자에게 무엇을 왜 하는지 한 줄로 안내한다.**
사용자는 내부 동작을 볼 수 없으므로, 도구 호출이나 명령 실행 전에 반드시 텍스트 메시지를 먼저 보낸다.

**안내 형식:** `[동작] — [이유]`

**예시:**
- `MS Docs에서 AI Search SKU 목록을 조회합니다 — 선택지를 정확하게 제공하기 위해서입니다.`
- `서브에이전트로 모델 가용성을 이중 검증합니다 — 1차 조회 결과를 독립적으로 확인하기 위해서입니다.`
- `Bicep 컴파일을 실행합니다 — 문법 에러가 없는지 확인하기 위해서입니다.`
- `What-if 검증을 실행합니다 — 실제 배포 전에 변경 사항을 미리 확인하기 위해서입니다.`
- `다이어그램을 생성합니다 — 확정된 아키텍처를 시각적으로 확인하실 수 있도록 합니다.`
- `배포된 리소스를 조회합니다 — 최종 다이어그램에 실제 리소스 정보를 반영하기 위해서입니다.`

**적용 대상 (이 동작들 전에 반드시 안내):**
- MS Docs WebFetch (팩트 체크, API 버전 조회 등)
- 서브에이전트 실행 (이중 검증 등)
- Bash 명령 실행 (az cli, bicep build, 다이어그램 생성 등)
- 파일 읽기/쓰기 (Bicep 파일 생성, 리뷰 등)
- AskUserQuestion 호출 (질문 의도 설명)

**하지 말 것:**
- 아무 말 없이 도구를 호출하는 것
- "잠시만요...", "확인 중..." 같은 모호한 메시지만 보내는 것
- 동작 후에야 뭘 했는지 설명하는 것

---

## PHASE 1: 아키텍처 어드바이저 (대화형 설계)

**이 Phase의 목표**: 사용자가 원하는 걸 정확히 파악하고, 아키텍처를 함께 확정하는 것.

### 1-1. 다이어그램 준비 — 필요 정보 수집

다이어그램을 그리기 전, 아래 항목이 모두 확정될 때까지 사용자에게 질문한다.
**모든 항목이 확정된 후 한 번에 다이어그램을 생성한다.**

**가장 먼저 프로젝트 이름을 확인한다:**

`AskUserQuestion`으로 기본값을 선택지로 제공한다. 사용자가 그냥 엔터만 치면 기본값이 적용되고, 직접 입력하고 싶으면 "Other"를 선택한다.
기본값은 사용자의 요청 내용에서 유추한다 (예: RAG 챗봇 → `rag-chatbot`, 데이터 플랫폼 → `data-platform`).

```
AskUserQuestion({
  questions: [{
    question: "프로젝트 이름을 정해주세요. Bicep 폴더명, 다이어그램 경로, 배포 이름에 사용됩니다.",
    header: "Project",
    options: [
      { label: "<유추한-기본값>", description: "이 이름으로 진행합니다" },
      { label: "azure-project", description: "기본 프로젝트명" }
    ],
    multiSelect: false
  }]
})
```
프로젝트 이름은 Bicep 출력 폴더명, 다이어그램 저장 경로, 배포 이름 등에 사용된다.

**🔹 아키텍처 가이던스 사전 조회 (질문 깊이 조정):**

사용자의 워크로드 유형이 파악되면, 다이어그램을 그리기 전에
`architecture-guidance-sources.md`의 decision rule에 따라
해당 워크로드의 reference architecture 문서를 최대 2개 targeted fetch한다.

**목적**: SKU/region 같은 스펙 질문만이 아니라,
공식 아키텍처가 권장하는 **설계 판단 포인트**를 질문에 반영하는 것.

**예시 — "RAG 챗봇" 요청 시:**
- Baseline Foundry Chat Architecture(A6) fetch
- 문서에서 권장하는 설계 판단 포인트 추출:
  → 네트워크 격리 수준 (full private vs hybrid?)
  → 인증 방식 (managed identity vs API key?)
  → 데이터 수집 전략 (push vs pull indexing?)
  → 모니터링 범위 (Application Insights 필요 여부?)
- 이 포인트들을 사용자 질문에 자연스럽게 포함

**주의:**
- architecture guidance에서 추출하는 것은 **"질문할 포인트"**이지 "정답"이 아님
- SKU/API version/region 같은 배포 스펙은 여전히 `azure-dynamic-sources.md` 경로로만 결정
- fetch budget: 최대 2개 문서. 전체 순회 금지

**확정 필요 항목:**
- [ ] 프로젝트 이름 (기본값: `azure-project`)
- [ ] 서비스 목록 (어떤 Azure 서비스를 쓸 것인지)
- [ ] 각 서비스의 SKU/티어
- [ ] 네트워킹 방식 (Private Endpoint 여부)
- [ ] 배포 위치 (region)

**질문 원칙:**
- 사용자가 이미 언급한 정보는 다시 묻지 않는다
- 다이어그램에 직접 표현되지 않는 세부 구현 사항(인덱싱 방법, 쿼리량 등)은 묻지 않는다
- 한 번에 너무 많은 질문을 하지 말고, 핵심 미확정 항목만 간결하게 묻는다
- 기본값이 명확한 항목(예: PE 적용 등)은 가정하고 확인만 받는다. 단, 위치는 반드시 사용자에게 확인받는다
- **SKU, 모델, 서비스 옵션을 물을 때는 MS Docs에서 확인한 전체 선택지를 보여주고, 해당 MS Docs URL도 함께 제공**한다. 사용자가 직접 참고하여 판단할 수 있도록 한다. 일부 옵션만 보여주거나 자의적으로 걸러내지 않는다

**🔹 서비스 옵션 탐색 원칙 — "기억에서 나열" 금지:**

사용자가 서비스 카테고리를 질문하거나("Spark 뭐 있어?", "메시지 큐 옵션은?"), 또는 특정 기능을 수행할 서비스를 탐색해야 할 때:

**절대 하지 말 것:**
- 본인 기억에 있는 2~3개 서비스만 URL 직접 fetch하여 나열하는 것
- "Azure에서 X는 A와 B가 있다"고 단정하는 것

**반드시 해야 할 것:**
1. **WebSearch로 카테고리 전체 탐색** — `"Azure managed Spark options site:learn.microsoft.com"` 같이 카테고리 수준으로 검색하여 어떤 서비스들이 존재하는지 먼저 발견한다
2. **v1 scope 교차 확인** — 검색 결과와 별개로, v1 범위 서비스(Foundry, Fabric, AI Search, ADLS Gen2 등)가 해당 카테고리에 해당하는지 확인한다. 예: "Spark" → Microsoft Fabric의 Data Engineering 워크로드도 Spark를 제공함
3. **발견된 옵션들을 targeted fetch** — 검색으로 발견한 서비스들의 MS Docs를 fetch하여 정확한 비교 정보를 수집한다
4. **사용자에게 전체 선택지 제시** — 발견된 모든 옵션을 빠짐없이 비교 제시한다

**예시 — "Spark 인스턴스 뭐가 있어?" 질문 시:**
```
잘못된 접근: Databricks URL + Synapse URL만 직접 fetch → 2개만 비교
올바른 접근: WebSearch("Azure managed Spark options") → Databricks, Synapse, Fabric Spark, HDInsight 발견
            → v1 scope 확인: Fabric이 v1 범위이고 Spark 제공 → 반드시 포함
            → 각 서비스 MS Docs targeted fetch → 전체 비교표 제시
```

이 원칙은 서비스 카테고리 탐색뿐 아니라, 사용자가 "대안", "다른 옵션", "비교" 등을 요구하는 모든 상황에 적용된다.

**🔹 AskUserQuestion 도구 필수 사용:**

선택지가 있는 질문은 반드시 `AskUserQuestion` 도구를 사용한다. 사용자가 화살표키로 선택할 수 있어 편리하고, 마지막에 "Other" 옵션이 자동 추가되어 직접 입력도 가능하다.

**AskUserQuestion 사용 규칙:**
- 선택지가 2개 이상인 질문은 **반드시** AskUserQuestion을 사용한다 (텍스트로 나열하지 않는다)
- 각 선택지의 `description`에 MS Docs URL이나 참고 정보를 포함한다
- 추천 옵션이 있으면 첫 번째에 놓고 label 끝에 `(Recommended)` 를 붙인다
- 한 번에 최대 4개 질문까지 묶을 수 있다 — 관련 있는 질문은 한 번에 묻는다
- 선택지는 2~4개로 제한된다. 5개 이상이면 가장 일반적인 3~4개를 선택지로 넣고 나머지는 "Other"로 직접 입력하도록 유도한다
- `multiSelect: true`로 복수 선택이 필요한 항목도 처리 가능 (예: 여러 모델 동시 선택)

**AskUserQuestion 사용 대상 항목:**
- 배포 위치 (region) 선택
- SKU/티어 선택
- 모델 선택 (채팅 모델, 임베딩 모델 등)
- 네트워킹 방식 선택
- 구독 선택 (Phase 1 Step 2)
- 리소스 그룹 선택 (Phase 1 Step 3)
- 그 외 사용자에게 선택을 구하는 모든 질문

**사용 예시:**
```
// 프로젝트 이름은 자유 입력이므로 AskUserQuestion 사용하지 않음 (텍스트로 질문)
// SKU, region 등 선택지가 있는 항목은 AskUserQuestion 사용:

AskUserQuestion({
  questions: [
    {
      question: "AI Search의 SKU를 선택해주세요. 참고: https://learn.microsoft.com/en-us/azure/search/search-sku-tier",
      header: "Search SKU",
      options: [
        { label: "Basic", description: "개발/테스트용. 최대 15개 인덱스. ..." },
        { label: "Standard S1 (Recommended)", description: "운영 환경 권장. ..." },
        { label: "Standard S2", description: "고트래픽 운영 환경. ..." },
        { label: "Free", description: "무료 체험. 50MB 스토리지 ..." }
      ],
      multiSelect: false
    },
    {
      question: "배포할 Azure 리전을 선택해주세요. 참고: https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models",
      header: "Region",
      options: [
        { label: "Korea Central (Recommended)", description: "한국 리전. 대부분 서비스 지원" },
        { label: "East US", description: "미국 동부. 모든 AI 모델 지원" },
        { label: "Japan East", description: "일본 동부. 한국 근접" }
      ],
      multiSelect: false
    }
  ]
})
```

> **주의**: 위 예시의 SKU, 리전, description 값은 설명용이다. 실제 질문 시에는 MS Docs를 WebFetch로 조회하여 최신 정보 기반으로 선택지를 동적으로 구성한다. 하드코딩하지 않는다.

**예시 — 사용자 입력이 부족한 경우:**
```
사용자: "RAG 챗봇 만들고 싶어. Foundry에 GPT 모델이랑 AI Search 쓸 거야."

→ 확정된 것: Microsoft Foundry, Azure AI Search
→ 아직 미확정: 프로젝트명, 구체적 모델명, 임베딩 모델, 네트워킹(PE?), SKU, 배포 위치

Claude는 가장 먼저 프로젝트 이름을 AskUserQuestion으로 확인한다 (기본값: rag-chatbot).
이후 각 미확정 항목도 AskUserQuestion 도구로 선택지를 제공한다.
선택지의 description에 MS Docs URL을 포함하여 사용자가 직접 참고할 수 있도록 한다.
```

모든 항목이 확정되면 다이어그램을 생성하고 아래 형식으로 보여준다:

**다이어그램 완성 후 보고 형식:**
```
## 아키텍처 다이어그램

[인터랙티브 다이어그램 링크]

**확정된 구성:**
- [사용자 요구사항에 따라 확정된 서비스 목록 나열]

**위치**: [확정된 region]

바꾸거나 추가할 부분 있으면 말씀해주세요.
```

### 1-2. 인터랙티브 HTML 다이어그램 생성

`generate_html_diagram.py`를 실행하여 인터랙티브 HTML 다이어그램을 만든다.
스크립트 경로는 설치 위치에 따라 다르므로 아래처럼 동적으로 찾는다.

**다이어그램 파일명 규칙:**

모든 다이어그램은 Bicep 프로젝트 폴더(`<project-name>/`) 안에 생성한다.
각 단계별로 번호를 붙여 체계적으로 관리하며, 이전 단계 파일은 덮어쓰지 않는다.

| 단계 | 파일명 | 생성 시점 |
|------|--------|-----------|
| Phase 1 설계 초안 | `01_arch_diagram_draft.html` | 아키텍처 설계 확정 시 |
| Phase 4 What-if 프리뷰 | `02_arch_diagram_preview.html` | What-if 검증 후 |
| Phase 4 배포 결과 | `03_arch_diagram_result.html` | 실제 배포 완료 후 |

**스크립트 경로 탐색 — 아래 순서로 찾는다:**
```bash
# 1순위: 프로젝트 로컬 스킬 폴더
DIAGRAM_SCRIPT=$(find .claude/skills/azure-arch-builder -name "generate_html_diagram.py" 2>/dev/null | head -1)
# 2순위: 글로벌 스킬 폴더
if [ -z "$DIAGRAM_SCRIPT" ]; then
  DIAGRAM_SCRIPT=$(find ~/.claude/skills/azure-arch-builder -name "generate_html_diagram.py" 2>/dev/null | head -1)
fi
OUTPUT_FILE="<project-name>/01_arch_diagram_draft.html"
python "$DIAGRAM_SCRIPT" \
  --services '<JSON>' \
  --connections '<JSON>' \
  --title "아키텍처 제목" \
  --output "$OUTPUT_FILE"

# 생성 후 자동으로 브라우저에서 열기 (OS 자동 감지)
if command -v open &>/dev/null; then
  open "$OUTPUT_FILE"                        # macOS
elif command -v wslview &>/dev/null; then
  wslview "$OUTPUT_FILE"                     # WSL2 (wslu 패키지)
elif command -v explorer.exe &>/dev/null; then
  explorer.exe "$(wslpath -w "$OUTPUT_FILE" 2>/dev/null || echo "$OUTPUT_FILE")"  # WSL2 fallback
elif command -v xdg-open &>/dev/null; then
  xdg-open "$OUTPUT_FILE"                   # Linux
elif command -v start &>/dev/null; then
  start "$OUTPUT_FILE"                       # Git Bash on Windows
fi
```

> **🚨 다이어그램 자동 오픈 (예외 없음)**: `generate_html_diagram.py`로 HTML 파일을 생성하면 **어떤 상황이든 반드시** 브라우저에서 자동으로 연다. 이유를 불문하고, 다이어그램이 (재)생성되면 무조건 `open`/`xdg-open`/`wslview`/`start` 명령을 실행한다. 다이어그램 생성과 브라우저 오픈은 항상 하나의 bash 명령 블록 안에서 함께 실행한다.
>
> **적용 시점 (이것뿐 아니라, HTML 다이어그램이 생성되는 모든 시점):**
> - Phase 1 설계 초안 (`01_arch_diagram_draft.html`)
> - Delta Confirmation 후 다이어그램 재생성
> - Phase 4 What-if 프리뷰 (`02_arch_diagram_preview.html`)
> - Phase 4 배포 결과 (`03_arch_diagram_result.html`)
> - 배포 후 아키텍처 변경 (`04_arch_diagram_update_draft.html`)
> - 그 외 어떤 이유로든 다이어그램이 재생성되는 경우

**services JSON 형식:**

사용자의 확정된 서비스 목록에 따라 동적으로 구성한다. 아래는 JSON 구조 설명이다.

```json
[
  {"id": "고유ID", "name": "서비스 표시명", "type": "아이콘타입", "sku": "SKU", "private": true/false,
   "details": ["상세 정보 줄1", "상세 정보 줄2"]}
]
```

사용 가능한 type 값: `ai_foundry`, `ai_hub`, `openai`, `search`, `storage`, `keyvault`, `fabric`, `vm`, `bastion`, `vpn`, `adf`, `pe` 등 (generate_html_diagram.py의 SERVICE_ICONS 참조)

**Private Endpoint 사용 시 — PE 노드 추가 필수:**

Private Endpoint가 포함된 아키텍처라면, 각 서비스마다 PE 노드를 services JSON에 반드시 추가하고 connections에도 연결을 넣어야 다이어그램에 표시된다.

```json
// 각 서비스에 대응하는 PE 노드 추가
{"id": "pe_서비스ID", "name": "PE: 서비스명", "type": "pe", "details": ["groupId: 해당그룹ID"]}

// connections에 서비스 → PE 연결 추가
{"from": "서비스ID", "to": "pe_서비스ID", "label": "", "type": "private"}
```

PE의 groupId는 서비스별로 다르다. `references/service-gotchas.md`의 PE groupId & DNS Zone 매핑 테이블을 참조한다.

> **서비스 명칭 규칙**: 반드시 최신 Azure 공식 명칭을 사용한다. 명칭이 확실하지 않으면 MS Docs를 확인한다.
> 서비스별 리소스 타입과 핵심 속성은 `references/domain-packs/ai-data.md`를 참조한다.

**connections JSON 형식:**
```json
[
  {"from": "서비스A_ID", "to": "서비스B_ID", "label": "연결 설명", "type": "api|data|security|private"}
]
```

생성된 HTML 파일을 computer:// 링크로 사용자에게 제공한다.

### 1-3. 대화를 통한 아키텍처 확정

아키텍처는 사용자와 대화하며 점진적으로 확정한다. 사용자가 변경을 요청하면 처음부터 다시 묻지 않고, **현재까지 확정된 상태를 기반으로 요청된 부분만 반영**해서 다이어그램을 재생성한다.

**⚠️ Delta Confirmation Rule — 서비스 추가/변경 시 필수 확인:**

서비스 추가/변경은 "단순 반영"이 아니라, **해당 서비스의 미확정 필수 필드를 다시 여는 이벤트**다.

**프로세스:**
1. 기존 확정 상태 + 새 요청을 diff한다
2. 새로 추가된 서비스의 required fields를 식별한다 (`domain-packs` 또는 MS Docs 참조)
3. MS Docs에서 해당 서비스의 리전 가용성/선택지를 fetch한다
4. required fields가 하나라도 미확정이면 **AskUserQuestion으로 먼저 확인**한다
5. **확인 완료 후에만** 다이어그램을 재생성한다

**절대 하지 말 것:**
- 미확정 필수 항목이 남은 채로 다이어그램을 확정 업데이트하는 것
- 사용자가 언급하지 않은 하위 구성요소/워크로드를 임의로 추가하는 것 (예: Fabric 요청에 OneLake, 데이터 파이프라인을 자동 추가)
- SKU/모델을 임의로 가정하여 "F SKU"처럼 모호하게 넣는 것

**이미 확정된 서비스의 설정은 다시 묻지 않는다.** 새로 추가/변경된 서비스의 미확정 항목만 확인한다.

---

**🚨🚨🚨 [최우선 원칙] 설계 단계 즉시 팩트 체크 🚨🚨🚨**

**Phase 1의 존재 이유는 "실현 가능한 아키텍처"를 확정하는 것이다.**
**사용자가 무엇을 요청하든, 다이어그램에 반영하기 전에 반드시 MS Docs를 WebFetch로 직접 조회하여 그것이 실제로 가능한지 팩트 체크한다.**

**설계 방향 vs 배포 스펙 — 정보 경로 분리:**

| 판단 유형 | 참조 경로 | 예시 |
|----------|----------|------|
| **설계 방향** (아키텍처 패턴, best practice, 서비스 조합) | `references/architecture-guidance-sources.md` → targeted fetch | "RAG 권장 구조는?", "enterprise baseline은?" |
| **배포 스펙** (API version, SKU, region, model, PE mapping) | `references/azure-dynamic-sources.md` → MS Docs fetch | "API version 뭐야?", "이 모델 Korea Central에서 되나?" |

- **설계 방향은 architecture guidance, 실제 배포값은 dynamic sources.** 이 두 경로를 혼용하지 않는다.
- Architecture guidance 문서의 내용으로 SKU/API version/region을 결정하지 않는다.
- **매 요청마다 Architecture Center 하위 문서를 싹 다 뒤지지 않는다.** 트리거 기반으로 관련 문서 최대 2개만 targeted fetch한다.
- 트리거/fetch budget/질문 유형별 decision rule은 `architecture-guidance-sources.md`를 참조한다.

**이 원칙은 예외 없이 모든 요청에 적용된다:**
- 모델 추가/변경 → MS Docs에서 해당 모델이 존재하는지, 해당 리전에서 배포 가능한지 확인
- 서비스 추가/변경 → MS Docs에서 해당 서비스가 해당 리전에서 사용 가능한지 확인
- SKU 변경 → MS Docs에서 해당 SKU가 유효한지, 원하는 기능을 지원하는지 확인
- 기능 요청 → MS Docs에서 해당 기능이 실제로 지원되는지 확인
- 서비스 조합 → MS Docs에서 서비스 간 연동이 가능한지 확인
- **그 외 어떤 요청이든** → MS Docs에서 팩트 체크

**MS Docs 확인 결과:**
- **가능** → 다이어그램에 반영
- **불가능** → 즉시 사용자에게 불가 사유를 설명하고, 가능한 대안을 제시

**팩트 체크 프로세스 — 이중 검증 필수:**

사용자의 요청에 대해 단순히 한 번 조회하고 끝내지 않는다.
**반드시 서브에이전트를 활용한 이중 검증을 수행한다.**

```
[1차 검증] 메인 에이전트가 MS Docs를 WebFetch로 직접 조회
    ↓
[2차 검증] 서브에이전트(Agent 도구)를 띄워서 동일 항목을 독립적으로 재검증
    - 서브에이전트는 다른 MS Docs 페이지나 관련 페이지를 추가 조회
    - 1차 검증 결과와 대조하여 불일치가 있으면 플래그
    ↓
[결과 종합] 두 검증 결과가 일치하면 사용자에게 답변
    - 불일치 시: 추가 조회로 해소하거나, 불확실한 부분을 사용자에게 솔직히 알림
```

**팩트 체크 품질 기준 — 대충 보지 말고 꼼꼼하게:**
- MS Docs 페이지를 fetch했으면 **모든 관련 섹션, 탭, 조건을 빠짐없이 확인**한다
- 모델 가용성 확인 시: Global Standard, Standard, Provisioned, Data Zone 등 **모든 배포 타입**을 확인한다. 하나의 배포 타입만 보고 "미지원"이라고 판단하지 않는다
- SKU 확인 시: 해당 SKU에서 지원하는 기능 목록을 **전부** 확인한다
- 페이지가 크면 관련 섹션을 **여러 번 fetch**해서라도 정확하게 파악한다
- 확신이 없으면 추가 페이지를 더 조회한다. **추측으로 답하지 않는다**

**절대 하지 말아야 할 것:**
- 확인 없이 다이어그램에 일단 넣기
- "Bicep 생성 시 확인할게요", "배포 시 검증됩니다" 같은 검증 미루기
- 자기 기억에만 의존해서 "될 겁니다"라고 답하기 — **반드시 MS Docs를 직접 조회**
- MS Docs를 fetch하고도 일부만 보고 성급하게 결론 내리기
- 1차 조회만으로 확정짓기 — **반드시 이중 검증**

**🚫 서브에이전트 사용 규칙:**

**포그라운드 vs 백그라운드 판단 기준:**
- **결과가 있어야 다음 단계를 진행할 수 있는 경우 → 포그라운드 (기본값)**
  - 예: SKU 목록 조회 후 사용자에게 선택지 제공, 모델 가용성 확인 후 다이어그램 반영
  - 이 경우 백그라운드로 돌리면 결과를 기다리며 사용자를 멍하게 방치하게 된다
- **결과를 기다리는 동안 독립적으로 할 수 있는 다른 작업이 있는 경우 → 백그라운드**
  - 예: 1차 검증을 직접 하면서 동시에 2차 검증 서브에이전트를 백그라운드로 실행

**대부분의 팩트 체크는 포그라운드로 실행한다.** 결과 없이 다음 질문을 할 수 없기 때문이다.

**이중 검증 시 병렬 실행 방법:**
```
// 1차 검증 (메인)과 2차 검증 (서브에이전트)을 동시에 실행
// → 같은 메시지에서 WebFetch와 Agent를 함께 호출
[메인] WebFetch로 MS Docs 직접 조회 (1차)
[동시에] Agent({ prompt: "...", run_in_background: true }) (2차)
// 1차 결과를 먼저 정리하고, 2차 알림이 오면 대조
```

**절대 하지 말 것:**
- 결과가 필요한데 백그라운드로 돌리고 아무것도 안 하며 대기하는 것
- `/private/tmp/claude-*` 등 내부 temp 파일을 `tail`, `cat`, `python3`으로 읽기
- `sleep` + `tail` / `wc -l` 로 서브에이전트 output 파일을 반복 체크
- 내부 JSONL 파일을 파싱하여 결과를 직접 추출

---

**⚠️ 중요: 어떤 bash 명령도 사용자가 명시적으로 다음 단계 진행을 승인하기 전까지 절대 실행하지 않는다.**
단, 위 팩트 체크를 위한 MS Docs WebFetch는 예외적으로 허용한다.

아키텍처가 확정되면 다음 단계 진행 여부를 먼저 사용자에게 묻는다:
```
아키텍처가 확정되었습니다! 다음 단계로 진행할까요?

✅ 확정된 아키텍처: [요약]

다음 순서로 진행됩니다:
1. [Bicep 코드 생성] — AI가 자동으로 IaC 코드 작성
2. [코드 리뷰] — 보안/모범사례 자동 검토
3. [Azure 배포] — 실제 리소스 생성 (선택)

진행할까요? (배포 없이 코드만 받고 싶으면 말씀해주세요)
```

사용자가 진행 승인하면 아래 순서로 정보를 수집한다.

**Step 1: Azure 로그인 확인**

```bash
az account show 2>&1
```

- 로그인 되어 있으면 → Step 2로 이동
- 로그인 안 되어 있으면 → 사용자에게 안내:
  ```
  Azure CLI 로그인이 필요합니다. 터미널에서 아래 명령어를 실행해주세요:
  az login
  완료 후 다시 말씀해주세요.
  ```

**Step 2: 구독 선택**

```bash
az account list --output json
```

조회된 구독 목록에서 최대 4개를 `AskUserQuestion`의 선택지로 제공한다.
5개 이상이면 자주 쓰는 구독 3~4개를 선택지로 넣고, 나머지는 "Other"로 직접 입력하도록 한다.
사용자가 선택하면 `az account set --subscription "<ID>"` 실행.

**Step 3: 리소스 그룹 확인**

```bash
az group list --output json
```

기존 리소스 그룹 목록에서 최대 4개를 `AskUserQuestion`의 선택지로 제공한다.
사용자가 기존 그룹을 선택하면 그대로 사용하고, "Other"로 새 이름을 입력하면 Phase 4 배포 시 생성한다.

**필수 확정 항목:**
- [ ] 서비스 목록 및 SKU
- [ ] 네트워킹 방식 (Private Endpoint 여부)
- [ ] 구독 ID (Step 2에서 확정)
- [ ] 리소스 그룹 이름 (Step 3에서 확정)
- [ ] 위치 (사용자에게 확인 — 서비스별 지역 가용성은 MS Docs에서 검증)

---

## PHASE 2: Bicep 생성 에이전트

사용자가 진행에 동의하면 `agents/bicep-generator.md` 지침을 읽고 Bicep 템플릿을 생성한다.
또는 별도 서브에이전트로 위임할 수 있다.

**민감 정보 처리 원칙 (절대 어기지 말 것):**
- VM 비밀번호, API 키 등 민감 값은 채팅에서 물어보지도, 파라미터 파일에 저장하지도 않는다
- VM이 포함된 경우 `main.bicepparam`에 `vmAdminPassword` 없이 생성하고, 배포 시 전달 방법을 안내한다:
  ```
  VM 관리자 비밀번호는 배포 시 직접 입력하세요:
  az deployment group create ... --parameters vmAdminPassword='원하는비밀번호'
  ```
- 코드 리뷰 시 `main.bicepparam`에 민감 값이 평문으로 있으면 즉시 제거한다

**MS Docs fetch 실패 시 처리:**
- rate limit 등으로 WebFetch가 실패하면 사용자에게 반드시 알린다:
  ```
  ⚠️ MS Docs API 버전 조회에 실패했습니다. 알려진 마지막 stable 버전으로 생성합니다.
  배포 전 실제 최신 버전 확인을 권장합니다.
  계속 진행할까요?
  ```
- 사용자 승인 없이 조용히 하드코딩 버전으로 진행하지 않는다

**Bicep 생성 전 참고 파일:**
- `references/service-gotchas.md` — 필수 속성, 흔한 실수, PE groupId/DNS Zone 매핑
- `references/domain-packs/ai-data.md` — AI/Data 서비스 구성 가이드 (v1 도메인)
- `references/azure-common-patterns.md` — PE/보안/명명 공통 패턴
- `references/azure-dynamic-sources.md` — MS Docs URL 레지스트리 (API version fetch용)
- 위 파일에 없는 서비스는 MS Docs를 직접 fetch하여 리소스 타입, 속성, PE 매핑을 확인한다

**출력 구조:**
```
<project-name>/
├── main.bicep              # 메인 오케스트레이션
├── main.bicepparam         # 파라미터 (환경별 값)
└── modules/
    ├── network.bicep       # VNet, Subnet (private endpoint subnet 포함)
    ├── ai.bicep            # AI 서비스 (사용자 요구에 따라 구성)
    ├── storage.bicep       # ADLS Gen2 (isHnsEnabled: true)
    ├── fabric.bicep        # Microsoft Fabric (필요 시)
    ├── keyvault.bicep      # Key Vault
    └── private-endpoints.bicep  # 모든 PE + DNS Zone
```

**Bicep 필수 원칙:**
- 모든 리소스명 파라미터화 — `param openAiName string = 'oai-${uniqueString(resourceGroup().id)}'`
- Private 서비스는 반드시 `publicNetworkAccess: 'Disabled'`
- pe-subnet에 `privateEndpointNetworkPolicies: 'Disabled'` 설정
- Private DNS Zone + VNet Link + DNS Zone Group 3종 세트 필수
- Microsoft Foundry 사용 시 **Foundry Project (`accounts/projects`) 반드시 함께 생성** — 없으면 포털 사용 불가
- ADLS Gen2는 반드시 `isHnsEnabled: true` (빠트리면 일반 Blob Storage가 됨)
- 비밀값은 Key Vault에 저장, `@secure()` 파라미터로 참조
- 한국어 주석으로 각 섹션 목적 설명

생성 완료 후 Phase 3로 즉시 전환한다.

---

## PHASE 3: Bicep 리뷰 에이전트

`agents/bicep-reviewer.md` 지침에 따라 검토한다.

**⚠️ 핵심: 눈으로만 보고 "통과"라고 하지 않는다. 반드시 `az bicep build`를 실행하여 실제 컴파일 결과를 확인한다.**

```bash
az bicep build --file main.bicep 2>&1
```

1. 컴파일 에러/경고 → 수정
2. 체크리스트 검토 → 수정
3. 재컴파일로 확인
4. 결과 보고 (컴파일 결과 포함)

상세 체크리스트와 수정 절차는 `agents/bicep-reviewer.md` 참조.

리뷰 완료 후 Phase 4로 전환하기 전 사용자에게 결과를 보여준다.

---

## PHASE 4: 배포 에이전트

**전제조건 확인 먼저:**
```bash
# az CLI 설치 및 로그인 확인
az account show 2>&1
```

로그인이 안 되어 있으면 사용자에게 `az login` 실행을 요청한다.
Claude가 직접 자격증명을 입력하거나 저장하지 않는다.

**배포 단계 (각 단계마다 사용자에게 확인):**

### 단계 1: 리소스 그룹 생성
```bash
az group create --name "<RG_NAME>" --location "<LOCATION>"  # Phase 1에서 확정한 위치
```
→ 성공 확인 후 다음 단계 진행

### 단계 2: What-if 검증 (실제 변경 없음)
```bash
az deployment group what-if \
  --resource-group "<RG_NAME>" \
  --template-file main.bicep \
  --parameters main.bicepparam
```
→ What-if 결과를 요약해서 사용자에게 보여준다.

### 단계 3: What-if 결과 기반 다이어그램 재생성

What-if가 성공하면, 실제 배포 예정 리소스 목록(리소스명, 타입, 위치, 수량)으로 다이어그램을 재생성한다.
Phase 1에서 그린 초안(`01_arch_diagram_draft.html`)은 그대로 두고, 프리뷰를 `02_arch_diagram_preview.html`로 생성한다.
초안은 언제든 다시 열어볼 수 있다.

```
## 배포 예정 아키텍처 (What-if 기반)

[인터랙티브 다이어그램 링크 — 02_arch_diagram_preview.html]
(설계 초안: 01_arch_diagram_draft.html)

생성될 리소스 (N개):
[What-if 결과 요약 테이블]

이 리소스들을 배포할까요? (예/아니오)
```

사용자가 확인하면:
```bash
az deployment group create \
  --resource-group "<RG_NAME>" \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --name "deploy-$(date +%Y%m%d-%H%M%S)" \
  2>&1 | tee deployment.log
```

배포 중 진행 상황을 주기적으로 모니터링:
```bash
az deployment group show \
  --resource-group "<RG_NAME>" \
  --name "<DEPLOYMENT_NAME>" \
  --query "{status:properties.provisioningState, duration:properties.duration}" \
  -o table
```

### 배포 실패 시 처리

배포가 실패하면 일부 리소스가 'Failed' 상태로 남을 수 있다. 이 상태에서 재배포하면 `AccountIsNotSucceeded` 같은 에러가 발생한다.

**⚠️ 리소스 삭제는 파괴적 명령이다. 반드시 사용자에게 상황을 설명하고 승인을 받은 후 실행한다.**

```
배포 중 [리소스명]이 실패했습니다.
재배포하려면 실패한 리소스를 먼저 삭제해야 합니다.

삭제 후 재배포할까요? (예/아니오)
```

사용자가 승인하면 실패한 리소스를 삭제하고 재배포한다.

### 단계 5: 배포 완료 — 실제 리소스 기반 다이어그램 생성 및 보고

배포가 완료되면 실제 배포된 리소스를 조회하여 최종 아키텍처 다이어그램을 생성한다.

**Step 1: 배포된 리소스 조회**
```bash
az resource list --resource-group "<RG_NAME>" --output json
```

**Step 2: 실제 리소스 기반 다이어그램 생성**

조회 결과에서 리소스명, 타입, SKU, 엔드포인트를 추출하여 `generate_html_diagram.py`로 최종 다이어그램을 생성한다.
이전 다이어그램을 덮어쓰지 않도록 파일명에 주의한다:
- `01_arch_diagram_draft.html` — 설계 초안 (유지)
- `02_arch_diagram_preview.html` — What-if 프리뷰 (유지)
- `03_arch_diagram_result.html` — 배포 결과 최종본

다이어그램의 services JSON은 실제 배포된 리소스 정보로 채운다:
- `name`: 실제 리소스 이름 (예: `foundry-duru57kxgqzxs`)
- `sku`: 실제 SKU
- `details`: 엔드포인트, 위치 등 실제 값

**Step 3: 보고**
```
## 배포 완료!

[인터랙티브 아키텍처 다이어그램 — 03_arch_diagram_result.html]
(설계 초안: 01_arch_diagram_draft.html | What-if 프리뷰: 02_arch_diagram_preview.html)

생성된 리소스 (N개):
[실제 배포 결과에서 리소스명, 타입, 엔드포인트를 동적으로 추출하여 나열]

## 다음 단계
1. Azure Portal에서 리소스 확인
2. Private Endpoint 연결 상태 확인
3. 필요 시 추가 구성 안내

## 정리 명령어 (필요 시)
az group delete --name <RG_NAME> --yes --no-wait
```

---

### 배포 완료 후 아키텍처 변경 요청 처리

**배포가 완료된 상태에서 사용자가 리소스 추가/변경/삭제를 요청하면, Bicep/배포로 바로 가지 않는다.**
반드시 Phase 1로 돌아가 아키텍처를 먼저 업데이트한다.

**프로세스:**

1. **사용자 의도 확인** — 기존 배포된 아키텍처에 추가하는 것인지 먼저 묻는다:
   ```
   현재 배포된 아키텍처에 VM을 추가하시겠습니까?
   기존 구성: [배포된 서비스 요약]
   ```

2. **Phase 1 복귀 — Delta Confirmation Rule 적용**
   - 기존 배포 결과(`03_arch_diagram_result.html`)를 현재 상태 기준선으로 사용
   - 새 서비스의 required fields 확인 (SKU, 네트워킹, region 가용성 등)
   - AskUserQuestion으로 미확정 항목 확인
   - 팩트 체크 (MS Docs fetch + 이중 검증)

3. **업데이트된 아키텍처 다이어그램 생성**
   - 기존 배포 리소스 + 새 리소스를 합쳐서 `04_arch_diagram_update_draft.html` 생성
   - 사용자에게 보여주고 확정 받기:
   ```
   ## 업데이트된 아키텍처

   [인터랙티브 다이어그램 — 04_arch_diagram_update_draft.html]
   (이전 배포 결과: 03_arch_diagram_result.html)

   **변경 사항:**
   - 추가: [새 서비스 목록]
   - 제거: [제거된 서비스 목록] (있을 경우)

   이 구성으로 진행할까요?
   ```

4. **확정 후 Phase 2 → 3 → 4 순서대로 진행**
   - 기존 Bicep에 incremental로 새 리소스 모듈 추가
   - 리뷰 → What-if → 배포 (incremental deployment)

**절대 하지 말 것:**
- 배포 완료 후 변경 요청에 아키텍처 다이어그램 업데이트 없이 바로 Bicep 생성으로 넘어가는 것
- 기존 배포 상태를 무시하고 새 리소스만 단독으로 만드는 것
- 사용자에게 "기존 아키텍처에 추가할지" 확인하지 않고 진행하는 것

---

## 빠른 참조

### 기본값

- **위치**: Phase 1에서 사용자와 확정. 서비스별 지역 가용성은 MS Docs에서 반드시 확인
- **네트워킹**: Private Endpoint 기본 적용
- **VNet CIDR**: 파라미터로 사용자에게 확인 (고객 환경 기존 주소공간 충돌 방지). 기본 제안: `10.0.0.0/16`, pe-subnet: `10.0.1.0/24`

### 참조 파일 (Stable vs Dynamic 분리 구조)

| 파일 | 역할 | 정보 성격 |
|------|------|----------|
| `references/azure-common-patterns.md` | PE/보안/명명 등 공통 패턴 | Stable |
| `references/azure-dynamic-sources.md` | MS Docs URL 레지스트리 (값 아닌 출처만) | Dynamic source |
| `references/architecture-guidance-sources.md` | 공식 아키텍처 가이던스 source registry (설계 방향 판단용) | Source registry |
| `references/service-gotchas.md` | 비직관적 필수 속성, 흔한 실수, PE 매핑 | Stable |
| `references/domain-packs/ai-data.md` | AI/Data 서비스 구성 가이드 (v1 도메인) | Stable + Decision Rules |
| `agents/bicep-generator.md` | Bicep 생성 규칙 + Fallback workflow | |
| `agents/bicep-reviewer.md` | 코드 리뷰 체크리스트 + 하드코딩 감지 | |

> **원칙**: Stable 정보는 reference 우선 참조. Dynamic 정보(API version, SKU, region, 모델)는 항상 MS Docs fetch.
