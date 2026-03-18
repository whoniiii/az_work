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

컴파일 통과 후 아래 항목을 검토한다. 전체 gotchas는 `references/service-gotchas.md` 참조.

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
- [ ] 서비스별 리소스 타입과 kind 값이 `references/domain-packs/ai-data.md` 또는 MS Docs와 일치
- [ ] 모델 배포: 순서 보장 (`dependsOn`)
- [ ] 파라미터 파일에 민감 값 없음 — **있으면 즉시 제거**

#### Medium (권장)
- [ ] `uniqueString()` 사용으로 리소스명 충돌 방지
- [ ] 리소스 참조로 암묵적 의존성 활용

### Step 4: 하드코딩 회귀 검사 (Dynamic 정보 누출 방지)

아래 항목이 Bicep 코드에 리터럴 값으로 박혀 있지 않은지 확인한다:

#### 반드시 파라미터화 (하드코딩 금지)
- [ ] `location` — 리터럴 지역명(`'eastus'`, `'koreacentral'` 등)이 직접 사용되지 않고 `param location`으로 전달
- [ ] 모델명/버전 — 리터럴이 아닌, Phase 1에서 확정하고 Step 0에서 가용성 확인된 값 사용
- [ ] SKU — 사용자와 확인된 값 사용

#### Dynamic 값이 Reference에 회귀하지 않았는지
이 리뷰에서 직접 체크할 범위는 아니지만, 만약 코드 내 주석이나 파라미터 설명에 특정 API version, SKU 목록, region 목록을 하드코딩했다면 제거하고 "MS Docs 확인" 안내로 교체한다.

#### Decision Rule 위반 체크
- [ ] Foundry 대신 `kind: 'OpenAI'`를 사용한 경우 → 사용자 명시 요청이 아니면 `kind: 'AIServices'`로 수정
- [ ] 일반 AI/RAG에 Hub(`MachineLearningServices`)를 사용한 경우 → 사용자 명시 요청이 아니면 Foundry로 수정
- [ ] standalone Azure OpenAI resource를 사용한 경우 → 사용자 명시 요청 또는 Docs상 필요한 경우가 아니면 Foundry 사용 검토 안내

### Step 5: 수정 후 재컴파일

Step 2~4에서 수정한 내용이 있으면 다시 `az bicep build`를 돌려서 새로운 에러가 없는지 확인한다.

### `az bicep build`의 한계

컴파일은 문법과 타입만 검증한다. 아래 항목은 컴파일로 잡을 수 없으므로, Phase 4의 `az deployment group what-if`에서 최종 검증된다:
- retired/unavailable SKU
- 지역별 서비스 가용성
- 모델명 유효성
- preview 전용 속성
- 서비스 정책 변경 (quota, capacity 등)

리뷰 결과에 이 한계를 명시하여 사용자가 what-if 단계의 중요성을 인지하도록 한다.

### Step 6: 결과 보고

```markdown
## Bicep 코드 리뷰 결과

**컴파일 결과**: [PASS/WARNING N개]
**체크리스트**: ✅ 통과 X개 / ⚠️ 경고 X개
**하드코딩 검사**: [PASS / 위반 N개]
**자동 수정**: X개 항목

### 컴파일 경고 (남아있는 것)
- [경고 내용 — 수정 불가 사유 포함]

### 자동 수정 내용
- [수정 파일:줄번호] 변경 전 → 변경 후 (사유)

### 하드코딩 위반 (있는 경우)
- [파일:줄번호] [위반 내용] → [수정 방법]

**결론**: [배포 준비 완료 / 수동 확인 필요]
```
