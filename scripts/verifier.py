"""베리파이어 모듈 - AI 클라이언트 검증 로직 스텁."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

DATA_DIR = Path(__file__).parent.parent / "data"


def verify_tool_entry(tool_data: Dict[str, Any]) -> bool:
    """간단한 검증 스텁: 필수 필드 존재 여부 확인."""
    required_keys = {"status", "type", "installation", "platforms", "is_standalone"}
    if not required_keys.issubset(tool_data):
        return False
    if tool_data["status"] not in {"verified", "rejected"}:
        return False
    return True


def load_verified_cache() -> Dict[str, Any]:
    """검증된 도구 캐시 로드."""
    cache_file = DATA_DIR / "verified-tools.yaml"
    if not cache_file.exists():
        return {}
    # YAML 파싱은 추후 구현; 현재는 JSON 유사 구조 가정
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
