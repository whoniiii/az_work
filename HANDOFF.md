# 인수인계 — azure-arch-builder 스킬 개발 컨텍스트

> Claude Code CLI에서 이 파일을 먼저 읽고 작업을 이어가세요.

---

## 프로젝트 한 줄 요약

ISD AI/Data 컨설턴트가 "AI Search랑 Foundry 만들고 싶어" 라고 말하면,
대화형으로 아키텍처를 설계하고 → Bicep 생성 → 코드 리뷰 → Azure 실제 배포까지 이어주는
**Claude 멀티에이전트 스킬**을 개발 중이다.

---

## 지금까지 완성된 것

### 파일 구조
```
azure-arch-builder/
├── SKILL.md                      ← 핵심. 4단계 워크플로우 전체 정의
├── HANDOFF.md                    ← 지금 이 파일
├── README.md                     ← GitHub용 설치 가이드
├── .gitignore
├── references/
│   ├── ai-data-services.md       ← Azure AI/Data 서비스 Bicep 스니펫 모음
│   ├── private-endpoints.md      ← Private Endpoint + DNS Zone 패턴
│   └── diagram-guide.md          ← 다이어그램 생성 가이드 (diagrams 라이브러리)
├── scripts/
│   ├── generate_html_diagram.py  ← 인터랙티브 HTML 다이어그램 생성기 (핵심 스크립트)
│   └── generate_diagram.py       ← PNG 다이어그램 생성기 (fallback)
└── agents/
    └── bicep-reviewer.md         ← Bicep 코드 리뷰 에이전트 지침
```

### 스킬 4단계 워크플로우 (SKILL.md 기준)

| Phase | 역할 | 상태 |
|-------|------|------|
| 1. 아키텍처 어드바이저 | 자연어 → 초안 제안 + HTML 다이어그램 + 대화로 확정 | ✅ 완성 |
| 2. Bicep 생성 에이전트 | 확정된 스펙 → Bicep IaC 코드 생성 | ✅ 완성 |
| 3. Bicep 리뷰 에이전트 | 보안/완전성/모범사례 자동 검토 및 수정 | ✅ 완성 |
| 4. 배포 에이전트 | az deployment what-if → 사용자 확인 → 실제 배포 | ✅ 완성 |

### 특화 Azure 서비스
- Azure OpenAI (gpt-4o, text-embedding)
- Azure AI Foundry Hub + Project (kind: Hub / kind: Project)
- Azure AI Search (Semantic Ranking, 벡터 검색)
- Microsoft Fabric (Capacity F SKU)
- ADLS Gen2 (`isHnsEnabled: true` 필수!)
- Key Vault, ADF, AML, ACR
- VNet + Private Endpoint + Private DNS Zone 전체 패턴

---

## 다음에 할 일 (우선순위 순)

### 1순위: GitHub 연동 설정
```bash
git init
git branch -m main
git add .
git commit -m "feat: Azure AI/Data 멀티에이전트 아키텍처 빌더 스킬 초기 버전"
git remote add origin https://github.com/<username>/azure-arch-builder.git
git push -u origin main
```

### 2순위: `agents/bicep-generator.md` 파일 추가
SKILL.md에서 참조하지만 아직 파일이 없음. 내용:
- Bicep 생성 시 참조할 세부 지침
- `references/ai-data-services.md`와 `references/private-endpoints.md` 활용법
- 모듈별 책임 범위 정의

### 3순위: 실제 사용 테스트
Claude Code CLI에서 직접 실행해보고 개선:
```
"AI Search랑 Foundry Hub 만들어줘, private endpoint 포함해서"
```
- Phase 1 HTML 다이어그램이 잘 뜨는지
- Phase 2 Bicep이 실제로 배포 가능한 수준인지 `az deployment validate`로 확인
- Phase 4 실제 Azure 구독에서 배포 테스트

### 4순위: 스킬 트리거 최적화 (선택)
```bash
# skill-creator의 description optimizer 실행
cd ~/.claude/skills/skill-creator  # 또는 스킬 크리에이터 경로
python -m scripts.run_loop \
  --skill-path ../azure-arch-builder \
  --model claude-sonnet-4-6 \
  --max-iterations 5
```

---

## 알아두면 좋은 것들

### 핵심 파일: `scripts/generate_html_diagram.py`
- Python 순수 구현, 외부 라이브러리 불필요
- `--services` JSON에 서비스 목록, `--connections` JSON에 연결 관계 넘기면 HTML 생성
- Private 서비스는 자동으로 VNet 점선 박스로 묶임
- 노드 드래그 가능, 사이드바에 서비스 목록

### ADLS Gen2 흔한 실수
`isHnsEnabled: true` 없으면 일반 Blob Storage가 됨 → Fabric, Synapse, Databricks 연결 시 문제 발생.
SKILL.md와 references/ai-data-services.md에 이 내용 강조되어 있음.

### Private Endpoint 3종 세트
아래 3개가 세트로 있어야 DNS 해석이 됨:
1. `Microsoft.Network/privateEndpoints`
2. `Microsoft.Network/privateDnsZones` + VNet Link
3. `Microsoft.Network/privateEndpoints/privateDnsZoneGroups`

### 배포 방식
`azd up`은 앱 배포 중심이라 순수 인프라 Bicep에는 `az deployment group create`가 더 적합.
`az deployment group what-if` → 사용자 확인 → `az deployment group create` 순서.

---

## 개발 컨텍스트

- **개발자**: jeonghoon (jhlee8024@gmail.com) — Microsoft ISD AI/Data 컨설턴트
- **개발 환경**: Cowork (Claude Desktop) → Claude Code CLI로 이관 중
- **스킬 저장 위치**: `~/.claude/skills/azure-arch-builder/` 또는 프로젝트 `.claude/skills/`
- **eval 결과**: with_skill 100%, without_skill 95% (isHnsEnabled, 다이어그램 일관성이 핵심 차별점)
