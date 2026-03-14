# azure-arch-builder

> Azure AI/Data 인프라를 자연어로 설계하고 자동 배포까지 이어주는 Claude 스킬

## 어떻게 동작하나요?

```
"AI Search랑 Foundry 만들고 싶어"
        ↓
[1] 아키텍처 초안 제안 + 인터랙티브 HTML 다이어그램
        ↓ (대화로 확정)
[2] Bicep IaC 자동 생성 (main.bicep + modules/)
        ↓
[3] 코드 자동 리뷰 (보안/완전성/모범사례)
        ↓ (사용자 확인)
[4] Azure 실제 배포 (az deployment, 단계별 보고)
```

**특화 영역**: Azure OpenAI, AI Foundry Hub/Project, AI Search, Microsoft Fabric, ADLS Gen2, AML, Key Vault + Private Endpoint 전체 구성

---

## 설치

### 전역 설치 (모든 프로젝트에서 사용)

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/whoniiii/az_work ~/.claude/skills/azure-arch-builder
```

### 프로젝트 로컬 설치 (특정 프로젝트에만 적용)

`.claude` 폴더는 `/init` 같은 별도 명령 없이 그냥 직접 만들면 됩니다.

```bash
# 프로젝트 루트에서
mkdir -p .claude/skills
git clone https://github.com/whoniiii/az_work .claude/skills/azure-arch-builder
```

> **`.claude` 폴더란?** Claude Code가 자동으로 인식하는 프로젝트 설정 폴더입니다.
> `/init`은 `CLAUDE.md`(프로젝트 지침 파일)를 만드는 명령이라 스킬 설치와는 별개입니다.
> 스킬은 `.claude/skills/<스킬명>/SKILL.md` 경로만 맞으면 자동으로 로드됩니다.

---

## 업데이트

```bash
# 전역 설치한 경우
cd ~/.claude/skills/azure-arch-builder && git pull

# 프로젝트 로컬 설치한 경우
cd .claude/skills/azure-arch-builder && git pull
```

---

## 파일 구조

```
azure-arch-builder/
├── SKILL.md                          # 메인 스킬 지침 (4단계 워크플로우)
├── references/
│   ├── ai-data-services.md           # Azure AI/Data 서비스 Bicep 스니펫
│   ├── private-endpoints.md          # Private Endpoint 패턴 & DNS Zone 매핑
│   └── diagram-guide.md              # 다이어그램 생성 가이드
├── scripts/
│   ├── generate_html_diagram.py      # 인터랙티브 HTML 아키텍처 다이어그램 생성
│   └── generate_diagram.py           # PNG 다이어그램 생성 (diagrams 라이브러리)
└── agents/
    ├── bicep-generator.md            # Bicep 생성 에이전트 지침
    └── bicep-reviewer.md             # Bicep 코드 리뷰 에이전트 지침
```

---

## 지원 시나리오

| 시나리오 | 서비스 조합 |
|---------|-----------|
| RAG 챗봇 | Azure OpenAI + AI Search + ADLS Gen2 + Key Vault |
| AI Foundry Hub | AI Hub + AI Project + OpenAI + Search + Storage |
| Data Lakehouse | Microsoft Fabric + ADLS Gen2 + ADF |
| ML Platform | Azure ML + ADLS Gen2 + Key Vault + ACR |

모든 구성에 **Private Endpoint + Private DNS Zone** 자동 적용.

---

## 기여

1. `fork` → `feature/xxx` 브랜치에서 수정
2. SKILL.md 또는 references/ 파일 업데이트
3. Pull Request 생성

## 라이선스

MIT
