# azure-arch-builder

> Azure AI/Data 인프라를 자연어로 설계하고 자동 배포까지 이어주는 Claude Code 스킬

"AI Search랑 Foundry 만들고 싶어" 라고 말하면, 대화를 통해 아키텍처를 확정하고 Bicep 코드 생성부터 실제 Azure 배포까지 자동으로 진행합니다.

---

## 설치

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/whoniiii/az_work ~/.claude/skills/azure-arch-builder
```

---

## 사용법

설치 후 프로젝트 폴더에서 Claude Code를 실행합니다.

```bash
cd your-project
claude
```

Azure 인프라 관련 요청을 하면 스킬이 자동으로 발동됩니다. 별도 명령어 없이 자연어로 말하면 됩니다.

```
"AI Search랑 Microsoft Foundry 만들어줘, private endpoint 포함해서"
"RAG 챗봇 아키텍처 구성해줘"
"Azure에 데이터 레이크하우스 올려줘"
```

이후 Claude가 단계별로 안내합니다:

1. **요구사항 수집** — 필요한 정보를 질문하여 아키텍처 구성 확정
2. **다이어그램 생성** — 인터랙티브 HTML 아키텍처 다이어그램 제시
3. **대화로 조정** — 서비스, SKU, 네트워킹 방식 수정 반영
4. **Bicep 생성** — MS Docs에서 최신 API 버전 확인 후 IaC 코드 자동 작성
5. **코드 리뷰** — 보안/완전성/모범사례 자동 검토 및 수정
6. **Azure 배포** — What-if 검증 → 확정 다이어그램 재생성 → 실제 배포

---

## 특징

- **최신 정보 기반**: API 버전, 서비스 명칭, 속성 등을 MS Docs에서 실시간 확인하여 적용
- **보안 우선**: Private Endpoint, 민감 정보 파일 저장 금지 등 보안 원칙 내장
- **대화형 설계**: 사용자와 대화하며 점진적으로 아키텍처 확정
- **단계별 승인**: 모든 주요 단계에서 사용자 확인 후 진행

---

## 지원 서비스

Azure AI/Data 관련 서비스를 자유롭게 조합할 수 있습니다. v1 범위 밖 서비스도 MS Docs 기반 fallback으로 대응합니다. 서비스별 상세 정보는 `references/domain-packs/ai-data.md`, 필수 속성과 PE 매핑은 `references/service-gotchas.md`를 참조합니다.

모든 구성에 **Private Endpoint + Private DNS Zone** 자동 적용 가능.

---

## 사전 요구사항

- [Claude Code CLI](https://claude.ai/code) 설치
- Azure CLI (`az`) 설치 및 로그인 (`az login`)

---

## 라이선스

MIT
