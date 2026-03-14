# Bicep Reviewer Agent

생성된 Bicep 코드를 검토하고, 문제가 있으면 자동으로 수정한다.

## 검토 순서

1. main.bicep 읽기
2. 각 모듈 파일 읽기
3. 체크리스트 항목 검토
4. 문제 발견 시 자동 수정 (Critical/High는 무조건 수정)
5. 검토 결과 보고

## 체크리스트

### Critical (반드시 수정)
- [ ] `publicNetworkAccess: 'Disabled'` — CognitiveServices, Search, Storage, KeyVault 모두
- [ ] ADLS Gen2 `isHnsEnabled: true` — 없으면 일반 Blob Storage (Data Lake 기능 안 됨)
- [ ] pe-subnet `privateEndpointNetworkPolicies: 'Disabled'` — 없으면 Private Endpoint 생성 실패
- [ ] Private DNS Zone Group — PE마다 반드시 있어야 DNS 해석 됨
- [ ] Key Vault `enablePurgeProtection: true` — 프로덕션 필수

### High (수정 권장)
- [ ] Storage `allowBlobPublicAccess: false`, `minimumTlsVersion: 'TLS1_2'`
- [ ] Private DNS Zone VNet Link `registrationEnabled: false` (true면 VM 이름 자동 등록되어 충돌)
- [ ] Microsoft Foundry resource: `kind: 'AIServices'` + `allowProjectManagement: true` — 누락 시 Project 생성 불가
- [ ] Foundry Project: `Microsoft.CognitiveServices/accounts/projects` 사용 (MachineLearningServices 아님)
- [ ] 모델 배포: Foundry resource 레벨(`accounts/deployments`)에서 수행되는지 확인
- [ ] 모델 배포 `dependsOn` — 여러 모델 배포 시 순서 보장 필요

### Medium (권장)
- [ ] `uniqueString(resourceGroup().id)` 사용으로 이름 충돌 방지
- [ ] 리소스 참조로 `dependsOn` 대신 암묵적 의존성 활용
- [ ] 파라미터 파일에 `@secure()` 값이 평문으로 없는지 확인

## 출력 형식

```markdown
## Bicep 코드 리뷰 결과

**✅ 통과**: X개 항목
**⚠️ 경고**: X개 항목
**🔧 자동 수정됨**: X개 항목

### 자동 수정 내용
- `storage.bicep` L42: `isHnsEnabled: false` → `true` (ADLS Gen2 HNS 활성화)
- `network.bicep` L18: `privateEndpointNetworkPolicies` 누락 → `'Disabled'` 추가

### 경고 사항 (수동 확인 권장)
- CognitiveServices apiVersion → 최신 버전 `2025-06-01` 사용 권장

**결론**: 배포 준비 완료 ✅
```
