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

### Cowork에서 사용

```bash
# 1. 이 저장소 클론
git clone https://github.com/<your-org>/azure-arch-builder

# 2. 스킬 폴더에 복사
cp -r azure-arch-builder ~/.claude/skills/
# 또는 프로젝트별로
cp -r azure-arch-builder .claude/skills/
```

또는 `.skill` 패키지 파일로 설치:
```bash
# skill 파일 빌드 (Cowork에서)
cd azure-arch-builder
python -m scripts.package_skill . ../

# 생성된 azure-arch-builder.skill 파일을 Cowork에서 "Copy to your skills"로 설치
```

### Claude Code CLI에서 사용

```bash
# 개인 전역 설치
mkdir -p ~/.claude/skills
git clone https://github.com/<your-org>/azure-arch-builder ~/.claude/skills/azure-arch-builder

# 또는 프로젝트 로컬 설치
mkdir -p .claude/skills
git clone https://github.com/<your-org>/azure-arch-builder .claude/skills/azure-arch-builder
```

---

## 업데이트

```bash
# 스킬이 설치된 위치에서
cd ~/.claude/skills/azure-arch-builder
git pull
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
