# Architecture Guidance Sources (설계 방향 판단용)

Azure 공식 아키텍처 가이던스를 **설계 방향 판단**에만 사용하기 위한 source registry.

> **이 문서의 URL은 "어디를 보면 되는지"의 출처 목록이다.**
> URL 안의 내용을 고정 사실로 하드코딩하지 않는다.
> SKU, API version, region, model availability, PE mapping 결정에는 사용하지 않는다 — 그것은 `azure-dynamic-sources.md` 경로로만 처리한다.

---

## 목적 분리

| 목적 | 사용 문서 | 결정 가능 항목 |
|------|----------|---------------|
| **설계 방향 판단** | 이 문서 (architecture-guidance-sources) | 아키텍처 패턴, best practice, 서비스 조합 방향, 보안 경계 설계 |
| **배포 스펙 확인** | `azure-dynamic-sources.md` | API version, SKU, region, model availability, PE groupId, 실제 속성값 |

**이 문서로 결정하면 안 되는 것:**
- API version
- SKU 이름/가격
- region 가용성
- 모델명/버전/배포 타입
- PE groupId / DNS Zone 매핑
- 리소스 속성의 구체적 값

---

## Primary Sources

설계 방향 판단 시 targeted fetch 대상.

| ID | 문서 | URL | 용도 |
|----|------|-----|------|
| A1 | Azure Architecture Center | https://learn.microsoft.com/en-us/azure/architecture/ | 허브 — 특정 도메인 문서를 찾을 때 진입점 |
| A2 | Well-Architected Framework | https://learn.microsoft.com/en-us/azure/architecture/framework/ | 보안/안정성/성능/비용/운영 원칙 |
| A3 | Cloud Adoption Framework / Landing Zone | https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone/ | enterprise 거버넌스, 네트워크 토폴로지, 구독 구조 |
| A4 | Azure AI/ML Architecture | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/ | AI/ML 워크로드 reference architecture 허브 |
| A5 | Basic Foundry Chat Reference Architecture | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/basic-azure-ai-foundry-chat | Foundry 기반 챗봇 기본 구조 |
| A6 | Baseline AI Foundry Chat Reference Architecture | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-openai-e2e-chat | Foundry 챗봇 enterprise baseline (네트워크 격리 포함) |
| A7 | RAG Solution Design Guide | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide | RAG 패턴 설계 가이드 |
| A8 | Microsoft Fabric Overview | https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview | Fabric 플랫폼 개요 및 워크로드 이해 |
| A9 | Fabric Governance / Adoption | https://learn.microsoft.com/en-us/power-bi/guidance/fabric-adoption-roadmap-governance | Fabric 거버넌스, 도입 로드맵 |

## Secondary Sources (awareness only)

직접 fetch 대상이 아니라, 변경 사항 인지용으로만 참조.

| 문서 | URL | 비고 |
|------|-----|------|
| Azure Updates | https://azure.microsoft.com/en-us/updates/ | 서비스 변경/신규 기능 공지. targeted fetch 대상 아님 |

---

## Fetch Trigger — 언제 조회하는가

아키텍처 가이던스 문서는 **매 요청마다 조회하지 않는다.** 아래 트리거에 해당할 때만 targeted fetch한다.

### 트리거 조건

0. **Phase 1에서 사용자의 워크로드 유형이 파악되었을 때 (자동)**
   - 해당 워크로드의 reference architecture를 사전 조회하여 질문 깊이를 조정
   - 사용자가 "best practice" 등을 명시하지 않아도 자동 발동
   - 목적: SKU/region 스펙 질문 외에, 공식 아키텍처 기반 설계 판단 포인트를 질문에 반영
1. **사용자가 설계 방향 근거를 요구할 때**
   - "best practice", "reference architecture", "권장 구조", "baseline", "well-architected", "landing zone", "enterprise pattern" 등의 키워드
2. **새로운 서비스 조합의 아키텍처 경계가 애매할 때**
   - 기존 domain-packs/service-gotchas로 판단이 안 되는 서비스 간 관계
3. **enterprise 수준 보안/거버넌스 설계가 필요할 때**
   - 구독 구조, 네트워크 토폴로지, landing zone 패턴

### 트리거에 해당하지 않는 경우

- 단순 리소스 생성 (SKU/API version/region 질문) → `azure-dynamic-sources.md`만 사용
- 이미 domain-packs에 패턴이 있는 서비스 조합 → reference 파일 우선
- Bicep 속성값 확인 → `service-gotchas.md` 또는 MS Docs Bicep reference

---

## Fetch Budget

| 상황 | 최대 fetch 수 |
|------|-------------|
| 기본 (트리거 발생 시) | 아키텍처 가이던스 문서 **최대 2개** |
| 추가 조회 허용 조건 | 문서 간 충돌 / 핵심 설계 불확실성 잔존 / 사용자가 더 깊은 근거를 명시적으로 요구 |
| 단순 배포 스펙 질문 | **0개** (architecture guidance 조회 안 함) |

---

## 질문 유형별 Decision Rule

| 질문 유형 | 조회할 문서 | 추출할 설계 판단 포인트 | 조회하지 않을 문서 |
|----------|-----------|---------------------|-----------------|
| RAG / chatbot / Foundry app | A5 또는 A6 + A7 | 네트워크 격리 수준, 인증 방식(managed identity vs key), 인덱싱 전략(push vs pull), 모니터링 범위 | 전체 Architecture Center 순회 금지 |
| Enterprise security / governance / landing zone | A2 + A3 | 구독 구조, 네트워크 토폴로지(hub-spoke 등), ID/거버넌스 모델, 보안 경계 | AI/ML 도메인 문서 불필요 |
| Fabric data platform | A8 + A9 | 용량 모델(SKU 선택 기준), 거버넌스 수준, 데이터 경계(workspace 분리 등) | AI 관련 문서 불필요 |
| 애매한 서비스 조합 (패턴 불명확) | A1 (허브에서 가장 가까운 도메인 문서 1개 탐색) + 해당 문서 1개 | 문서에서 식별되는 주요 설계 결정 포인트 | 하위 문서 전체 순회 금지 |
| 단순 리소스 생성값 (SKU/API/region) | 조회 안 함 | — | architecture guidance 전체 |
| AI/ML 일반 아키텍처 | A4 (허브) + 가장 가까운 reference architecture 1개 | 컴퓨팅 격리, 데이터 경계, 모델 서빙 방식 | 전체 crawl 금지 |

---

## URL Fallback Rule

1. `en-us` Learn URL을 기본 사용
2. 특정 URL이 404 / 리다이렉트 / 폐기된 경우 → 상위 허브 페이지로 fallback
   - 예: A5가 실패 → A4 (AI/ML 허브)에서 "foundry chat" 키워드로 탐색
3. 상위 허브에서도 찾을 수 없으면 → A1 (Architecture Center 메인)에서 제목 키워드 검색
4. **URL이 있다고 해서 그 내용의 값을 고정 규칙처럼 사용하지 않는다**

---

## 전체 탐색 금지

- Architecture Center 하위 문서를 광범위하게 순회(crawl)하지 않는다
- 질문 유형별 decision rule에 따라 관련 문서 1~2개만 targeted fetch
- fetch한 문서 내에서도 관련 섹션만 참고하고, 전체를 정독하지 않는다
- 무제한 fetch, 재귀적 링크 따라가기, 하위 페이지 열거를 금지한다
