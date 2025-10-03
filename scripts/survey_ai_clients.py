#!/usr/bin/env python3
"""
AI Client Registry - 자동 조사 스크립트
macOS 로컬 설치형 AI 클라이언트를 조사하고 검증합니다.
"""

import argparse
import json
import os
import re
from typing import Dict, Any

import requests
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from requests.exceptions import RequestException

import verifier

# 프로젝트 루트 디렉토리
ROOT_DIR = Path(__file__).parent.parent

# .env 파일이 있으면 로드해 환경변수를 보완한다.
load_dotenv()

REJECTED_LOG_FILE = ROOT_DIR / "data" / "rejected-candidates.jsonl"


def load_cache() -> Dict[str, Any]:
    """기존 캐시 로드"""
    cache_file = ROOT_DIR / "data" / ".ai-tools-cache.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for name, entry in data.items():
                entry.setdefault("name", name)
            return data
    return {}


def load_seed_tools() -> Dict[str, Any]:
    """프로젝트가 신뢰하는 초기 검증 도구 목록 로드"""
    seed_file = ROOT_DIR / "data" / "seed-tools.json"
    if not seed_file.exists():
        return {}
    with open(seed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for name, entry in data.items():
        entry.setdefault("name", name)
    return data


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
            "temperature": 0.1,
            "max_tokens": 6000
        }
    )

    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Client Registry survey")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="API 호출을 건너뛰고 캐시/시드 데이터로만 보고서를 생성",
    )
    parser.add_argument(
        "--no-rejected-log",
        action="store_true",
        help="거부 후보를 파일로 남기지 않습니다",
    )
    return parser.parse_args()


def load_survey_prompt():
    """조사용 프롬프트 로드"""
    prompt_file = ROOT_DIR / "prompts" / "survey-prompt.md"
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()


def parse_ai_response(raw_text):
    """OpenRouter 응답에서 JSON 객체를 추출한다."""
    if not raw_text:
        return {}

    match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL | re.IGNORECASE)
    candidate = match.group(1) if match else raw_text

    start = candidate.find('{')
    end = candidate.rfind('}')
    if start == -1 or end == -1:
        print("⚠️ JSON 본문을 찾지 못했습니다.")
        return {}

    candidate = candidate[start:end + 1]

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        print(f"⚠️ JSON 파싱 실패: {exc}")
        return {}

    if not isinstance(data, dict):
        print("⚠️ JSON 루트가 객체가 아닙니다.")
        return {}

    for name, entry in data.items():
        if isinstance(entry, dict):
            entry.setdefault("name", name)

    return data


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

    cli_tools = sorted((r for r in verified if r['type'] == 'cli'), key=lambda t: t['name'])
    desktop_apps = sorted((r for r in verified if r['type'] == 'desktop'), key=lambda t: t['name'])
    hybrid_tools = sorted((r for r in verified if r['type'] == 'hybrid'), key=lambda t: t['name'])

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

    if rejected:
        report += "## ❌ 검증 실패 도구\n\n"
        for tool in sorted(rejected, key=lambda t: t['name']):
            report += f"### {tool['name']}\n"
            report += f"- **사유**: {tool.get('notes', '검증 실패')}\n"
            report += f"- **공식 사이트**: {tool.get('official_site', 'N/A')}\n\n"

    return report


def main():
    args = parse_args()
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
    parsed_tools = {}
    api_response_received = False
    rejected_candidates = []

    if args.offline:
        print("🛑 오프라인 모드: OpenRouter API 호출을 건너뜁니다.")
    else:
        try:
            ai_response = call_openrouter_api(full_prompt)
            print("✅ AI 응답 수신 완료")
            # API 응답 내용을 디버깅용으로 로그 파일에 저장한다.
            debug_log = ROOT_DIR / "logs" / "openrouter_response.jsonl"
            debug_log.parent.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            with debug_log.open("a", encoding="utf-8") as fp:
                fp.write(f"[{timestamp}]\n{ai_response}\n")

            parsed_tools = parse_ai_response(ai_response)
            if parsed_tools:
                print(f"🧠 AI 응답에서 {len(parsed_tools)}개 도구 파싱")
            else:
                print("⚠️ AI 응답에서 파싱된 도구가 없습니다.")

            api_response_received = True
        except ValueError as exc:
            print(f"⚠️ {exc}")
            print("⚙️ API 호출 없이 기존 캐시 기반으로 보고서를 생성합니다.")
        except RequestException as exc:
            print(f"❌ OpenRouter API 호출 실패: {exc}")
            print("⚙️ API 없이 캐시 데이터로 보고서를 생성합니다.")
        except Exception as exc:
            print(f"❌ 예기치 않은 오류 발생: {exc}")
            raise

    seed_tools = load_seed_tools()
    results: Dict[str, Any] = {}

    def _merge_source(
        source: Dict[str, Any],
        label: str,
        *,
        allow_client_errors: bool,
        status_override: str | None = None,
        note_prefix: str | None = None,
    ) -> None:
        for tool_name, raw in source.items():
            if (
                label == "캐시"
                and str(raw.get("status", "")).lower() == "rejected"
                and str(raw.get("notes", "")).startswith("AI 제안")
            ):
                continue

            candidate = dict(raw)
            if status_override == "rejected":
                candidate["status"] = "rejected"
                candidate["is_standalone"] = False

            is_valid, normalized, issues = verifier.verify_tool_entry(
                tool_name,
                candidate,
                allow_client_errors=allow_client_errors,
            )
            if not is_valid:
                print(f"⚠️ {label} '{tool_name}' 검증 실패: {'; '.join(issues)}")
                if label == "AI 응답":
                    rejected_candidates.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "source": label,
                            "name": tool_name,
                            "issues": issues,
                            "payload": candidate,
                        }
                    )
                continue

            if status_override:
                normalized["status"] = status_override
                if status_override != "verified":
                    normalized["is_standalone"] = False
                if note_prefix:
                    note_existing = normalized.get("notes", "")
                    normalized["notes"] = f"{note_prefix} {note_existing}".strip()

            if label == "AI 응답" and normalized["status"] == "rejected":
                rejected_candidates.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "source": label,
                        "name": tool_name,
                        "issues": issues or ["AI 응답 거부"],
                        "payload": normalized,
                    }
                )
                existing_entry = results.get(tool_name)
                if existing_entry and existing_entry.get("status") == "verified":
                    continue

            results[tool_name] = normalized

    if seed_tools:
        _merge_source(seed_tools, "시드", allow_client_errors=True)

    if cache:
        _merge_source(cache, "캐시", allow_client_errors=True)

    if parsed_tools:
        _merge_source(
            parsed_tools,
            "AI 응답",
            allow_client_errors=False,
            status_override="rejected",
            note_prefix="AI 제안: 추가 검증 필요",
        )

    if rejected_candidates and not args.no_rejected_log:
        REJECTED_LOG_FILE.parent.mkdir(exist_ok=True)
        with REJECTED_LOG_FILE.open("a", encoding="utf-8") as fp:
            for entry in rejected_candidates:
                fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"🗒️ 거부 후보 {len(rejected_candidates)}건을 {REJECTED_LOG_FILE}에 기록했습니다.")
    elif rejected_candidates:
        print(f"🗒️ 거부 후보 {len(rejected_candidates)}건을 기록하지 않고 건너뜁니다 (--no-rejected-log).")

    # 5. 보고서 생성
    report = generate_report(results)
    report_file = ROOT_DIR / "docs" / "REPORT.md"
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📄 보고서 생성: {report_file}")

    # 6. 캐시 저장
    save_cache(results)
    print("💾 캐시 저장 완료")

    if api_response_received:
        print("\n✅ 조사 완료!")
    else:
        print("\n✅ 조사 완료 (API 응답 없이 캐시 기반)")


if __name__ == "__main__":
    main()
