# Azure AI/Data 서비스 Bicep 스니펫

> **네이밍 기준 (2025년 최신)**
> - Azure AI Studio → Azure AI Foundry → **Microsoft Foundry** (최신 명칭, 2025년)
> - Microsoft Foundry Hub/Project: Bicep 리소스 타입은 동일 (`Microsoft.MachineLearningServices/workspaces`)
> - 표시 명칭: "Microsoft Foundry Hub", "Microsoft Foundry Project"

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

```bicep
// Azure OpenAI Service (Microsoft Foundry 포털 ai.azure.com에서 관리)
param openAiName string = 'oai-${uniqueString(resourceGroup().id)}'
param openAiSku string = 'S0'
param openAiLocation string = 'eastus' // OpenAI는 지역 제한 있음

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAiName
  location: openAiLocation
  kind: 'OpenAI'
  sku: {
    name: openAiSku
  }
  properties: {
    publicNetworkAccess: 'Disabled'  // Private Endpoint 사용 시
    customSubDomainName: openAiName
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// GPT-4o 모델 배포
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: 'gpt-4o'
  sku: {
    name: 'GlobalStandard'
    capacity: 30  // TPM (Thousands of tokens per minute)
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
  }
}

// text-embedding-3-large 배포
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
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
```

### Microsoft Foundry Hub

```bicep
// Microsoft Foundry Hub (구: Azure AI Studio Hub → Azure AI Foundry Hub → Microsoft Foundry Hub)
// Bicep 리소스 타입은 MachineLearningServices/workspaces, kind: 'Hub'
param aiHubName string = 'aih-${uniqueString(resourceGroup().id)}'

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: aiHubName
  location: location
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: aiHubName
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id  // 선택사항
    publicNetworkAccess: 'Disabled'
    managedNetwork: {
      isolationMode: 'AllowOnlyApprovedOutbound'
      outboundRules: {}
    }
  }
}

// Microsoft Foundry Project
param aiProjectName string = 'aip-${uniqueString(resourceGroup().id)}'

resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: aiProjectName
  location: location
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: aiProjectName
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Disabled'
  }
}

// AI Services Connection (OpenAI → Microsoft Foundry Hub 연결)
resource aiServicesConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-10-01' = {
  parent: aiHub
  name: 'aoai-connection'
  properties: {
    category: 'AzureOpenAI'
    target: openAi.properties.endpoint
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: openAi.listKeys().key1
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: openAi.id
    }
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
