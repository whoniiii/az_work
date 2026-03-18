# Domain Pack: AI/Data (v1)

Azure AI/Data 워크로드에 특화된 서비스 구성 가이드.
v1 스코프: Foundry, AI Search, ADLS Gen2, Key Vault, Fabric, ADF, VNet/PE.

> 필수 속성/흔한 실수 → `service-gotchas.md`
> 동적 정보 (API version, SKU, region) → `azure-dynamic-sources.md`
> 공통 패턴 (PE, 보안, 명명) → `azure-common-patterns.md`

---

## 1. Microsoft Foundry (CognitiveServices)

### 리소스 계층

```
Microsoft.CognitiveServices/accounts (kind: 'AIServices')
├── /projects          — Foundry Project (포털 접근에 필수)
└── /deployments       — 모델 배포 (GPT-4o, embedding 등)
```

### Bicep 핵심 구조

```bicep
// Foundry resource
resource foundry 'Microsoft.CognitiveServices/accounts@<fetch>' = {
  name: foundryName
  location: location
  kind: 'AIServices'
  sku: { name: '<사용자 확인>' }               // ← SKU는 Phase 1에서 MS Docs 확인 후 확정
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: foundryName  // ← 필수, 글로벌 고유값. 생성 후 변경 불가 — 누락 시 리소스 삭제 후 재생성
    allowProjectManagement: true
    publicNetworkAccess: 'Disabled'
    networkAcls: { defaultAction: 'Deny' }
  }
}

// Foundry Project — 반드시 Foundry와 세트
resource project 'Microsoft.CognitiveServices/accounts/projects@<fetch>' = {
  parent: foundry
  name: '${foundryName}-project'
  location: location
  sku: { name: '<부모와 동일>' }
  kind: 'AIServices'
  identity: { type: 'SystemAssigned' }
  properties: {}
}

// 모델 배포 — Foundry resource 레벨
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@<fetch>' = {
  parent: foundry
  name: '<모델명>'                              // ← Phase 1에서 사용자와 확정
  sku: {
    name: '<배포 타입>'                          // ← GlobalStandard, Standard 등 — MS Docs fetch
    capacity: <사용자 확인>                       // ← 용량 단위 — MS Docs에서 가용 범위 확인
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: '<모델명>'                           // ← 반드시 가용성 확인 (fetch)
      version: '<fetch>'                         // ← 버전도 fetch
    }
  }
}
```

> `@<fetch>`: API version은 `azure-dynamic-sources.md`의 URL에서 확인.
> 모델명/버전/배포타입/capacity: 모두 Dynamic — Phase 1에서 MS Docs fetch 후 사용자와 확정.

---

## 2. Azure AI Search

### Bicep 핵심 구조

```bicep
resource search 'Microsoft.Search/searchServices@<fetch>' = {
  name: searchName
  location: location
  sku: { name: '<사용자 확인>' }
  identity: { type: 'SystemAssigned' }
  properties: {
    hostingMode: 'default'
    publicNetworkAccess: 'disabled'
    semanticSearch: '<사용자 확인>'    // disabled | free | standard — MS Docs 확인
  }
}
```

### 설계 참고

- PE 지원: Basic SKU 이상 (MS Docs에서 최신 제약 확인)
- Semantic Ranker: `semanticSearch` 속성으로 활성화 (`disabled` | `free` | `standard`) — SKU별 지원 여부 MS Docs 확인
- 벡터 검색: 유료 SKU에서 지원 (MS Docs 확인)
- RAG 구성 시 Foundry와 함께 사용하는 것이 일반적

---

## 3. ADLS Gen2 (Storage Account)

### Bicep 핵심 구조

```bicep
resource storage 'Microsoft.Storage/storageAccounts@<fetch>' = {
  name: storageName        // 소문자+숫자만, 하이픈 불가
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    isHnsEnabled: true                 // ← 절대 빠뜨리지 말 것
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
    networkAcls: { defaultAction: 'Deny' }
  }
}

// 컨테이너
resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@<fetch>' = {
  name: '${storage.name}/default/raw'
}
```

### 설계 참고

- `isHnsEnabled`는 생성 후 변경 불가 → 빠뜨리면 리소스 재생성 필요
- PE: 용도에 따라 `blob`과 `dfs` 두 PE 필요할 수 있음
- 일반적인 컨테이너: `raw`, `processed`, `curated`

---

## 4. Microsoft Fabric

### Bicep 핵심 구조

```bicep
resource fabric 'Microsoft.Fabric/capacities@<fetch>' = {
  name: fabricName
  location: location
  sku: { name: '<사용자 확인>', tier: 'Fabric' }
  properties: {
    administration: {
      members: [ '<admin-email>' ]    // ← 필수, 없으면 배포 실패
    }
  }
}
```

### 설계 참고

- Bicep으로 프로비저닝 가능한 것: Capacity만
- Workspace, Lakehouse, Warehouse 등은 포털에서 수동 생성
- admin 이메일은 사용자에게 확인 (`AskUserQuestion`)

### Phase 1 추가 시 필수 확인 항목

Fabric이 대화 중 추가되면, 다이어그램 업데이트 전에 아래 항목을 반드시 AskUserQuestion으로 확인:

- [ ] **SKU/Capacity**: F2, F4, F8, ... — MS Docs에서 가용 SKU fetch 후 선택지 제공
- [ ] **administration.members**: admin 이메일 — 없으면 배포 실패

> 사용자가 명시하지 않은 하위 워크로드(OneLake, 데이터 파이프라인, Warehouse 등)를 임의로 구성에 넣지 않는다. Bicep으로 프로비저닝 가능한 것은 Capacity만이다.

---

## 5. Azure Data Factory

### Bicep 핵심 구조

```bicep
resource adf 'Microsoft.DataFactory/factories@<fetch>' = {
  name: adfName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
}
```

### 설계 참고

- Self-hosted Integration Runtime은 Bicep 외 수동 설정
- 온프레미스 데이터 수집 시나리오에 주로 사용
- PE groupId: `dataFactory`

---

## 6. AML / AI Hub (MachineLearningServices)

### 사용 시점

```
Decision Rule:
├─ 일반 AI/RAG → Foundry (AIServices) 사용
└─ ML 훈련, 오픈소스 모델 필요 → AI Hub 검토
    └─ 사용자가 명시적으로 요구한 경우에만
```

### Bicep 핵심 구조

```bicep
resource hub 'Microsoft.MachineLearningServices/workspaces@<fetch>' = {
  name: hubName
  location: location
  kind: 'Hub'
  sku: { name: '<사용자 확인>', tier: '<사용자 확인>' }  // 예: Basic/Basic — MS Docs에서 가용 SKU 확인
  identity: { type: 'SystemAssigned' }
  properties: {
    friendlyName: hubName
    storageAccount: storage.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id    // Hub에서는 필요
    publicNetworkAccess: 'Disabled'
  }
}
```

### AI Hub 의존성

Hub 사용 시 추가 필요:
- Storage Account
- Key Vault
- Application Insights + Log Analytics Workspace
- Container Registry (선택)

---

## 7. 일반적인 AI/Data 아키텍처 조합

### RAG 챗봇

```
Foundry (AIServices) + Project
├── <chat-model> (chat)              — Phase 1에서 가용성 확인 후 확정
├── <embedding-model> (embedding)    — Phase 1에서 가용성 확인 후 확정
├── AI Search (vector + semantic)
├── ADLS Gen2 (document store)
└── Key Vault (secrets)
+ VNet/PE 전체 구성
```

### 데이터 플랫폼

```
Fabric Capacity (analytics)
├── ADLS Gen2 (data lake)
├── ADF (ingestion)
└── Key Vault (secrets)
+ VNet/PE 구성
```
