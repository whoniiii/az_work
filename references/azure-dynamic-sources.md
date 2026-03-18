# Azure Dynamic Sources Registry

이 파일은 **자주 바뀌는 정보의 출처(URL)**만 관리한다.
실제 값(API version, SKU, region 등)은 여기에 적지 않는다.
Bicep 생성 전 반드시 아래 URL을 fetch하여 최신 정보를 확인한다.

---

## 1. Bicep API Version (항상 fetch 필수)

서비스별 MS Docs Bicep 레퍼런스. 이 URL에서 최신 stable apiVersion을 확인 후 사용.

| 서비스 | MS Docs URL |
|--------|-------------|
| CognitiveServices (Foundry/OpenAI) | https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts |
| AI Search | https://learn.microsoft.com/en-us/azure/templates/microsoft.search/searchservices |
| Storage Account | https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/storageaccounts |
| Key Vault | https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/vaults |
| Virtual Network | https://learn.microsoft.com/en-us/azure/templates/microsoft.network/virtualnetworks |
| Private Endpoints | https://learn.microsoft.com/en-us/azure/templates/microsoft.network/privateendpoints |
| Private DNS Zones | https://learn.microsoft.com/en-us/azure/templates/microsoft.network/privatednszones |
| Fabric | https://learn.microsoft.com/en-us/azure/templates/microsoft.fabric/capacities |
| Data Factory | https://learn.microsoft.com/en-us/azure/templates/microsoft.datafactory/factories |
| Application Insights | https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/components |
| ML Workspace (Hub) | https://learn.microsoft.com/en-us/azure/templates/microsoft.machinelearningservices/workspaces |

> **하위 리소스도 반드시 확인**: `accounts/projects`, `accounts/deployments`, `privateDnsZones/virtualNetworkLinks` 등 하위 리소스는 부모와 API 버전이 다를 수 있다. 부모 페이지에서 하위 리소스 링크를 따라 확인.

### 위 테이블에 없는 서비스

위 테이블은 v1 스코프 서비스만 포함. 그 외 서비스는:
```
https://learn.microsoft.com/en-us/azure/templates/microsoft.{provider}/{resourceType}
```
형식으로 URL을 구성하여 fetch.

---

## 2. 모델 가용성 (Foundry/OpenAI 모델 사용 시 필수)

모델명이 대상 리전에서 배포 가능한지 확인. 정적 지식에 의존하지 않는다.

| 확인 방법 | URL / 명령 |
|-----------|-----------|
| MS Docs 모델 가용성 | https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models |
| Azure CLI (기존 리소스) | `az cognitiveservices account list-models --name "<NAME>" --resource-group "<RG>" -o table` |

> 모델이 해당 리전에서 사용 불가한 경우 → 사용자에게 알리고, 가용한 리전/대체 모델 제안. 사용자 승인 없이 대체하지 않는다.

---

## 3. Private Endpoint 매핑 (새 서비스 추가 시)

PE groupId와 DNS Zone 매핑은 Azure가 변경할 수 있다. 새 서비스나 확인이 필요한 경우:

| 확인 방법 | URL |
|-----------|-----|
| PE DNS 통합 공식 문서 | https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns |

> `service-gotchas.md`에 있는 주요 서비스 매핑은 안정적이지만, 새 서비스 추가 시 반드시 위 URL에서 재확인.

---

## 4. 서비스 리전 가용성

특정 서비스가 특정 리전에서 사용 가능한지 확인:

| 확인 방법 | URL |
|-----------|-----|
| Azure 서비스별 리전 가용성 | https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/ |

---

## 5. Azure Updates (Secondary Awareness)

아래 소스는 **참고용**으로만 사용. primary source는 항상 MS Docs 공식 문서.

| 소스 | URL | 용도 |
|------|-----|------|
| Azure Updates | https://azure.microsoft.com/en-us/updates/ | 서비스 변경 인지 |
| What's New in Azure | 서비스별 Docs 내 What's New 페이지 | 기능 변경 확인 |

---

## Decision Rule: 언제 fetch하는가?

| 정보 유형 | fetch 필수 여부 | 근거 |
|-----------|----------------|------|
| API version | **항상 fetch** | 수시로 변경, 틀리면 배포 실패 |
| 모델 가용성 (이름, 리전) | **항상 fetch** | 리전별 다르고 수시 변경 |
| SKU 목록 | **항상 fetch** | 서비스별 변경 가능 |
| 리전 가용성 | **항상 fetch** | 서비스별 리전 지원은 수시 변경. 사용자 지정 리전이 해당 서비스에서 가용한지 반드시 확인 |
| PE groupId & DNS Zone | v1 주요 서비스는 `service-gotchas.md` 참조 가능, **새 서비스나 복합 구성(Monitor 등)은 반드시 fetch** | 주요 서비스 매핑은 안정적이나 신규/복합 서비스는 위험 |
| 필수 속성 패턴 | reference 우선 참조 | 불변에 가까움 (isHnsEnabled 등) |
