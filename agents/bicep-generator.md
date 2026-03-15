# Bicep Generator Agent

Phase 1에서 확정된 아키텍처 스펙을 받아 배포 가능한 Bicep 템플릿을 생성한다.

## Step 0: 최신 스펙 확인 (Bicep 생성 전 필수)

Bicep 코드에 API 버전을 하드코딩하지 않는다.
반드시 사용할 서비스의 MS Docs Bicep 레퍼런스를 fetch해서 최신 stable apiVersion을 확인 후 사용한다.

### 확인 방법
1. 사용할 서비스 목록 파악
2. 해당 서비스의 MS Docs URL fetch (WebFetch 도구 사용)
3. 페이지에서 최신 stable API 버전 확인
4. 해당 버전으로 Bicep 작성

### 서비스별 MS Docs URL

| 서비스 | MS Docs URL |
|--------|-------------|
| Microsoft Foundry / Azure OpenAI (CognitiveServices) | https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts |
| Azure AI Search | https://learn.microsoft.com/en-us/azure/templates/microsoft.search/searchservices |
| Storage Account (ADLS Gen2) | https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/storageaccounts |
| Key Vault | https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/vaults |
| Virtual Network | https://learn.microsoft.com/en-us/azure/templates/microsoft.network/virtualnetworks |
| Private Endpoints | https://learn.microsoft.com/en-us/azure/templates/microsoft.network/privateendpoints |
| Private DNS Zones | https://learn.microsoft.com/en-us/azure/templates/microsoft.network/privatednszones |
| Microsoft Fabric | https://learn.microsoft.com/en-us/azure/templates/microsoft.fabric/capacities |
| ADF | https://learn.microsoft.com/en-us/azure/templates/microsoft.datafactory/factories |
| Application Insights | https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/components |
| MachineLearningServices (Hub 기반 레거시) | https://learn.microsoft.com/en-us/azure/templates/microsoft.machinelearningservices/workspaces |

> **중요**: 위 URL을 WebFetch로 직접 조회하여 최신 stable apiVersion을 확인한다. 레퍼런스 파일이나 이전 대화에 있던 하드코딩된 버전을 그냥 쓰지 말 것.

> **에러/경고 발생 시에도 동일 원칙 적용**: what-if나 배포 중 API 버전 관련 에러가 발생하면, 에러 메시지에 포함된 버전을 "최신 버전"으로 믿고 바로 적용하지 않는다. 반드시 위 MS Docs URL을 다시 fetch하여 실제 최신 stable 버전을 확인한 후 수정한다.

---

## 사전 준비 (생성 전 반드시 읽기)

1. `references/ai-data-services.md` — 서비스별 정확한 리소스 정의 및 스니펫
2. `references/private-endpoints.md` — Private Endpoint + DNS Zone 패턴

## 입력 받는 정보

Phase 1 완료 시 다음 정보가 확정되어 있어야 한다:

```
- services: [서비스 목록 + SKU]
- networking: private_endpoint 여부
- resource_group: 리소스 그룹 이름
- location: 배포 위치 (기본: koreacentral)
- subscription_id: Azure 구독 ID
```

## 출력 파일 구조

```
<project-name>/
├── main.bicep              # 메인 오케스트레이션 — 모듈 호출 및 파라미터 전달
├── main.bicepparam         # 파라미터 파일 — 환경별 값, 민감 정보 제외
└── modules/
    ├── network.bicep           # VNet, Subnet (pe-subnet 포함)
    ├── ai.bicep                # AI 서비스 (사용자 요구에 따라 구성)
    ├── storage.bicep           # ADLS Gen2 (isHnsEnabled: true 필수)
    ├── fabric.bicep            # Microsoft Fabric Capacity (필요 시만)
    ├── keyvault.bicep          # Key Vault
    ├── monitoring.bicep        # Application Insights, Log Analytics (Microsoft Foundry 사용 시)
    └── private-endpoints.bicep # 모든 PE + Private DNS Zone + VNet Link + DNS Zone Group
```

## 모듈별 책임 범위

### `network.bicep`
- VNet (기본 CIDR: 10.0.0.0/16)
- pe-subnet (10.0.1.0/24) — `privateEndpointNetworkPolicies: 'Disabled'` 필수
- 추가 서브넷 필요 시 파라미터로 처리

### `ai.bicep`
- **Microsoft Foundry resource** (`Microsoft.CognitiveServices/accounts`, `kind: 'AIServices'`) — 최상위 AI 리소스
  - `allowProjectManagement: true` 필수
  - 모델 배포 (`Microsoft.CognitiveServices/accounts/deployments`) — Foundry resource 레벨에서 수행
- **Foundry Project** (`Microsoft.CognitiveServices/accounts/projects`) — Foundry resource의 서브리소스
- **Azure AI Search** — Semantic Ranking, 벡터 검색 설정
- ⚠️ Hub 기반(`Microsoft.MachineLearningServices/workspaces`)은 ML/오픈소스 모델 필요 시에만 사용. 일반 AI/RAG 구성은 Microsoft Foundry (AIServices) 사용

### `storage.bicep`
- ADLS Gen2: `isHnsEnabled: true` ← **절대 빠트리지 말 것**
- 컨테이너: raw, processed, curated (또는 요구사항에 맞게)
- `allowBlobPublicAccess: false`, `minimumTlsVersion: 'TLS1_2'`

### `keyvault.bicep`
- `enableRbacAuthorization: true` (액세스 정책 방식 사용 금지)
- `enableSoftDelete: true`, `softDeleteRetentionInDays: 90`
- `enablePurgeProtection: true`

### `monitoring.bicep`
- Log Analytics Workspace
- Application Insights (Hub 기반 구성에서만 필요 — Foundry AIServices는 불필요)

### `private-endpoints.bicep`
- 각 서비스마다 3종 세트:
  1. `Microsoft.Network/privateEndpoints` (pe-subnet에 배치)
  2. `Microsoft.Network/privateDnsZones` + VNet Link (`registrationEnabled: false`)
  3. `Microsoft.Network/privateEndpoints/privateDnsZoneGroups`
- 서비스별 DNS Zone 매핑은 `references/private-endpoints.md` 참조

## 필수 코딩 원칙

### 이름 규칙
```bicep
// uniqueString으로 충돌 방지 — 반드시 사용
param openAiName string = 'oai-${uniqueString(resourceGroup().id)}'
param searchName string = 'srch-${uniqueString(resourceGroup().id)}'
param storageName string = 'st${uniqueString(resourceGroup().id)}'  // 특수문자 불가
param keyVaultName string = 'kv-${uniqueString(resourceGroup().id)}'
```

### 네트워크 격리
```bicep
// Private Endpoint 사용 시 모든 서비스에 필수
publicNetworkAccess: 'Disabled'
networkAcls: {
  defaultAction: 'Deny'
  ipRules: []
  virtualNetworkRules: []
}
```

### 의존성 관리
```bicep
// 명시적 dependsOn 대신 리소스 참조로 암묵적 의존성 활용
resource aiProject '...' = {
  properties: {
    hubResourceId: aiHub.id  // aiHub 참조 → 자동으로 aiHub 먼저 배포됨
  }
}
```

### 보안
```bicep
// 민감 값은 Key Vault 참조 사용, 파라미터 파일에 평문 저장 금지
@secure()
param adminPassword string  // main.bicepparam에 평문 값 넣지 않음
```

### 한국어 주석
```bicep
// Microsoft Foundry resource — kind: 'AIServices'
// allowProjectManagement: true 없으면 Foundry Project 생성 불가
// apiVersion은 Step 0에서 fetch한 최신 버전으로 대체
resource foundry 'Microsoft.CognitiveServices/accounts@<Step 0에서 fetch한 버전>' = {
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true
    ...
  }
}
```

## main.bicep 기본 구조

```bicep
// ============================================================
// Azure [프로젝트명] 인프라 — main.bicep
// 생성일: [날짜]
// ============================================================

targetScope = 'resourceGroup'

// ── 공통 파라미터 ─────────────────────────────────────────
param location string = 'koreacentral'
param openAiLocation string = 'eastus'  // OpenAI 지역 제한
param projectPrefix string = 'prod'
param vnetAddressPrefix string = '10.0.0.0/16'
param peSubnetPrefix string = '10.0.1.0/24'

// ── 네트워크 ──────────────────────────────────────────────
module network './modules/network.bicep' = {
  name: 'deploy-network'
  params: {
    location: location
    vnetAddressPrefix: vnetAddressPrefix
    peSubnetPrefix: peSubnetPrefix
  }
}

// ── AI/Data 서비스 ────────────────────────────────────────
module ai './modules/ai.bicep' = {
  name: 'deploy-ai'
  params: {
    location: location
    openAiLocation: openAiLocation
  }
  dependsOn: [network]
}

// ── 스토리지 ──────────────────────────────────────────────
module storage './modules/storage.bicep' = {
  name: 'deploy-storage'
  params: {
    location: location
  }
}

// ── Key Vault ─────────────────────────────────────────────
module keyVault './modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  params: {
    location: location
  }
}

// ── Private Endpoint (모든 서비스) ────────────────────────
module privateEndpoints './modules/private-endpoints.bicep' = {
  name: 'deploy-private-endpoints'
  params: {
    location: location
    vnetId: network.outputs.vnetId
    peSubnetId: network.outputs.peSubnetId
    openAiId: ai.outputs.openAiId
    searchId: ai.outputs.searchId
    storageId: storage.outputs.storageId
    keyVaultId: keyVault.outputs.keyVaultId
  }
}

// ── 출력 ──────────────────────────────────────────────────
output vnetId string = network.outputs.vnetId
output openAiEndpoint string = ai.outputs.openAiEndpoint
output searchEndpoint string = ai.outputs.searchEndpoint
```

## main.bicepparam 기본 구조

```bicep
using './main.bicep'

param location = 'koreacentral'
param openAiLocation = 'eastus'
param projectPrefix = 'prod'
// 민감 값은 여기에 넣지 말 것 — Key Vault 참조 사용
```

## 자주 발생하는 실수 체크

| 항목 | 잘못된 예 | 올바른 예 |
|------|----------|----------|
| ADLS Gen2 HNS | `isHnsEnabled: false` (생략) | `isHnsEnabled: true` |
| PE 서브넷 정책 | 미설정 | `privateEndpointNetworkPolicies: 'Disabled'` |
| DNS Zone Group | PE만 생성 | PE + DNS Zone + VNet Link + DNS Zone Group |
| Microsoft Foundry resource | `kind: 'OpenAI'` 또는 MachineLearningServices 사용 | `kind: 'AIServices'` + `allowProjectManagement: true` |
| Foundry Project 미생성 | `allowProjectManagement` 누락 | `allowProjectManagement: true` 필수 |
| 레거시 Hub 사용 | `Microsoft.MachineLearningServices/workspaces` (일반 AI용) | Microsoft Foundry (AIServices) 사용 — Hub는 ML/오픈소스 모델 전용 |
| 공개 네트워크 | 설정 없음 | `publicNetworkAccess: 'Disabled'` |
| Storage 이름 | `st-my-storage` (하이픈 불가) | `stmystorage` 또는 `st${uniqueString(...)}` |
| 서비스 지역 제한 | 가용하지 않은 지역에 배포 | MS Docs에서 서비스별 가용 지역 확인 후 배포 |

## 생성 완료 후

Bicep 생성이 완료되면:
1. 생성된 파일 목록과 각 파일의 역할을 사용자에게 요약 보고
2. Phase 3 (Bicep Reviewer)로 즉시 전환
3. 리뷰어는 `agents/bicep-reviewer.md` 지침에 따라 자동 검토 및 수정 진행
