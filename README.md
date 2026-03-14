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

Claude Code에서 원하는 Azure 인프라를 자연어로 요청하면 됩니다.

```
"AI Search랑 Foundry Hub 만들어줘, private endpoint 포함해서"
"RAG 챗봇 아키텍처 구성해줘"
"Azure에 데이터 레이크하우스 올려줘"
```

이후 Claude가 단계별로 안내합니다:

1. **아키텍처 제안** — 서비스 구성 초안 + 인터랙티브 다이어그램 제시
2. **대화로 확정** — 서비스, SKU, 네트워킹 방식 조정
3. **Bicep 생성** — 배포 가능한 IaC 코드 자동 작성
4. **코드 리뷰** — 보안/완전성/모범사례 자동 검토 및 수정
5. **Azure 배포** — what-if 확인 후 실제 배포

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

## 사전 요구사항

- [Claude Code CLI](https://claude.ai/code) 설치
- Azure CLI (`az`) 설치 및 로그인 (`az login`)

---

## 라이선스

MIT
