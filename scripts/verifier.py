"""AI 클라이언트 메타데이터 검증 및 정규화 모듈."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import requests

VALID_TYPES = {"cli", "desktop", "hybrid"}
VALID_STATUSES = {"verified", "rejected"}
ALLOWED_INSTALL_METHODS = {"pip", "npm", "brew", "direct", "git"}
REQUEST_TIMEOUT = 5
USER_AGENT = "ai-client-registry-bot/1.0"


def _ensure_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def _normalize_platforms(platforms: Any) -> List[str]:
    if isinstance(platforms, list):
        return [str(p).strip() for p in platforms if str(p).strip()]
    if isinstance(platforms, str):
        return [p.strip() for p in platforms.split(",") if p.strip()]
    return []


def _looks_like_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _check_url(url: str, allow_client_errors: bool = False) -> Tuple[bool, str | None]:
    if not url:
        return False, "URL이 비어 있습니다"
    if not _looks_like_url(url):
        return False, "URL 형식이 올바르지 않습니다"

    try:
        response = requests.head(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        status = response.status_code
        if status >= 500 or (status >= 400 and not allow_client_errors):
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            )
            status = response.status_code
        if status >= 500:
            return False, f"HTTP {status} 응답"
        if status >= 400 and not allow_client_errors:
            return False, f"HTTP {status} 응답"
    except requests.RequestException as exc:  # pragma: no cover - 네트워크 의존
        return False, str(exc)
    return True, None


def verify_tool_entry(
    name: str,
    tool_data: Dict[str, Any],
    *,
    allow_client_errors: bool = False,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """도구 정보를 검증하고 정규화한다."""

    issues: List[str] = []
    normalized: Dict[str, Any] = {"name": name}

    status = str(tool_data.get("status", "")).strip().lower()
    if status not in VALID_STATUSES:
        issues.append("status 값이 올바르지 않습니다")
    normalized["status"] = status or "unknown"

    tool_type = str(tool_data.get("type", "")).strip().lower()
    if tool_type not in VALID_TYPES:
        issues.append("type 값이 올바르지 않습니다")
    normalized["type"] = tool_type or "unknown"

    official_site = str(tool_data.get("official_site", "")).strip()
    if official_site:
        ok, error = _check_url(official_site, allow_client_errors=allow_client_errors)
        if not ok:
            issues.append(f"공식 사이트 확인 실패: {error}")
    else:
        issues.append("공식 사이트가 없습니다")
    normalized["official_site"] = official_site

    github = tool_data.get("github")
    if github:
        github = str(github).strip()
        ok, error = _check_url(github, allow_client_errors=True)
        if not ok:
            issues.append(f"GitHub URL 확인 실패: {error}")
    normalized["github"] = github or None

    installation = tool_data.get("installation", {}) or {}
    install_method = str(installation.get("method", "")).strip().lower()
    install_command = str(installation.get("command", "")).strip()
    if not install_method or not install_command:
        issues.append("설치 정보가 불완전합니다")
    elif install_method not in ALLOWED_INSTALL_METHODS:
        issues.append(f"설치 method '{install_method}'는 허용되지 않습니다")
    if install_command and install_command.split()[0] in {"sudo", "rm", "curl"}:
        issues.append("설치 명령어에 위험한 명령이 포함되어 있습니다")
    normalized["installation"] = {
        "method": install_method or "",
        "command": install_command,
    }

    platforms = _normalize_platforms(tool_data.get("platforms", []))
    platforms_lower = {p.lower() for p in platforms}
    if "macos" not in platforms_lower:
        issues.append("macOS 지원 정보가 없습니다")
    normalized["platforms"] = platforms

    is_standalone = _ensure_bool(tool_data.get("is_standalone"))
    normalized["is_standalone"] = is_standalone

    verified_date = str(tool_data.get("verified_date", "")).strip() or datetime_today()
    normalized["verified_date"] = verified_date

    notes = str(tool_data.get("notes", "")).strip()
    if len(notes) > 200:
        notes = notes[:197] + "..."
    normalized["notes"] = notes

    if status == "verified" and not is_standalone:
        issues.append("verified 상태지만 is_standalone 값이 False 입니다")
    if status == "rejected" and is_standalone:
        issues.append("rejected 상태지만 is_standalone 값이 True 입니다")

    return len(issues) == 0, normalized, issues


def datetime_today() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d")
