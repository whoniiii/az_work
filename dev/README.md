# azure-arch-builder — 개발자 가이드

> 이 폴더는 `dev` 브랜치 전용. `main`(고객 배포용)에 포함하지 않는다.

---

## 프로젝트 목적

ISD AI/Data 컨설턴트가 고객사 Azure AI/Data 인프라를 빠르게 설계하고 배포할 수 있도록
자연어 → 아키텍처 설계 → Bicep 생성 → 코드 리뷰 → 실제 배포까지 이어주는 Claude Code 스킬.

---

## 브랜치 전략

| 브랜치 | 용도 |
|--------|------|
| `dev` | 개발, 실험, eval 작업 |
| `main` | 고객 배포용 — PR로만 머지 |

- `dev`에서 작업 → 검증 완료 → `main`으로 PR (이 `dev/` 폴더는 PR에서 제외)

---

## 스킬 구조

```
az_work/
├── SKILL.md                          # 4단계 워크플로우 메인 지침 + v1 scope + fallback 정의
├── agents/
│   ├── bicep-generator.md            # Phase 2: Bicep 생성 에이전트 (Stable/Dynamic 원칙 + fallback)
│   └── bicep-reviewer.md             # Phase 3: 코드 리뷰 에이전트 (하드코딩 회귀 검사 포함)
├── references/
│   ├── azure-common-patterns.md      # PE/보안/명명 공통 패턴 (Stable)
│   ├── azure-dynamic-sources.md      # MS Docs URL 레지스트리 (Dynamic source)
│   ├── service-gotchas.md            # 필수 속성, 흔한 실수, PE 매핑 (Stable)
│   └── domain-packs/
│       └── ai-data.md                # AI/Data 서비스 구성 가이드 (v1 도메인)
└── scripts/
    └── generate_html_diagram.py      # 인터랙티브 HTML 다이어그램 생성기
```

---

## 핵심 주의사항

### ADLS Gen2
`isHnsEnabled: true` 없으면 일반 Blob Storage → Fabric, Synapse, Databricks 연결 불가.

### Private Endpoint 3종 세트
아래 3개가 세트로 있어야 DNS 해석 됨:
1. `Microsoft.Network/privateEndpoints`
2. `Microsoft.Network/privateDnsZones` + VNet Link (`registrationEnabled: false`)
3. `Microsoft.Network/privateEndpoints/privateDnsZoneGroups`

### Microsoft Foundry
- Foundry resource: `kind: 'AIServices'` + `allowProjectManagement: true`
- Foundry Project (`accounts/projects`) 반드시 함께 생성 — 없으면 포털 사용 불가
- 레거시 Hub 기반(`MachineLearningServices`)은 ML 전용

### 서비스 지역 가용성
서비스별 지역 지원은 수시로 변경된다. 지역을 하드코딩하지 말고 MS Docs에서 확인할 것.

---

## eval

테스트 케이스는 `dev/evals.json` 참조.

| ID | 카테고리 | 시나리오 | 핵심 검증 포인트 |
|----|---------|---------|----------------|
| 1 | v1-core | RAG 챗봇 (Foundry + Search + ADLS + KV) | PE 3종 세트, isHnsEnabled, Foundry Project, API fetch |
| 2 | v1-core | 데이터 플랫폼 (Fabric + ADLS + ADF) | Fabric Capacity, ADLS HNS, PE groupId |
| 3 | v1-core | Foundry 완전 private 구성 | Foundry + Project, PE, DNS Zone |
| 4 | decision-rule | "Azure OpenAI로" 요청 | Decision Rule: AIServices 기본 제안 |
| 5 | decision-rule | AI Hub ML 훈련 환경 | Hub 적절 판단 + 의존성 완비 |
| 6 | fallback | AKS + Key Vault | Fallback 고지 + MS Docs fetch |
| 7 | fallback | SQL Database + App Service | 범위 밖 2개 서비스 동시 fallback |
| 8 | stable-vs-dynamic | 사용자가 API 버전 지정 | fetch로 검증, 맹목 수용 안 함 |
| 9 | hardcoding-regression | 하드코딩된 Bicep 리뷰 | location/kind/API version 회귀 감지 |

---

## 작업 히스토리

| 날짜 | 작업 |
|------|------|
| 2026-03-14 | 초기 버전 완성, GitHub 연동, 브랜치 전략 수립 |
