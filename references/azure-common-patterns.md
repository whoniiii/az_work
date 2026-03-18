# Azure Common Patterns (Stable)

이 파일은 Azure 서비스 전반에 걸쳐 반복되는 **불변에 가까운 패턴**만 담는다.
API version, SKU, region 같은 동적 정보는 여기에 넣지 않는다 → `azure-dynamic-sources.md` 참조.

---

## 1. 네트워크 격리 패턴

### Private Endpoint 3종 세트

PE를 사용하는 모든 서비스에는 반드시 3종 세트를 구성한다:

1. **Private Endpoint** — pe-subnet에 배치
2. **Private DNS Zone** + **VNet Link** (`registrationEnabled: false`)
3. **DNS Zone Group** — PE에 연결

> 하나라도 빠지면 PE가 있어도 DNS 해석이 안 되어 연결 실패.

### PE 서브넷 필수 설정

```bicep
resource peSubnet 'Microsoft.Network/virtualNetworks/subnets' = {
  properties: {
    addressPrefix: peSubnetPrefix              // ← CIDR은 파라미터로 — 기존 네트워크 충돌 방지
    privateEndpointNetworkPolicies: 'Disabled'  // ← 필수. 없으면 PE 배포 실패
  }
}
```

### publicNetworkAccess 패턴

PE 사용 서비스는 반드시:
```bicep
properties: {
  publicNetworkAccess: 'Disabled'
  networkAcls: {
    defaultAction: 'Deny'
  }
}
```

---

## 2. 보안 패턴

### Key Vault

```bicep
properties: {
  enableRbacAuthorization: true    // Access Policy 방식 사용 금지
  enableSoftDelete: true
  softDeleteRetentionInDays: 90
  enablePurgeProtection: true
}
```

### Managed Identity

AI 서비스에서 다른 리소스에 접근할 때:
```bicep
identity: {
  type: 'SystemAssigned'  // 또는 'UserAssigned'
}
```

### 민감 정보

- `@secure()` 데코레이터 사용
- `.bicepparam` 파일에 평문 저장 금지
- Key Vault 참조 사용

---

## 3. 이름 규칙 (CAF 기반)

```
rg-{project}-{env}          리소스 그룹
vnet-{project}-{env}        Virtual Network
st{project}{env}             Storage Account (특수문자 불가, 소문자+숫자만)
kv-{project}-{env}           Key Vault
srch-{project}-{env}         AI Search
foundry-{project}-{env}      Cognitive Services (Foundry)
```

> 이름 충돌 방지: `uniqueString(resourceGroup().id)` 사용 권장
> ```bicep
> param storageName string = 'st${uniqueString(resourceGroup().id)}'
> ```

---

## 4. Bicep 모듈 구조

```
<project>/
├── main.bicep              # 오케스트레이션 — 모듈 호출 + 파라미터 전달
├── main.bicepparam         # 환경별 값 (민감 정보 제외)
└── modules/
    ├── network.bicep           # VNet, Subnet
    ├── <service>.bicep         # 서비스별 모듈
    ├── keyvault.bicep          # Key Vault
    └── private-endpoints.bicep # 모든 PE + DNS Zone + VNet Link
```

### 의존성 관리

```bicep
// ✅ 올바름: 리소스 참조로 암묵적 의존성
resource project '...' = {
  properties: {
    parentId: foundry.id  // foundry 참조 → 자동으로 foundry 먼저 배포
  }
}

// ❌ 피할 것: 명시적 dependsOn (필요할 때만 사용)
```

---

## 5. PE Bicep 공통 템플릿

```bicep
// ── Private Endpoint ──
resource pe 'Microsoft.Network/privateEndpoints@<fetch>' = {
  name: 'pe-${serviceName}'
  location: location
  properties: {
    subnet: { id: peSubnetId }
    privateLinkServiceConnections: [{
      name: 'pls-${serviceName}'
      properties: {
        privateLinkServiceId: serviceId
        groupIds: ['<groupId>']  // ← 서비스별 다름. service-gotchas.md 참조
      }
    }]
  }
}

// ── Private DNS Zone ──
resource dnsZone 'Microsoft.Network/privateDnsZones@<fetch>' = {
  name: '<dnsZoneName>'  // ← 서비스별 다름
  location: 'global'
}

// ── VNet Link ──
resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@<fetch>' = {
  parent: dnsZone
  name: '${dnsZone.name}-link'
  location: 'global'
  properties: {
    virtualNetwork: { id: vnetId }
    registrationEnabled: false  // ← 반드시 false
  }
}

// ── DNS Zone Group ──
resource dnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@<fetch>' = {
  parent: pe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [{
      name: 'config'
      properties: { privateDnsZoneId: dnsZone.id }
    }]
  }
}
```

> `@<fetch>`: API version은 배포 전 반드시 MS Docs에서 최신 stable 버전 확인.
