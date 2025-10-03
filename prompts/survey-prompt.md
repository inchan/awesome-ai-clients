# macOS 로컬 AI 클라이언트 조사 프롬프트

현재 날짜: {current_date}
기존 캐시: {cache_count}개 도구

## 작업 요청

macOS 환경에서 **독립 실행 가능한** AI 클라이언트를 조사하고 검증하세요.

### 조건
- ✅ CLI 도구 또는 Desktop 애플리케이션
- ✅ 로컬 설치 가능
- ✅ IDE 없이 독립 실행 가능
- ❌ IDE 플러그인만 제공하는 도구 제외

### 검색 전략

1. **1차 검색**
   - "AI CLI tools 2025"
   - "AI coding assistant desktop apps"
   - "LLM command line interface"

2. **공식 소스 확인**
   - 공식 웹사이트 URL
   - GitHub 저장소
   - 공식 문서

3. **심화 검색** (플러그인으로 보이는 경우)
   - npm 패키지 검색: `@org/tool-cli`
   - GitHub CLI 프로젝트
   - 공식 문서의 CLI 섹션

### 출력 형식

JSON 형식으로 반환:

```json
{
  "tool_name": {
    "status": "verified|rejected",
    "type": "cli|desktop|hybrid",
    "official_site": "URL",
    "github": "URL|null",
    "installation": {
      "method": "npm|pip|brew|direct",
      "command": "설치 명령어"
    },
    "platforms": ["macOS", "Windows", "Linux"],
    "is_standalone": true,
    "verified_date": "2025-10-04",
    "notes": "설명"
  }
}
```

최소 15개 이상의 도구를 조사하고 검증하세요.
