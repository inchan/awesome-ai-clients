# AI Client Registry 🤖

> 자동화된 로컬 설치형 AI 클라이언트 검증 및 추적 시스템

[
[

## 📋 개요

macOS 환경에서 **독립 실행 가능한** AI 클라이언트(CLI 도구 및 Desktop 앱)를 자동으로 조사하고 검증합니다.
- IDE 플러그인 형태 제외
- 공식 소스 검증
- 주간 자동 업데이트

## 🛠️ 검증된 도구

### CLI 도구 (7개)
- Claude Code
- GitHub Copilot CLI
- Gemini CLI
- Aider
- Continue CLI
- LLM CLI (simonw)
- CodeWhisperer CLI

### Desktop 애플리케이션 (6개)
- Claude Desktop
- ChatGPT Desktop
- Perplexity Desktop
- Cursor
- Windsurf
- Replit Desktop

### 하이브리드 (2개)
- Continue
- Cline

[📊 전체 보고서 보기](docs/REPORT.md)

## 🔄 자동화

- **주기**: 매주 월요일 오전 9시 (UTC)
- **엔진**: GitHub Actions + OpenRouter API (무료)
- **검증**: 공식 소스, 설치 방법, 독립 실행 여부

## 📖 사용법

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/ai-client-registry.git
cd ai-client-registry

# 로컬 실행
pip install -r scripts/requirements.txt
export OPENROUTER_API_KEY="your-key"
python scripts/survey_ai_clients.py
```

## 🤝 기여

새로운 AI 클라이언트를 발견하셨나요? Issue 또는 PR을 열어주세요!

## 📄 라이선스

MIT License
