import json
from typing import Any


def parse_json_object(content: str, source: str = "模型") -> dict[str, Any]:
    """Parse one JSON object, tolerating a fenced response but no extra prose."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"{source}返回了空内容。")

    text = content.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{source}返回的内容不是合法JSON：第{exc.lineno}行第{exc.colno}列。"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(f"{source}必须返回JSON对象。")
    return result


def require_fields(data: dict[str, Any], fields: tuple[str, ...], source: str) -> dict[str, Any]:
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"{source}缺少必要字段：{', '.join(missing)}")
    return data
