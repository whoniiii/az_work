# Azure AI/Data 서비스 레퍼런스

> **이 파일의 목적**: 자주 사용되는 AI/Data 서비스의 핵심 속성과 흔한 실수를 정리한 치트시트.
> **이 파일에 없는 서비스도 지원한다.** 없는 서비스는 MS Docs를 직접 확인하여 Bicep을 작성한다.
> API 버전은 하드코딩하지 않는다. Bicep 생성 전 반드시 MS Docs URL을 fetch하여 최신 stable apiVersion을 확인할 것.
> (`agents/bicep-generator.md` Step 0 참조)

## 목차
1. [Microsoft Foundry](#microsoft-foundry)
2. [Azure AI Search](#azure-ai-search)
3. [Microsoft Fabric](#microsoft-fabric)
4. [Azure Data Lake Storage Gen2 (ADLS Gen2)](#azure-data-lake-storage-gen2-adls-gen2)
5. [Azure Key Vault](#azure-key-vault)
6. [Azure Machine Learning (AML)](#azure-machine-learning-aml)
7. [Virtual Network / Private Endpoint](#virtual-network--private-endpoint)

---

## Microsoft Foundry

### 무엇인지
Azure AI 서비스의 최상위 리소스. 모델 배포, 프로젝트 관리, AI Search 연결 등 모든 AI 기능을 통합 관리한다.

### 계층 구조
```
Microsoft Foundry resource
└── Foundry Project (accounts/projects)
    └── Project assets (에이전트, 파일, 평가)
모델 배포 (accounts/deployments) — Foundry resource 레벨, Project에서 공유 사용
```

### 리소스 타입
- Foundry resource: `Microsoft.CognitiveServices/accounts`, `kind: 'AIServices'`
- Foundry Project: `Microsoft.CognitiveServices/accounts/projects`
- 모델 배포: `Microsoft.CognitiveServices/accounts/deployments`

### 핵심 속성 (빠뜨리면 안 되는 것들)
- `identity: { type: 'SystemAssigned' }` — **필수. 없으면 accounts/projects 생성 실패**
- `allowProjectManagement: true` — **없으면 Foundry Project 생성 불가**
- `customSubDomainName` — **필수** (엔드포인트 도메인 결정)
- `kind: 'AIServices'` — Foundry임을 나타내는 핵심 값. `'OpenAI'`와 혼동 금지
- `publicNetworkAccess: 'Disabled'` — Private Endpoint 사용 시 필수

### 레거시 주의
- **Azure OpenAI (`kind: 'OpenAI'`)**: 레거시. Foundry(`kind: 'AIServices'`)의 서브셋. 신규 개발에 사용 금지
- **Hub 기반 (`Microsoft.MachineLearningServices/workspaces`)**: 레거시. ML/오픈소스 모델, Serverless API, Managed compute가 명시적으로 필요한 경우에만 사용. 일반 AI/RAG 구성에는 Microsoft Foundry(AIServices) 사용

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource foundry 'Microsoft.CognitiveServices/accounts@<fetch로 확인>' = {
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'         // 필수 — 없으면 배포 실패
  }
  properties: {
    allowProjectManagement: true   // Foundry Project 생성 활성화 필수
    customSubDomainName: foundryName
    publicNetworkAccess: 'Disabled'
    ...
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@<fetch로 확인>' = {
  parent: foundry
  ...
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@<fetch로 확인>' = {
  parent: foundry
  ...
}
```

### MS Docs
- Foundry 개요: https://learn.microsoft.com/en-us/azure/ai-foundry/
- Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts

---

## Azure AI Search

### 무엇인지
벡터 검색, 시맨틱 랭킹, 풀텍스트 검색을 제공하는 검색 서비스. RAG 아키텍처의 핵심 컴포넌트.

### 리소스 타입
- `Microsoft.Search/searchServices`

### 핵심 속성 (빠뜨리면 안 되는 것들)
- `publicNetworkAccess: 'disabled'` — Private Endpoint 사용 시 필수
- `semanticSearch: 'free'` — Semantic Ranking 활성화 (standard 이상 SKU에서 사용 가능)
- `sku.name` — SKU 선택: `free` / `basic` / `standard` / `standard2` / `standard3`

### SKU 선택 기준
| SKU | 용도 |
|-----|------|
| free | 개발/테스트 (인덱스 3개, 50MB 제한) |
| basic | 소규모 프로덕션 |
| standard | 일반 프로덕션 (Semantic Ranking 지원) |
| standard2/3 | 대규모 프로덕션 |

> Private Endpoint는 basic 이상 SKU에서 지원

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource searchService 'Microsoft.Search/searchServices@<fetch로 확인>' = {
  sku: { name: 'standard' }
  properties: {
    publicNetworkAccess: 'disabled'
    semanticSearch: 'free'
    ...
  }
}
```

### MS Docs
- Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.search/searchservices

---

## Microsoft Fabric

### 무엇인지
통합 분석 플랫폼. OneLake 기반의 Lakehouse, Warehouse, Dataflow, Spark 등을 제공.

### 리소스 타입
- `Microsoft.Fabric/capacities`

### 핵심 속성 (빠뜨리면 안 되는 것들)
- `administration.members` — **관리자 이메일 필수** (없으면 배포 실패)
- `sku.name` — F SKU 선택: `F2` / `F4` / `F8` / `F16` / `F32` / `F64` 등
- `sku.tier: 'Fabric'` — 고정값

### Bicep 범위 제한
- **Bicep으로 프로비저닝 가능한 것**: Capacity만
- **Fabric Portal 또는 REST API로 별도 구성해야 하는 것**: Workspace, Lakehouse, Warehouse, Dataflow 등

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource fabricCapacity 'Microsoft.Fabric/capacities@<fetch로 확인>' = {
  sku: {
    name: 'F4'
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: [fabricAdminEmail]  // 관리자 이메일 필수
    }
  }
}
```

### MS Docs
- Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.fabric/capacities

---

## Azure Data Lake Storage Gen2 (ADLS Gen2)

### 무엇인지
계층적 네임스페이스(HNS)가 활성화된 Azure Storage Account. 빅데이터 분석, Spark, Fabric OneLake 연결에 사용.

### 리소스 타입
- `Microsoft.Storage/storageAccounts`, `kind: 'StorageV2'`
- 컨테이너: `Microsoft.Storage/storageAccounts/blobServices/containers`

### 핵심 속성 (빠뜨리면 안 되는 것들)
- `isHnsEnabled: true` — **절대 빠트리지 말 것. 없으면 일반 Blob Storage가 됨. ADLS Gen2의 핵심**
- `allowBlobPublicAccess: false` — 보안 필수
- `minimumTlsVersion: 'TLS1_2'` — 보안 필수
- `publicNetworkAccess: 'Disabled'` — Private Endpoint 사용 시 필수
- `kind: 'StorageV2'` — ADLS Gen2는 StorageV2만 지원

### Private Endpoint 주의
ADLS Gen2는 PE를 두 개 만들어야 할 수 있다:
- `groupId: 'dfs'` — Spark/Fabric이 사용하는 DFS 엔드포인트
- `groupId: 'blob'` — 일반 SDK가 사용하는 Blob 엔드포인트

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource storageAccount 'Microsoft.Storage/storageAccounts@<fetch로 확인>' = {
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true              // ADLS Gen2 핵심 — 절대 빠트리지 말 것
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
    ...
  }
}
```

### MS Docs
- Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/storageaccounts

---

## Azure Key Vault

### 무엇인지
시크릿, 인증서, 키를 안전하게 저장하고 관리하는 서비스.

### 리소스 타입
- `Microsoft.KeyVault/vaults`

### 핵심 속성 (빠뜨리면 안 되는 것들)
- `enableRbacAuthorization: true` — **RBAC 방식 사용 필수. Access Policy 방식 사용 금지**
- `enablePurgeProtection: true` — 삭제된 Vault 영구 삭제 방지 (규정 준수)
- `softDeleteRetentionInDays: 90` — 소프트 삭제 보존 기간
- `publicNetworkAccess: 'disabled'` — Private Endpoint 사용 시 필수
- `networkAcls.bypass: 'AzureServices'` — ARM 배포 및 Azure 서비스 접근 허용

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource keyVault 'Microsoft.KeyVault/vaults@<fetch로 확인>' = {
  properties: {
    enableRbacAuthorization: true   // Access Policy 방식 사용 금지
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    ...
  }
}
```

### MS Docs
- Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/vaults

---

## Azure Machine Learning (AML)

### 무엇인지
ML 모델 훈련, 실험, 배포를 위한 플랫폼. 오픈소스 모델, HuggingFace, Managed compute가 필요한 경우에 사용.

> **주의**: 일반 AI/RAG 구성에는 Microsoft Foundry(AIServices)를 사용한다. AML Hub/Project 기반은 레거시이며 ML 전용이다.

### 리소스 타입
- AML Workspace: `Microsoft.MachineLearningServices/workspaces`, `kind: 'Default'`
- Hub (레거시): `kind: 'Hub'`
- Hub Project (레거시): `kind: 'Project'`

### 핵심 속성
- `storageAccount` — 연결할 Storage Account ID (필수)
- `keyVault` — 연결할 Key Vault ID (필수)
- `publicNetworkAccess: 'Disabled'` — Private Endpoint 사용 시 필수
- Hub의 경우 `managedNetwork.isolationMode: 'AllowOnlyApprovedOutbound'` 권장

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource amlWorkspace 'Microsoft.MachineLearningServices/workspaces@<fetch로 확인>' = {
  kind: 'Default'  // 일반 AML Workspace
  properties: {
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    publicNetworkAccess: 'Disabled'
    ...
  }
}
```

### MS Docs
- Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.machinelearningservices/workspaces

---

## Virtual Network / Private Endpoint

### 무엇인지
- **VNet**: Azure 리소스들의 격리된 네트워크 환경
- **Private Endpoint**: VNet 내 프라이빗 IP로 PaaS 서비스에 접근. 인터넷을 통하지 않고 내부 네트워크만 사용

### 리소스 타입
- VNet: `Microsoft.Network/virtualNetworks`
- Private Endpoint: `Microsoft.Network/privateEndpoints`
- Private DNS Zone: `Microsoft.Network/privateDnsZones`

### 핵심 속성 (빠뜨리면 안 되는 것들)
- pe-subnet에 `privateEndpointNetworkPolicies: 'Disabled'` — **없으면 PE 배포 불가**
- Private DNS Zone + VNet Link + DNS Zone Group — **3종 세트 필수** (하나라도 빠지면 DNS 해석 실패)
- DNS Zone의 `registrationEnabled: false` — PaaS 서비스용 고정값 (VM 자동등록 불필요)

### 3종 세트 패턴
각 서비스마다 아래 3가지를 반드시 함께 생성:
1. `Microsoft.Network/privateEndpoints` (pe-subnet에 배치)
2. `Microsoft.Network/privateDnsZones` + VNet Link (`registrationEnabled: false`)
3. `Microsoft.Network/privateEndpoints/privateDnsZoneGroups`

### Bicep 구조 요약
```bicep
// apiVersion은 MS Docs fetch 후 확인
resource vnet 'Microsoft.Network/virtualNetworks@<fetch로 확인>' = {
  properties: {
    subnets: [
      {
        name: 'pe-subnet'
        properties: {
          privateEndpointNetworkPolicies: 'Disabled'  // PE 배포 필수 설정
          ...
        }
      }
    ]
  }
}
```

### MS Docs
- VNet Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.network/virtualnetworks
- Private Endpoint Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.network/privateendpoints
- Private DNS Zones Bicep 레퍼런스: https://learn.microsoft.com/en-us/azure/templates/microsoft.network/privatednszones

---

## 네이밍 컨벤션 (CAF 기준)

| 서비스 | 접두사 | 예시 |
|--------|--------|------|
| Resource Group | rg- | rg-ai-platform-prod |
| Virtual Network | vnet- | vnet-ai-prod-krc |
| Azure OpenAI / Foundry | oai- / foundry- | foundry-ai-prod |
| AI Search | srch- | srch-docs-prod |
| Storage Account | st | stailakeprod |
| Key Vault | kv- | kv-ai-secrets-prod |
| Fabric Capacity | fabric- | fabric-analytics-prod |
| AML Workspace | mlw- | mlw-training-prod |
