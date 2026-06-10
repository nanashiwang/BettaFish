"""管线 LLM 客户端：OpenAI 协议中转，JSON 输出带解析重试。"""

from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger
from openai import OpenAI

from config import settings


class LLMError(Exception):
    pass


def _client() -> OpenAI:
    api_key = settings.OPENAI_API_KEY
    base_url = settings.OPENAI_BASE_URL
    if not api_key:
        raise LLMError("未配置 OPENAI_API_KEY，无法调用 LLM")
    return OpenAI(api_key=api_key, base_url=base_url)


def _extract_json(content: str) -> Any:
    """容忍代码块包裹与前后杂文的 JSON 提取。"""
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start > 0:
        text = text[start:]
    return json.loads(text)


def invoke_json(system: str, user: str, model: str, max_tokens: int = 4000) -> Any:
    """调用 LLM 并解析 JSON 输出；解析失败自动重试一次，再失败抛 LLMError。"""
    client = _client()
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            return _extract_json(content)
        except Exception as exc:
            last_error = exc
            logger.warning(f"LLM 调用/解析失败（第 {attempt + 1} 次）: {exc}")
    raise LLMError(f"LLM 调用失败: {last_error}")
