# Azure AI/Data 서비스 Bicep 스니펫

> **Microsoft Foundry 최신 아키텍처 (2025년)**
>
> **계층 구조**: `Microsoft Foundry resource` → `Foundry Project` → Project assets (에이전트, 파일, 평가)
>
> - **Microsoft Foundry resource**: 최상위 Azure 리소스. 모델 배포, 네트워킹, 보안 거버넌스 담당
>   - Bicep: `Microsoft.CognitiveServices/accounts` + `kind: 'AIServices'`
> - **Foundry Project**: Foundry resource의 서브리소스. 팀/유스케이스 단위 개발 경계
>   - Bicep: `Microsoft.CognitiveServices/accounts/projects`
> - **모델 배포**: Foundry resource 레벨에서 배포 → 프로젝트에서 공유 사용
>   - Bicep: `Microsoft.CognitiveServices/accounts/deployments`
> - **Azure OpenAI (`kind: 'OpenAI'`)**: 레거시. Foundry (`kind: 'AIServices'`)의 서브셋
>   - 동일 리소스 프로바이더(`Microsoft.CognitiveServices`)이므로 업그레이드 가능
> - **Hub 기반 (`Microsoft.MachineLearningServices/workspaces`)**: 레거시. ML/오픈소스 모델, Serverless API 필요 시에만 사용
> - **API 버전**: `2025-06-01`

## 목차
1. [Azure OpenAI / Microsoft Foundry](#azure-openai--microsoft-foundry)
2. [Azure AI Search](#azure-ai-search)
3. [Microsoft Fabric](#microsoft-fabric)
4. [ADLS Gen2 / Storage Account](#adls-gen2--storage-account)
5. [Azure Machine Learning](#azure-machine-learning)
6. [Key Vault](#key-vault)
7. [Container Registry](#container-registry)
8. [Virtual Network](#virtual-network)

---

## Azure OpenAI / Microsoft Foundry

### Microsoft Foundry resource (신규 권장)

```bicep
// Microsoft Foundry resource — kind: 'AIServices' (Azure OpenAI의 superset)
// 모델 배포, 프로젝트 관리, AI Search 연결 등 모든 AI 기능의 최상위 리소스
param foundryName string = 'foundry-${uniqueString(resourceGroup().id)}'

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: foundryName
  location: location  // OpenAI 지원 지역: eastus, swedencentral 등
  kind: 'AIServices'  // 핵심 — OpenAI가 아닌 AIServices (Foundry)
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true  // Foundry Project 생성 활성화 필수
    customSubDomainName: foundryName
    disableLocalAuth: false       // EntraID + API Key 모두 허용 (운영 환경은 true 권장)
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// 모델 배포 — Foundry resource 레벨에서 수행, Project에서 공유 사용
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: 'gpt-4o'
  sku: {
    name: 'GlobalStandard'
    capacity: 30  // TPM (Thousands of tokens per minute)
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: 'text-embedding-3-large'
  sku: {
    name: 'Standard'
    capacity: 120
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: '1'
    }
  }
  dependsOn: [gpt4oDeployment]
}

// Foundry Project — Foundry resource의 서브리소스, 팀/유스케이스 단위
param foundryProjectName string = 'proj-${uniqueString(resourceGroup().id)}'

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundry
  name: foundryProjectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}
```

### Azure OpenAI Service (레거시 — 신규 개발 시 Microsoft Foundry 사용 권장)

```bicep
// Azure OpenAI Service — kind: 'OpenAI' (Foundry의 서브셋, 레거시)
// 기존 호환성 유지 목적 또는 OpenAI 전용 엔드포인트가 명시적으로 필요한 경우
param openAiName string = 'oai-${uniqueString(resourceGroup().id)}'

resource openAi 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: openAiName
  location: location  // eastus, swedencentral 등 OpenAI 지원 지역
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}
```

### Hub 기반 구성 (레거시 — ML/오픈소스 모델, Serverless API, Managed compute 필요 시에만)

```bicep
// Azure AI Hub — MachineLearningServices, kind: 'Hub'
// ⚠️ 신규 개발에는 Microsoft Foundry (AIServices) 사용 권장
// Hub 기반은 HuggingFace, NVIDIA NIM, Managed compute, Prompt flow 등 ML 기능 필요 시 사용
param aiHubName string = 'aih-${uniqueString(resourceGroup().id)}'

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: aiHubName
  location: location
  kind: 'Hub'
  identity: { type: 'SystemAssigned' }
  properties: {
    friendlyName: aiHubName
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    publicNetworkAccess: 'Disabled'
    managedNetwork: {
      isolationMode: 'AllowOnlyApprovedOutbound'
    }
  }
}

// Hub-based Project (레거시)
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: 'proj-${uniqueString(resourceGroup().id)}'
  location: location
  kind: 'Project'
  identity: { type: 'SystemAssigned' }
  properties: {
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Disabled'
  }
}
```

---

## Azure AI Search

```bicep
param searchServiceName string = 'srch-${uniqueString(resourceGroup().id)}'
param searchSku string = 'standard'  // free, basic, standard, standard2, standard3
param searchReplicaCount int = 1
param searchPartitionCount int = 1

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  sku: {
    name: searchSku
  }
  properties: {
    replicaCount: searchReplicaCount
    partitionCount: searchPartitionCount
    publicNetworkAccess: 'disabled'
    networkRuleSet: {
      ipRules: []
    }
    semanticSearch: 'free'  // Semantic ranking 활성화
  }
}

// Managed Identity에 Search 권한 부여 (예: AI Hub → Search)
resource searchIndexDataContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(searchService.id, aiHub.id, '8ebe5a00-799e-43f5-93ac-243d3dce84a7')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8ebe5a00-799e-43f5-93ac-243d3dce84a7')  // Search Index Data Contributor
    principalId: aiHub.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

---

## Microsoft Fabric

```bicep
// Microsoft Fabric Capacity (F SKU)
param fabricCapacityName string = 'fabric-${uniqueString(resourceGroup().id)}'
param fabricSku string = 'F2'  // F2, F4, F8, F16, F32, F64 ...
param fabricAdminEmail string  // Fabric 관리자 이메일

resource fabricCapacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: fabricCapacityName
  location: location
  sku: {
    name: fabricSku
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: [fabricAdminEmail]
    }
  }
}

// Fabric은 대부분의 설정을 Fabric Portal에서 진행
// Bicep으로는 Capacity만 프로비저닝 가능
// Workspace, Lakehouse, Warehouse 등은 Fabric REST API 또는 Portal 사용

// Fabric에서 ADLS Gen2 OneLake 연결 시
// → ADLS Gen2의 Storage Blob Data Contributor 역할을 Fabric managed identity에 부여
```

---

## ADLS Gen2 / Storage Account

```bicep
param storageAccountName string = 'st${uniqueString(resourceGroup().id)}'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_ZRS'  // Zone-redundant storage
  }
  properties: {
    isHnsEnabled: true  // ADLS Gen2 (Hierarchical Namespace)
    publicNetworkAccess: 'Disabled'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: []
    }
    encryption: {
      services: {
        blob: { enabled: true }
        file: { enabled: true }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// 컨테이너 생성 (raw, processed, curated 레이어 패턴)
resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/raw'
  properties: {
    publicAccess: 'None'
  }
}

resource processedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/processed'
  properties: {
    publicAccess: 'None'
  }
}

resource curatedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/curated'
  properties: {
    publicAccess: 'None'
  }
}
```

---

## Azure Machine Learning

```bicep
param amlWorkspaceName string = 'mlw-${uniqueString(resourceGroup().id)}'

resource amlWorkspace 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: amlWorkspaceName
  location: location
  kind: 'Default'  // 일반 AML Workspace (Hub/Project와 구분)
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: amlWorkspaceName
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    containerRegistry: containerRegistry.id  // 선택사항
    publicNetworkAccess: 'Disabled'
    managedNetwork: {
      isolationMode: 'AllowOnlyApprovedOutbound'
    }
  }
}
```

---

## Key Vault

```bicep
param keyVaultName string = 'kv-${uniqueString(resourceGroup().id)}'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true  // RBAC 방식 (Access Policy 아님)
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

// Key Vault Secrets Officer 역할 부여 (예: 배포 서비스 주체에게)
resource kvSecretsOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, deployer, 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')
    principalId: deployer  // 배포 주체의 Object ID
    principalType: 'User'
  }
}
```

---

## Container Registry

```bicep
param acrName string = 'cr${uniqueString(resourceGroup().id)}'

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Premium'  // Private Endpoint는 Premium SKU 필요
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Disabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}
```

---

## Virtual Network

```bicep
param vnetName string = 'vnet-${uniqueString(resourceGroup().id)}'
param vnetAddressPrefix string = '10.0.0.0/16'

// 서브넷 구성 예시
// - pe-subnet: Private Endpoint 전용 (NSG 불필요, PrivateEndpointNetworkPolicies 비활성화 필요)
// - app-subnet: App Service / AKS 등 워크로드 (위임 가능)
// - training-subnet: AML Compute (서비스 엔드포인트 추가 가능)

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [vnetAddressPrefix]
    }
    subnets: [
      {
        name: 'pe-subnet'
        properties: {
          addressPrefix: '10.0.1.0/24'
          // Private Endpoint는 이 설정이 반드시 필요
          privateEndpointNetworkPolicies: 'Disabled'
          privateLinkServiceNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'app-subnet'
        properties: {
          addressPrefix: '10.0.2.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'training-subnet'
        properties: {
          addressPrefix: '10.0.3.0/24'
          serviceEndpoints: [
            { service: 'Microsoft.Storage' }
            { service: 'Microsoft.KeyVault' }
          ]
        }
      }
    ]
  }
}

// 서브넷 참조용
var peSubnetId = '${vnet.id}/subnets/pe-subnet'
var appSubnetId = '${vnet.id}/subnets/app-subnet'
```

---

## 네이밍 컨벤션 (CAF 기준)

| 서비스 | 접두사 | 예시 |
|--------|--------|------|
| Resource Group | rg- | rg-ai-platform-prod |
| Virtual Network | vnet- | vnet-ai-prod-krc |
| Azure OpenAI | oai- | oai-gpt4-prod |
| AI Search | srch- | srch-docs-prod |
| AI Hub | aih- | aih-foundry-prod |
| AI Project | aip- | aip-rag-prod |
| Storage Account | st | stailakeprod |
| Key Vault | kv- | kv-ai-secrets-prod |
| Fabric Capacity | fabric- | fabric-analytics-prod |
| AML Workspace | mlw- | mlw-training-prod |
| Container Registry | cr | crmlprod |
