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

### 1-1. 초안 제안

사용자의 첫 요청을 받으면, 즉시 아키텍처 초안을 제안한다. 너무 많은 질문을 먼저 하지 말고,
합리적인 가정을 바탕으로 초안을 먼저 보여준 뒤 피드백을 받는 방식이 더 효과적이다.

**초안 제안 형식:**
```
## 이런 아키텍처를 생각하고 계신 건가요?

[서비스 구성 한 문장 요약]

**포함 서비스:**
- Azure AI Search (Standard SKU) — 문서 인덱싱 및 벡터 검색
- Azure OpenAI (gpt-4o + text-embedding-3-large) — 추론 및 임베딩
- ADLS Gen2 — 문서 스토리지
- Key Vault — 키/시크릿 관리
- VNet + Private Endpoint — 모든 서비스 네트워크 격리

**네트워킹**: Private Endpoint (모든 서비스)
**위치**: koreacentral
**예상 비용**: 월 약 $XXX~$XXX (사용량 따라 다름)

[인터랙티브 다이어그램 링크]

맞게 이해했나요? 추가하거나 바꾸고 싶은 부분 있으면 말씀해주세요.
```

### 1-2. 인터랙티브 HTML 다이어그램 생성

`generate_html_diagram.py`를 실행하여 인터랙티브 HTML 다이어그램을 만든다.
스크립트 경로는 설치 위치에 따라 다르므로 아래처럼 동적으로 찾는다.

**중요: `--output`은 반드시 `archi_diagram.html`로 고정한다. 절대 다른 이름을 사용하지 않는다.**

```bash
DIAGRAM_SCRIPT=$(find ~/.claude -name "generate_html_diagram.py" 2>/dev/null | head -1)
python "$DIAGRAM_SCRIPT" \
  --services '<JSON>' \
  --connections '<JSON>' \
  --title "아키텍처 제목" \
  --output "archi_diagram.html"
```

**services JSON 형식 (최신 Azure 서비스 명칭 사용):**
```json
[
  {"id": "openai", "name": "Azure OpenAI Service", "type": "openai", "sku": "S0", "private": true,
   "details": ["gpt-4o (30K TPM)", "text-embedding-3-large (120K TPM)"]},
  {"id": "foundry", "name": "Microsoft Foundry", "type": "ai_foundry", "sku": "S0 (AIServices)", "private": true,
   "details": ["kind: AIServices", "gpt-4o 배포", "text-embedding-3-large 배포"]},
  {"id": "foundry_project", "name": "Foundry Project", "type": "ai_hub", "sku": "Project", "private": true,
   "details": ["Foundry resource 하위 프로젝트", "에이전트/평가 작업 공간"]},
  {"id": "search", "name": "Azure AI Search", "type": "search", "sku": "Standard", "private": true,
   "details": ["Semantic Ranking 활성화", "벡터 검색 지원"]},
  {"id": "storage", "name": "Azure Data Lake Storage Gen2", "type": "storage", "sku": "Standard ZRS", "private": true,
   "details": ["Hierarchical Namespace", "raw/processed/curated 컨테이너"]},
  {"id": "kv", "name": "Azure Key Vault", "type": "keyvault", "sku": "Standard", "private": true,
   "details": ["RBAC 방식", "Soft Delete 90일"]}
]
```

> **서비스 명칭 및 아키텍처 규칙**: 반드시 최신 공식 명칭과 구조를 사용한다.
> - **Microsoft Foundry** = `Microsoft.CognitiveServices/accounts` + `kind: 'AIServices'` (최상위)
>   - 모델(gpt-4o 등)은 Foundry resource 레벨에서 배포, Project에서 공유 사용
>   - `allowProjectManagement: true` 없으면 Project 생성 불가
> - **Foundry Project** = `Microsoft.CognitiveServices/accounts/projects` (Foundry의 서브리소스)
> - **Azure OpenAI Service** (`kind: 'OpenAI'`) = 레거시. Foundry(AIServices)의 서브셋. 신규 개발 시 Microsoft Foundry 사용
> - **Hub 기반** (`Microsoft.MachineLearningServices`) = 레거시. ML/오픈소스 모델, Serverless API 필요 시에만
> - **Azure AI Search** — 정확한 명칭
> - **Azure Data Lake Storage Gen2** — 정확한 명칭 (ADLS Gen2)

**connections JSON 형식:**
```json
[
  {"from": "openai", "to": "search", "label": "벡터 검색", "type": "api"},
  {"from": "search", "to": "storage", "label": "문서 인덱싱", "type": "data"},
  {"from": "openai", "to": "kv", "label": "API Key 참조", "type": "security"}
]
```

생성된 HTML 파일을 computer:// 링크로 사용자에게 제공한다.

### 1-3. 대화를 통한 아키텍처 확정

사용자 피드백을 받을 때마다 다이어그램을 업데이트하고 새 링크를 제공한다.
서비스 목록과 네트워킹 방식이 확정되면 아래 순서로 나머지 정보를 수집한다.

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

**Step 3: 리소스 그룹 이름 확인**

사용자에게 직접 묻는다:
```
리소스 그룹 이름을 입력해주세요. (예: rg-rag-prod)
```

**필수 확정 항목:**
- [ ] 서비스 목록 및 SKU
- [ ] 네트워킹 방식 (Private Endpoint 여부)
- [ ] 구독 ID (Step 2에서 확정)
- [ ] 리소스 그룹 이름 (Step 3에서 확정)
- [ ] 위치 (기본: koreacentral)

**Phase 2로 전환 시 사용자에게 확인:**
```
아키텍처가 확정되었습니다! 다음 단계로 진행할까요?

✅ 확정된 아키텍처: [요약]

다음 순서로 진행됩니다:
1. [Bicep 코드 생성] — AI가 자동으로 IaC 코드 작성
2. [코드 리뷰] — 보안/비용/모범사례 자동 검토
3. [배포 확인] — 실제 Azure 배포 전 최종 확인
4. [Azure 배포] — 단계별 리소스 생성

진행할까요? (배포 없이 코드만 받고 싶으면 말씀해주세요)
```

---

## PHASE 2: Bicep 생성 에이전트

사용자가 진행에 동의하면 `agents/bicep-generator.md` 지침을 읽고 Bicep 템플릿을 생성한다.
또는 별도 서브에이전트로 위임할 수 있다.

**Bicep 생성 전 반드시 읽어야 할 파일:**
- `references/ai-data-services.md` — 서비스별 정확한 리소스 정의
- `references/private-endpoints.md` — Private Endpoint 패턴 및 DNS Zone 매핑

**출력 구조:**
```
<project-name>/
├── main.bicep              # 메인 오케스트레이션
├── main.bicepparam         # 파라미터 (환경별 값)
└── modules/
    ├── network.bicep       # VNet, Subnet (private endpoint subnet 포함)
    ├── ai.bicep            # OpenAI, AI Search, Microsoft Foundry
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
- [ ] Microsoft Foundry Hub: `kind: 'Hub'`, Project: `kind: 'Project'` 올바름
- [ ] OpenAI 모델 배포 apiVersion이 최신 stable 버전

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
→ What-if 결과를 요약해서 사용자에게 보여준다:
```
## 배포 예정 리소스 (What-if 결과)

생성될 리소스 (12개):
+ Microsoft.Network/virtualNetworks: vnet-prod-krc
+ Microsoft.CognitiveServices/accounts: oai-xxxx
+ Microsoft.Search/searchServices: srch-xxxx
...

예상 배포 시간: 약 15-20분
이 리소스들을 생성할까요? (예/아니오)
```

### 단계 3: 실제 배포
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

### 단계 4: 배포 완료 보고
```
## 배포 완료! 🎉

생성된 리소스 (12개):
✅ vnet-prod-krc (VNet)
✅ oai-xxxx (Azure OpenAI) — 엔드포인트: https://oai-xxxx.openai.azure.com/
✅ srch-xxxx (AI Search) — 엔드포인트: https://srch-xxxx.search.windows.net/
...

## 다음 단계
1. Azure Portal에서 리소스 확인
2. Key Vault에 연결 문자열 저장 (필요 시 도움 가능)
3. Private Endpoint 연결 상태 확인

## 정리 명령어 (필요 시)
az group delete --name <RG_NAME> --yes --no-wait
```

---

## 빠른 참조

### AI/Data 시나리오별 기본 구성

| 시나리오 | 서비스 조합 | Private Endpoint |
|---------|-----------|-----------------|
| RAG 챗봇 | Microsoft Foundry (AIServices) + Foundry Project + Azure AI Search + Azure Data Lake Storage Gen2 + Azure Key Vault | account, searchService, dfs/blob, vault |
| Microsoft Foundry (full) | Microsoft Foundry (AIServices) + Foundry Project + Azure AI Search + Azure Data Lake Storage Gen2 + Azure Key Vault | account, searchService, dfs, vault |
| Data Lakehouse | Microsoft Fabric + Azure Data Lake Storage Gen2 + Azure Data Factory + (Azure AI Search) | dfs, blob |
| ML Platform (레거시 Hub) | Azure AI Hub + Hub Project + Azure AI Search + Azure Data Lake Storage Gen2 + Azure Key Vault | amlworkspace, searchService, dfs, vault |

### 기본값

- **위치**: koreacentral (OpenAI는 eastus 또는 swedencentral)
- **네트워킹**: Private Endpoint 기본 적용
- **VNet CIDR**: 10.0.0.0/16, pe-subnet: 10.0.1.0/24
- **스토리지 이중화**: Standard_ZRS
- **Key Vault**: RBAC 방식, Soft Delete 90일, Purge Protection 활성화

### 비용 예상 가이드

| 구성 | 월 예상 비용 |
|-----|------------|
| OpenAI S0 + AI Search Standard | $100-$500+ (사용량) |
| Fabric F4 | ~$730/월 (항상 켜진 경우) |
| ADLS Gen2 (1TB) | ~$20/월 |
| Key Vault Standard | ~$5/월 |
| VNet + Private Endpoint | 소액 |
