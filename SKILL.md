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

**가장 먼저 프로젝트 이름을 확인한다:**
```
프로젝트 이름을 정해주세요. (입력하지 않으시면 azure-project 로 하겠습니다)
```
프로젝트 이름은 Bicep 출력 폴더명, 다이어그램 저장 경로, 배포 이름 등에 사용된다.

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

**예시 — 사용자 입력이 부족한 경우:**
```
사용자: "RAG 챗봇 만들고 싶어. Foundry에 GPT 모델이랑 AI Search 쓸 거야."

→ 확정된 것: Microsoft Foundry, Azure AI Search
→ 아직 미확정: 프로젝트명, 구체적 모델명, 임베딩 모델, 네트워킹(PE?), SKU, 배포 위치

Claude 질문 예시:
"몇 가지 확인할게요.
1. 프로젝트 이름을 정해주세요. (입력하지 않으시면 azure-project 로 하겠습니다)
2. 배포할 모델을 알려주세요. 임베딩 모델도 필요하신가요?
3. 네트워킹은 Private Endpoint로 모든 서비스 격리할까요, 아니면 퍼블릭도 허용할까요?
4. AI Search SKU는 어떤 걸로 할까요?
5. 배포 위치는 어디로 할까요?"
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
python "$DIAGRAM_SCRIPT" \
  --services '<JSON>' \
  --connections '<JSON>' \
  --title "아키텍처 제목" \
  --output "<project-name>/01_arch_diagram_draft.html"
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

---

**🚨🚨🚨 [최우선 원칙] 설계 단계 즉시 팩트 체크 🚨🚨🚨**

**Phase 1의 존재 이유는 "실현 가능한 아키텍처"를 확정하는 것이다.**
**사용자가 무엇을 요청하든, 다이어그램에 반영하기 전에 반드시 MS Docs를 WebFetch로 직접 조회하여 그것이 실제로 가능한지 팩트 체크한다.**

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

## 빠른 참조

### 기본값

- **위치**: Phase 1에서 사용자와 확정. 서비스별 지역 가용성은 MS Docs에서 반드시 확인
- **네트워킹**: Private Endpoint 기본 적용
- **VNet CIDR**: 10.0.0.0/16, pe-subnet: 10.0.1.0/24

### 참조 파일

서비스별 리소스 타입, 핵심 속성, SKU, PE 매핑 등 Azure 서비스 상세 정보는 아래 파일을 참조한다.
이 파일들의 정보도 오래될 수 있으므로, Bicep 생성 시에는 반드시 MS Docs를 fetch하여 최신 정보를 확인한다.

- `references/ai-data-services.md` — 서비스별 리소스 정의 및 핵심 속성
- `references/private-endpoints.md` — PE groupId 및 DNS Zone 매핑
- `agents/bicep-generator.md` — Bicep 생성 규칙 및 MS Docs URL 목록
- `agents/bicep-reviewer.md` — 코드 리뷰 체크리스트
