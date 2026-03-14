# Azure Private Endpoint 패턴

## Private Endpoint란?

VNet의 프라이빗 IP 주소를 Azure PaaS 서비스에 할당하여, 인터넷을 거치지 않고 내부 네트워크로만 접근하게 하는 기능.
엔터프라이즈/컴플라이언스 환경에서 필수.

## Bicep 기본 패턴

```bicep
// ======================================
// Private Endpoint 생성 (공통 패턴)
// ======================================
// 각 서비스마다 groupId가 다름 (아래 표 참조)

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: 'pe-${targetResourceName}'
  location: location
  properties: {
    subnet: {
      id: peSubnetId  // privateEndpointNetworkPolicies: 'Disabled' 인 서브넷
    }
    privateLinkServiceConnections: [
      {
        name: 'plsc-${targetResourceName}'
        properties: {
          privateLinkServiceId: targetResource.id
          groupIds: ['<GROUP_ID>']  // 서비스별 groupId (아래 표 참조)
        }
      }
    ]
  }
}

// Private DNS Zone Group (PE와 DNS Zone 연결)
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: privateEndpoint
  name: 'dnszg-${targetResourceName}'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config1'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}
```

## 서비스별 groupId & Private DNS Zone

| 서비스 | groupId | Private DNS Zone |
|--------|---------|-----------------|
| Azure OpenAI / Cognitive Services | `account` | `privatelink.cognitiveservices.azure.com` |
| Azure AI Search | `searchService` | `privatelink.search.windows.net` |
| Azure Storage (Blob/ADLS) | `blob` | `privatelink.blob.core.windows.net` |
| Azure Storage (DFS/ADLS Gen2) | `dfs` | `privatelink.dfs.core.windows.net` |
| Azure Storage (File) | `file` | `privatelink.file.core.windows.net` |
| Azure Key Vault | `vault` | `privatelink.vaultcore.azure.net` |
| Azure ML Workspace | `amlworkspace` | `privatelink.api.azureml.ms`, `privatelink.notebooks.azure.net` |
| Container Registry | `registry` | `privatelink.azurecr.io` |
| Azure Monitor / Log Analytics | `azuremonitor` | `privatelink.monitor.azure.com` |
| App Service / Functions | `sites` | `privatelink.azurewebsites.net` |
| Event Hub | `namespace` | `privatelink.servicebus.windows.net` |
| Service Bus | `namespace` | `privatelink.servicebus.windows.net` |

> **ADLS Gen2 주의**: DFS 엔드포인트(`dfs`)와 Blob 엔드포인트(`blob`) 두 개 모두 Private Endpoint를 만들어야 할 수 있다. Spark/Fabric은 DFS, 일반 SDK는 Blob을 사용.

## Private DNS Zone 생성 및 VNet 연결

```bicep
// Private DNS Zone 생성
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.cognitiveservices.azure.com'  // 서비스별로 다름
  location: 'global'  // DNS Zone은 항상 global
}

// VNet과 DNS Zone 연결 (DNS 쿼리가 이 Zone으로 라우팅되도록)
resource dnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZone
  name: 'link-${vnetName}'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false  // Auto-registration은 VM용, PaaS는 false
  }
}
```

## 전체 Private Endpoint 모듈 예시 (OpenAI)

```bicep
// modules/private-endpoints.bicep

param location string
param vnetId string
param peSubnetId string

// 각 리소스 ID를 파라미터로 받음
param openAiId string
param searchServiceId string
param storageAccountId string
param keyVaultId string

// ---- OpenAI Private Endpoint ----
resource peOpenAi 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: 'pe-openai'
  location: location
  properties: {
    subnet: { id: peSubnetId }
    privateLinkServiceConnections: [{
      name: 'plsc-openai'
      properties: {
        privateLinkServiceId: openAiId
        groupIds: ['account']
      }
    }]
  }
}

resource dnsZoneOpenAi 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.cognitiveservices.azure.com'
  location: 'global'
}

resource dnsZoneOpenAiVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dnsZoneOpenAi
  name: 'link-openai'
  location: 'global'
  properties: {
    virtualNetwork: { id: vnetId }
    registrationEnabled: false
  }
}

resource peOpenAiDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: peOpenAi
  name: 'dnszg-openai'
  properties: {
    privateDnsZoneConfigs: [{
      name: 'config1'
      properties: { privateDnsZoneId: dnsZoneOpenAi.id }
    }]
  }
}

// ---- AI Search Private Endpoint ----
resource peSearch 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: 'pe-search'
  location: location
  properties: {
    subnet: { id: peSubnetId }
    privateLinkServiceConnections: [{
      name: 'plsc-search'
      properties: {
        privateLinkServiceId: searchServiceId
        groupIds: ['searchService']
      }
    }]
  }
}

resource dnsZoneSearch 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.search.windows.net'
  location: 'global'
}

resource dnsZoneSearchVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dnsZoneSearch
  name: 'link-search'
  location: 'global'
  properties: {
    virtualNetwork: { id: vnetId }
    registrationEnabled: false
  }
}

resource peSearchDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: peSearch
  name: 'dnszg-search'
  properties: {
    privateDnsZoneConfigs: [{
      name: 'config1'
      properties: { privateDnsZoneId: dnsZoneSearch.id }
    }]
  }
}

// ---- Storage (ADLS Gen2 - DFS) Private Endpoint ----
resource peStorageDfs 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: 'pe-storage-dfs'
  location: location
  properties: {
    subnet: { id: peSubnetId }
    privateLinkServiceConnections: [{
      name: 'plsc-storage-dfs'
      properties: {
        privateLinkServiceId: storageAccountId
        groupIds: ['dfs']  // ADLS Gen2는 dfs 사용
      }
    }]
  }
}

resource dnsZoneStorageDfs 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.dfs.core.windows.net'
  location: 'global'
}

resource dnsZoneStorageDfsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dnsZoneStorageDfs
  name: 'link-storage-dfs'
  location: 'global'
  properties: {
    virtualNetwork: { id: vnetId }
    registrationEnabled: false
  }
}

resource peStorageDfsDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: peStorageDfs
  name: 'dnszg-storage-dfs'
  properties: {
    privateDnsZoneConfigs: [{
      name: 'config1'
      properties: { privateDnsZoneId: dnsZoneStorageDfs.id }
    }]
  }
}

// ---- Key Vault Private Endpoint ----
resource peKeyVault 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: 'pe-keyvault'
  location: location
  properties: {
    subnet: { id: peSubnetId }
    privateLinkServiceConnections: [{
      name: 'plsc-keyvault'
      properties: {
        privateLinkServiceId: keyVaultId
        groupIds: ['vault']
      }
    }]
  }
}

resource dnsZoneKeyVault 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.vaultcore.azure.net'
  location: 'global'
}

resource dnsZoneKeyVaultVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dnsZoneKeyVault
  name: 'link-keyvault'
  location: 'global'
  properties: {
    virtualNetwork: { id: vnetId }
    registrationEnabled: false
  }
}

resource peKeyVaultDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: peKeyVault
  name: 'dnszg-keyvault'
  properties: {
    privateDnsZoneConfigs: [{
      name: 'config1'
      properties: { privateDnsZoneId: dnsZoneKeyVault.id }
    }]
  }
}
```

## Managed Network (AI Hub / AML 전용)

Microsoft Foundry Hub와 AML Workspace는 Managed Network라는 별도 격리 기능을 제공한다.
`AllowOnlyApprovedOutbound` 모드로 설정하면, Hub 내부에서 외부로 나가는 트래픽도 승인된 경로만 허용.

```bicep
// AI Hub Managed Network 아웃바운드 규칙 예시
resource aiHubOutboundToSearch 'Microsoft.MachineLearningServices/workspaces/outboundRules@2024-04-01' = {
  parent: aiHub
  name: 'allow-search'
  properties: {
    type: 'PrivateEndpoint'
    destination: {
      serviceResourceId: searchService.id
      subresourceTarget: 'searchService'
      sparkEnabled: false
    }
  }
}
```

## 체크리스트 (배포 전 확인)

- [ ] pe-subnet에 `privateEndpointNetworkPolicies: 'Disabled'` 설정됨
- [ ] 각 서비스의 `publicNetworkAccess: 'Disabled'` 설정됨
- [ ] Private DNS Zone이 VNet과 연결됨 (`registrationEnabled: false`)
- [ ] Private Endpoint마다 DNS Zone Group이 생성됨
- [ ] ADLS Gen2는 `blob`과 `dfs` 두 groupId 모두 Private Endpoint 생성 여부 확인
- [ ] Key Vault `networkAcls.bypass: 'AzureServices'`로 ARM 배포 허용
- [ ] 온프레미스 연결 시 DNS Forwarder 또는 Azure DNS Private Resolver 필요
