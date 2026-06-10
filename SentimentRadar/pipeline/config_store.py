"""管线配置存取：radar_config 键值表 + 默认值合并。"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from sqlalchemy import text

from SentimentRadar.db import get_engine

DEFAULTS: Dict[str, Any] = {
    "enabled": False,
    "run_times": ["16:35"],
    "llm_model": "gpt-5.4-mini",
    "tushare_token": "",
}

_CONFIG_KEY = "pipeline"


def get_config() -> Dict[str, Any]:
    config = deepcopy(DEFAULTS)
    with get_engine().begin() as conn:
        row = conn.execute(
            text("SELECT value FROM radar_config WHERE key = :key"), {"key": _CONFIG_KEY}
        ).fetchone()
    if row and isinstance(row.value, dict):
        config.update(row.value)
    return config


def update_config(partial: Dict[str, Any]) -> Dict[str, Any]:
    """合并写入配置，仅接受 DEFAULTS 中存在的键。"""
    config = get_config()
    for key, value in partial.items():
        if key in DEFAULTS:
            config[key] = value
    with get_engine().begin() as conn:
        conn.execute(
            text(
                "INSERT INTO radar_config (key, value, updated_at) "
                "VALUES (:key, CAST(:value AS JSONB), NOW()) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()"
            ),
            {"key": _CONFIG_KEY, "value": json.dumps(config, ensure_ascii=False)},
        )
    return config
