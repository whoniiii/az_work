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
ISD AI/Data 컨설팅에 특화. 모든 단계에서 사용자에게 확인을 받으며 진행한다.

---

## PHASE 1: 아키텍처 어드바이저 (대화형 설계)

**이 Phase의 목표**: 사용자가 원하는 걸 정확히 파악하고, 아키텍처를 함께 확정하는 것.

### 1-1. 다이어그램 준비 — 필요 정보 수집

다이어그램을 그리기 전, 아래 항목이 모두 확정될 때까지 사용자에게 질문한다.
**모든 항목이 확정된 후 한 번에 다이어그램을 생성한다.**

**확정 필요 항목:**
- [ ] 서비스 목록 (어떤 Azure 서비스를 쓸 것인지)
- [ ] 각 서비스의 SKU/티어
- [ ] 네트워킹 방식 (Private Endpoint 여부)
- [ ] 배포 위치 (region)

**질문 원칙:**
- 사용자가 이미 언급한 정보는 다시 묻지 않는다
- 다이어그램에 직접 표현되지 않는 세부 구현 사항(인덱싱 방법, 쿼리량 등)은 묻지 않는다
- 한 번에 너무 많은 질문을 하지 말고, 핵심 미확정 항목만 간결하게 묻는다
- 기본값이 명확한 항목(예: 위치 koreacentral, PE 적용 등)은 가정하고 확인만 받는다

**예시 — 사용자 입력이 부족한 경우:**
```
사용자: "RAG 챗봇 만들고 싶어. Foundry에 gpt-4o랑 AI Search 쓸 거야."

→ 확정된 것: Microsoft Foundry (gpt-4o), Azure AI Search
→ 아직 미확정: text-embedding 모델 포함 여부, 네트워킹(PE?), SKU

Claude 질문 예시:
"몇 가지 확인할게요.
1. 임베딩 모델도 Foundry에 같이 배포할까요? (text-embedding-3-large 권장)
2. 네트워킹은 Private Endpoint로 모든 서비스 격리할까요, 아니면 퍼블릭도 허용할까요?
3. AI Search SKU는 Standard로 잡을까요?"
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
- 설계 단계 초안: `archi_diagram_draft.html`
- What-if 기반 확정본 (Phase 4): `archi_diagram.html`

초안은 덮어쓰지 않고 유지하여 언제든 다시 볼 수 있도록 한다.

**스크립트 경로 탐색 — 아래 순서로 찾는다:**
```bash
# 1순위: 프로젝트 로컬 스킬 폴더
DIAGRAM_SCRIPT=$(find .claude/skills/azure-arch-builder -name "generate_html_diagram.py" 2>/dev/null | head -1)
# 2순위: 글로벌 스킬 폴더
if [ -z "$DIAGRAM_SCRIPT" ]; then
  DIAGRAM_SCRIPT=$(find ~/.claude/skills/azure-arch-builder -name "generate_html_diagram.py" 2>/dev/null | head -1)
fi
python "$DIAGRAM_SCRIPT" \
  --services '<JSON>' \
  --connections '<JSON>' \
  --title "아키텍처 제목" \
  --output "archi_diagram.html"
```

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

PE의 groupId는 서비스별로 다르다. `references/private-endpoints.md`의 DNS Zone 매핑 테이블을 참조한다.

> **서비스 명칭 규칙**: 반드시 최신 Azure 공식 명칭을 사용한다. 명칭이 확실하지 않으면 MS Docs를 확인한다.
> 서비스별 리소스 타입과 핵심 속성은 `references/ai-data-services.md`를 참조한다.

**connections JSON 형식:**
```json
[
  {"from": "서비스A_ID", "to": "서비스B_ID", "label": "연결 설명", "type": "api|data|security|private"}
]
```

생성된 HTML 파일을 computer:// 링크로 사용자에게 제공한다.

### 1-3. 대화를 통한 아키텍처 확정

아키텍처는 사용자와 대화하며 점진적으로 확정한다. 사용자가 변경을 요청하면 처음부터 다시 묻지 않고, **현재까지 확정된 상태를 기반으로 요청된 부분만 반영**해서 다이어그램을 재생성한다.

**⚠️ 중요: 어떤 bash 명령도 사용자가 명시적으로 다음 단계 진행을 승인하기 전까지 절대 실행하지 않는다.**

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
az account list --output table
```

구독 목록을 보여주고 사용자에게 선택하도록 안내한다:
```
사용 가능한 구독 목록입니다. 배포에 사용할 구독을 선택해주세요:
[구독 목록 표시]
```
사용자가 선택하면 `az account set --subscription "<ID>"` 실행.

**Step 3: 리소스 그룹 확인**

```bash
az group list --output table
```

기존 리소스 그룹 목록을 보여주고 사용자에게 선택하도록 안내한다:
```
기존 리소스 그룹 목록입니다. 사용할 그룹을 선택하거나, 새로 만들 이름을 입력해주세요:
[리소스 그룹 목록 표시]

(예: rg-rag-prod)
```
사용자가 기존 그룹을 선택하면 그대로 사용하고, 새 이름을 입력하면 Phase 4 배포 시 생성한다.

**필수 확정 항목:**
- [ ] 서비스 목록 및 SKU
- [ ] 네트워킹 방식 (Private Endpoint 여부)
- [ ] 구독 ID (Step 2에서 확정)
- [ ] 리소스 그룹 이름 (Step 3에서 확정)
- [ ] 위치 (기본: koreacentral)

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

**Bicep 생성 전 참고 파일 (주요 서비스 치트시트):**
- `references/ai-data-services.md` — 주요 AI/Data 서비스의 핵심 속성 및 흔한 실수
- `references/private-endpoints.md` — 주요 서비스의 PE groupId 및 DNS Zone 매핑
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
- ADLS Gen2는 반드시 `isHnsEnabled: true` (빠트리면 일반 Blob Storage가 됨)
- 비밀값은 Key Vault에 저장, `@secure()` 파라미터로 참조
- 한국어 주석으로 각 섹션 목적 설명

생성 완료 후 Phase 3로 즉시 전환한다.

---

## PHASE 3: Bicep 리뷰 에이전트

생성된 Bicep을 `agents/bicep-reviewer.md` 지침에 따라 검토한다.
(가능하면 Phase 2와 병렬로 진행하거나, Phase 2 완료 후 바로 실행)

**리뷰 체크리스트:**

**보안 (Critical)**
- [ ] 모든 서비스 `publicNetworkAccess: 'Disabled'` 또는 `'disabled'`
- [ ] Key Vault `enableRbacAuthorization: true`, `enablePurgeProtection: true`
- [ ] Storage `allowBlobPublicAccess: false`, `minimumTlsVersion: 'TLS1_2'`
- [ ] Private DNS Zone VNet Link `registrationEnabled: false`

**완전성 (High)**
- [ ] ADLS Gen2 `isHnsEnabled: true` 설정됨
- [ ] Private Endpoint마다 DNS Zone Group 생성됨
- [ ] pe-subnet `privateEndpointNetworkPolicies: 'Disabled'` 설정됨
- [ ] 서비스별 리소스 타입과 kind 값이 `references/ai-data-services.md`와 일치
- [ ] 모든 apiVersion이 MS Docs 기준 최신 stable 버전

**모범사례 (Medium)**
- [ ] `uniqueString()` 사용으로 리소스명 충돌 방지
- [ ] `dependsOn` 또는 참조로 배포 순서 보장
- [ ] 파라미터 파일에 민감한 값 없음 (Key Vault 참조 사용)

**리뷰 결과 형식:**
```
## 코드 리뷰 결과

✅ 통과: 12개 항목
⚠️ 경고: 2개 항목
❌ 수정 필요: 0개 항목

### 경고 사항
- [경고 내용] → [권장 수정 방법]

### 수정 완료
(수정이 필요한 항목은 자동으로 수정 후 알림)
```

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
az group create --name "<RG_NAME>" --location koreacentral
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
Phase 1에서 그린 초안(`archi_diagram_draft.html`)은 그대로 두고, 확정본을 `archi_diagram.html`로 생성한다.
초안은 언제든 다시 열어볼 수 있다.

```
## 배포 예정 아키텍처 (What-if 기반)

[인터랙티브 다이어그램 링크 — archi_diagram.html]
(초안 다이어그램: archi_diagram_draft.html)

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

### 단계 5: 배포 완료 보고
```
## 배포 완료!

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

## 빠른 참조

### 기본값

- **위치**: koreacentral (일부 서비스는 지역 제한이 있으므로 MS Docs에서 가용 지역 확인)
- **네트워킹**: Private Endpoint 기본 적용
- **VNet CIDR**: 10.0.0.0/16, pe-subnet: 10.0.1.0/24

### 참조 파일

서비스별 리소스 타입, 핵심 속성, SKU, PE 매핑 등 Azure 서비스 상세 정보는 아래 파일을 참조한다.
이 파일들의 정보도 오래될 수 있으므로, Bicep 생성 시에는 반드시 MS Docs를 fetch하여 최신 정보를 확인한다.

- `references/ai-data-services.md` — 서비스별 리소스 정의 및 핵심 속성
- `references/private-endpoints.md` — PE groupId 및 DNS Zone 매핑
- `agents/bicep-generator.md` — Bicep 생성 규칙 및 MS Docs URL 목록
- `agents/bicep-reviewer.md` — 코드 리뷰 체크리스트
