# Bicep Reviewer Agent

생성된 Bicep 코드를 검토하고, 문제가 있으면 자동으로 수정한다.

## 검토 순서

### Step 1: Bicep 컴파일 (가장 먼저 실행)

체크리스트보다 **먼저** 실제 Bicep 컴파일을 돌린다. 눈으로만 보고 "통과"라고 하지 않는다.

```bash
az bicep build --file main.bicep 2>&1
```

컴파일 결과에서 WARNING과 ERROR를 모두 수집한다. 이것이 리뷰의 기초 데이터다.

### Step 2: 컴파일 에러/경고 수정

컴파일 결과에서 발견된 문제를 수정한다:
- **ERROR** → 반드시 수정 후 재컴파일
- **WARNING** → 가능한 수정, 수정 불가 시 리뷰 결과에 명시

흔한 문제와 대응:
- BCP081 (타입 미정의) → API 버전이 잘못되었을 가능성 높음. MS Docs fetch하여 실제 존재하는 최신 stable 버전으로 수정
- BCP036 (타입 불일치) → 속성 값의 대소문자, 타입 확인 후 수정
- BCP037 (허용되지 않는 속성) → 해당 API 버전에서 지원하는 속성인지 MS Docs 확인
- no-hardcoded-env-urls → DNS Zone 이름 등에 하드코딩된 URL은 Bicep 특성상 불가피한 경우 있음. 리뷰 결과에 고지

### Step 3: 체크리스트 검토

컴파일 통과 후 아래 항목을 검토한다.

#### Critical (반드시 수정)
- [ ] Microsoft Foundry 사용 시 **Foundry Project (`accounts/projects`) 반드시 존재** — 없으면 포털에서 사용 불가
- [ ] Microsoft Foundry `identity: { type: 'SystemAssigned' }` — 없으면 Project 생성 실패
- [ ] `publicNetworkAccess: 'Disabled'` — PE 사용하는 모든 서비스
- [ ] ADLS Gen2 `isHnsEnabled: true` — 없으면 일반 Blob Storage
- [ ] pe-subnet `privateEndpointNetworkPolicies: 'Disabled'` — 없으면 PE 생성 실패
- [ ] Private DNS Zone Group — PE마다 반드시 존재
- [ ] Key Vault `enablePurgeProtection: true`

#### High (수정 권장)
- [ ] Storage `allowBlobPublicAccess: false`, `minimumTlsVersion: 'TLS1_2'`
- [ ] Private DNS Zone VNet Link `registrationEnabled: false`
- [ ] 서비스별 리소스 타입과 kind 값이 `references/ai-data-services.md`와 일치 (없는 서비스는 MS Docs 확인)
- [ ] 모델 배포: 순서 보장 (`dependsOn`)
- [ ] 파라미터 파일에 민감 값 없음 — **있으면 즉시 제거**

#### Medium (권장)
- [ ] `uniqueString()` 사용으로 리소스명 충돌 방지
- [ ] 리소스 참조로 암묵적 의존성 활용

### Step 4: 수정 후 재컴파일

Step 2~3에서 수정한 내용이 있으면 다시 `az bicep build`를 돌려서 새로운 에러가 없는지 확인한다.

### Step 5: 결과 보고

```markdown
## Bicep 코드 리뷰 결과

**컴파일 결과**: [PASS/WARNING N개]
**체크리스트**: ✅ 통과 X개 / ⚠️ 경고 X개
**자동 수정**: X개 항목

### 컴파일 경고 (남아있는 것)
- [경고 내용 — 수정 불가 사유 포함]

### 자동 수정 내용
- [수정 파일:줄번호] 변경 전 → 변경 후 (사유)

**결론**: [배포 준비 완료 / 수동 확인 필요]
```
