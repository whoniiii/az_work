# Service Gotchas (Stable)

서비스별 **비직관적 필수 속성**, **흔한 실수**, **PE 매핑** 정리.
여기에는 불변에 가까운 패턴만 넣는다. API version, SKU 목록, region 같은 동적 값은 넣지 않는다.

---

## 1. 필수 속성 (빠뜨리면 배포 실패 또는 기능 장애)

| 서비스 | 필수 속성 | 누락 시 결과 | 비고 |
|--------|----------|-------------|------|
| ADLS Gen2 | `isHnsEnabled: true` | 일반 Blob Storage가 됨. 되돌릴 수 없음 | `kind: 'StorageV2'` 필수 |
| Storage Account | 이름에 특수문자/하이픈 불가 | 배포 실패 | 소문자+숫자만, 3-24자 |
| Foundry (AIServices) | `allowProjectManagement: true` | Foundry Project 생성 불가 | `kind: 'AIServices'` |
| Foundry (AIServices) | `identity: { type: 'SystemAssigned' }` | Project 생성 시 실패 | |
| Foundry Project | Foundry resource와 반드시 세트 생성 | 포털에서 사용 불가 | `accounts/projects` |
| Key Vault | `enableRbacAuthorization: true` | Access Policy 방식 혼용 위험 | |
| Key Vault | `enablePurgeProtection: true` | 프로덕션 필수 | |
| Fabric Capacity | `administration.members` 필수 | 배포 실패 | admin 이메일 |
| PE Subnet | `privateEndpointNetworkPolicies: 'Disabled'` | PE 배포 실패 | |
| PE DNS Zone | `registrationEnabled: false` (VNet Link) | DNS 충돌 가능 | |
| PE 구성 | 3종 세트 (PE + DNS Zone + VNet Link + Zone Group) | PE 있어도 DNS 해석 실패 | |

---

## 2. PE groupId & DNS Zone 매핑 (주요 서비스)

아래 매핑은 안정적이나, 새 서비스 추가 시 `azure-dynamic-sources.md`의 PE DNS 통합 문서에서 재확인.

| 서비스 | groupId | Private DNS Zone |
|--------|---------|-----------------|
| Azure OpenAI / CognitiveServices | `account` | `privatelink.cognitiveservices.azure.com` |
| Azure AI Search | `searchService` | `privatelink.search.windows.net` |
| Storage (Blob/ADLS) | `blob` | `privatelink.blob.core.windows.net` |
| Storage (DFS/ADLS Gen2) | `dfs` | `privatelink.dfs.core.windows.net` |
| Key Vault | `vault` | `privatelink.vaultcore.azure.net` |
| Azure ML / AI Hub | `amlworkspace` | `privatelink.api.azureml.ms` |
| Container Registry | `registry` | `privatelink.azurecr.io` |
| Cosmos DB (SQL) | `Sql` | `privatelink.documents.azure.com` |
| Azure Cache for Redis | `redisCache` | `privatelink.redis.cache.windows.net` |
| Data Factory | `dataFactory` | `privatelink.datafactory.azure.net` |
| API Management | `Gateway` | `privatelink.azure-api.net` |
| Event Hub | `namespace` | `privatelink.servicebus.windows.net` |
| Service Bus | `namespace` | `privatelink.servicebus.windows.net` |
| Monitor (AMPLS) | ⚠️ 복합 구성 — 아래 참고 | ⚠️ 다중 DNS Zone 필요 — 아래 참고 |

> **ADLS Gen2 주의**: 용도에 따라 `blob`과 `dfs` 두 PE가 모두 필요할 수 있다.
>
> **⚠️ Azure Monitor Private Link (AMPLS) 주의**: Azure Monitor는 단일 PE + 단일 DNS Zone으로 구성할 수 없다. Azure Monitor Private Link Scope (AMPLS)를 통해 연결하며, **5개 DNS Zone**이 모두 필요하다:
> - `privatelink.monitor.azure.com`
> - `privatelink.oms.opinsights.azure.com`
> - `privatelink.ods.opinsights.azure.com`
> - `privatelink.agentsvc.azure-automation.net`
> - `privatelink.blob.core.windows.net` (Log Analytics 데이터 수집용)
>
> 이 매핑은 복잡하고 변경 가능성이 있으므로, Monitor PE 구성 시 반드시 MS Docs를 fetch하여 확인한다:
> https://learn.microsoft.com/en-us/azure/azure-monitor/logs/private-link-configure

---

## 3. 흔한 실수 체크리스트

| 항목 | ❌ 잘못된 예 | ✅ 올바른 예 |
|------|------------|------------|
| ADLS Gen2 HNS | `isHnsEnabled` 생략 또는 `false` | `isHnsEnabled: true` |
| PE 서브넷 | 정책 미설정 | `privateEndpointNetworkPolicies: 'Disabled'` |
| DNS Zone Group | PE만 생성 | PE + DNS Zone + VNet Link + DNS Zone Group |
| Foundry resource | `kind: 'OpenAI'` | `kind: 'AIServices'` + `allowProjectManagement: true` |
| Foundry Project | Foundry만 있고 Project 없음 | 반드시 세트로 생성 |
| Key Vault 인증 | Access Policy | `enableRbacAuthorization: true` |
| 공개 네트워크 | 설정 없음 | `publicNetworkAccess: 'Disabled'` |
| Storage 이름 | `st-my-storage` | `stmystorage` 또는 `st${uniqueString(...)}` |
| API version | 이전 대화/에러에서 복사 | MS Docs에서 최신 stable 확인 |
| 리전 | 하드코딩 (`'eastus'`) | 파라미터로 전달 (`param location`) |
| 민감 값 | `.bicepparam`에 평문 | `@secure()` + Key Vault 참조 |

---

## 4. 서비스 관계 Decision Rules

절대적 단정 대신 **기본 선택 규칙**으로 기술한다.

### Foundry vs Azure OpenAI vs AI Hub

```
기본 규칙:
├─ AI/RAG 워크로드 → Microsoft Foundry (kind: 'AIServices') 사용
│   ├─ Foundry resource + Foundry Project 세트 생성
│   └─ 모델 배포는 Foundry resource 레벨에서 수행 (accounts/deployments)
│
├─ ML/오픈소스 모델 훈련 필요 → AI Hub (MachineLearningServices) 검토
│   └─ 사용자가 명시적으로 요구하거나, Foundry에서 미지원 기능이 필요한 경우
│
└─ standalone Azure OpenAI resource →
    사용자가 명시적으로 요구하거나,
    공식 문서상 별도 리소스가 필요한 경우에만 검토
```

> 이 규칙은 현재 MS 권장 사항을 반영한 **기본 선택 가이드**이다.
> Azure 제품 관계는 변할 수 있으므로, 확신이 없으면 MS Docs를 확인한다.

### Monitoring

```
기본 규칙:
├─ Foundry (AIServices) → Application Insights 불필요
└─ AI Hub (MachineLearningServices) → Application Insights + Log Analytics 필요
```
