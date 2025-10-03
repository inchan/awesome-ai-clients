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

최소 15개 이상의 도구를 조사하고 검증하세요. 범위에 해당하는 모든 후보를 가능한 한 빠짐없이 포함하세요.

### 응답 지침
- 설명이나 코드블록 없이 **순수 JSON만** 반환하세요.
- 출력은 `{` 로 시작하고 `}` 로 끝나는 하나의 JSON 객체여야 합니다.
- JSON 최상위 키는 각각의 도구 이름이어야 합니다.
- 가능한 모든 유효 후보를 포함하되, 각 항목은 중복 없이 한 번만 나열하세요.
- 각 `notes` 값은 100자 이하의 한 문장으로 요약하세요.
