#!/usr/bin/env python3
"""
AI Client Registry - 자동 조사 스크립트
macOS 로컬 설치형 AI 클라이언트를 조사하고 검증합니다.
"""

import os
import json
import yaml
import requests
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from requests.exceptions import RequestException

# 프로젝트 루트 디렉토리
ROOT_DIR = Path(__file__).parent.parent

# .env 파일이 있으면 로드해 환경변수를 보완한다.
load_dotenv()


def load_cache():
    """기존 캐시 로드"""
    cache_file = ROOT_DIR / "data" / ".ai-tools-cache.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """캐시 저장"""
    cache_file = ROOT_DIR / "data" / ".ai-tools-cache.json"
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def call_openrouter_api(prompt):
    """OpenRouter API를 통해 무료 AI 모델 호출"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY 환경변수가 설정되지 않았습니다")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/ai-client-registry",
            "Content-Type": "application/json"
        },
        json={
            "model": "qwen/qwen-2.5-coder-32b-instruct:free",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 AI 개발 도구 전문가입니다. 정확한 정보만 제공하세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
    )

    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']


def load_survey_prompt():
    """조사용 프롬프트 로드"""
    prompt_file = ROOT_DIR / "prompts" / "survey-prompt.md"
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()


def generate_report(results):
    """마크다운 보고서 생성"""
    report = f"""# AI Client Registry Report

**생성일**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S KST')}  
**검증 도구 수**: {len([r for r in results.values() if r['status'] == 'verified'])}개

## 📊 검증 통계

"""

    # 통계 계산
    verified = [r for r in results.values() if r['status'] == 'verified']
    rejected = [r for r in results.values() if r['status'] == 'rejected']

    cli_tools = [r for r in verified if r['type'] == 'cli']
    desktop_apps = [r for r in verified if r['type'] == 'desktop']
    hybrid_tools = [r for r in verified if r['type'] == 'hybrid']

    report += f"- ✅ 검증됨: {len(verified)}개\n"
    report += f"- ❌ 거부됨: {len(rejected)}개\n"
    report += f"- 💻 CLI 도구: {len(cli_tools)}개\n"
    report += f"- 🖥️ Desktop 앱: {len(desktop_apps)}개\n"
    report += f"- 🔄 하이브리드: {len(hybrid_tools)}개\n\n"

    # 각 카테고리별 상세 정보
    report += "## 💻 CLI 도구\n\n"
    for tool in cli_tools:
        report += f"### {tool['name']}\n"
        report += f"- **공식 사이트**: {tool.get('official_site', 'N/A')}\n"
        report += f"- **설치**: `{tool['installation']['command']}`\n"
        report += f"- **플랫폼**: {', '.join(tool['platforms'])}\n\n"

    report += "## 🖥️ Desktop 애플리케이션\n\n"
    for tool in desktop_apps:
        report += f"### {tool['name']}\n"
        report += f"- **공식 사이트**: {tool.get('official_site', 'N/A')}\n"
        report += f"- **플랫폼**: {', '.join(tool['platforms'])}\n\n"

    report += "## 🔄 하이브리드 도구\n\n"
    for tool in hybrid_tools:
        report += f"### {tool['name']}\n"
        report += f"- **공식 사이트**: {tool.get('official_site', 'N/A')}\n"
        report += f"- **타입**: CLI + IDE Extension\n\n"

    return report


def main():
    print("🔍 AI Client Registry 조사 시작...")

    # 1. 캐시 로드
    cache = load_cache()
    print(f"📦 기존 캐시: {len(cache)}개 도구")

    # 2. 조사 프롬프트 로드
    survey_prompt = load_survey_prompt()

    # 3. AI에게 조사 요청
    print("🤖 AI 조사 중...")
    current_date = datetime.now().strftime('%Y-%m-%d')
    full_prompt = survey_prompt.replace('{current_date}', current_date)
    full_prompt = full_prompt.replace('{cache_count}', str(len(cache)))

    ai_response = None
    try:
        ai_response = call_openrouter_api(full_prompt)
        print("✅ AI 응답 수신 완료")
    except ValueError as exc:
        print(f"⚠️ {exc}")
        print("⚙️ API 호출 없이 기존 캐시 기반으로 보고서를 생성합니다.")
    except RequestException as exc:
        print(f"❌ OpenRouter API 호출 실패: {exc}")
        print("⚙️ API 없이 캐시 데이터로 보고서를 생성합니다.")
    except Exception as exc:
        print(f"❌ 예기치 않은 오류 발생: {exc}")
        raise

    # 4. 결과 파싱 및 병합 (여기서는 간단히 텍스트 저장)
    # 실제로는 JSON 파싱 로직 필요

    # 5. 보고서 생성
    report = generate_report(cache)
    report_file = ROOT_DIR / "docs" / "REPORT.md"
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📄 보고서 생성: {report_file}")

    # 6. 캐시 저장
    save_cache(cache)
    print("💾 캐시 저장 완료")

    if ai_response:
        print("\n✅ 조사 완료!")
    else:
        print("\n✅ 조사 완료 (API 응답 없이 캐시 기반)")


if __name__ == "__main__":
    main()
