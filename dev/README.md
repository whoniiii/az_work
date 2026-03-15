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
├── SKILL.md                          # 4단계 워크플로우 메인 지침
├── agents/
│   ├── bicep-generator.md            # Phase 2: Bicep 생성 에이전트
│   └── bicep-reviewer.md             # Phase 3: 코드 리뷰 에이전트
├── references/
│   ├── ai-data-services.md           # Azure AI/Data 서비스 Bicep 스니펫
│   └── private-endpoints.md          # Private Endpoint + DNS Zone 패턴
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

| ID | 시나리오 | 핵심 검증 포인트 |
|----|---------|----------------|
| 1 | RAG 챗봇 (Foundry + Search + ADLS + KV) | PE 3종 세트, isHnsEnabled, Foundry Project |
| 2 | 데이터 플랫폼 (Fabric + ADLS + ADF) | Fabric Capacity, ADLS HNS |
| 3 | Microsoft Foundry 완전 private 구성 | Foundry + Project, PE, DNS Zone |

현재 eval 결과: with_skill 100% / without_skill 95%
차별점: `isHnsEnabled` 자동 적용, 다이어그램 일관성

---

## 작업 히스토리

| 날짜 | 작업 |
|------|------|
| 2026-03-14 | 초기 버전 완성, GitHub 연동, 브랜치 전략 수립 |
