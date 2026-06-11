"""话题提取与板块映射：LLM 聚合热榜为财经话题，并从真实板块清单中约束选择。"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List

from sqlalchemy import text

from SentimentRadar.db import get_engine
from SentimentRadar.pipeline.llm import invoke_json

_TOPIC_SYSTEM = (
    "你是 A 股舆情分析师。根据今日各平台热榜标题，聚合出与 A 股市场相关的热点话题。"
    "只输出 JSON，不要任何解释。"
)

_TOPIC_USER_TEMPLATE = """以下是今日各平台热榜（格式：编号|平台|标题）：

{news_text}

任务：聚合出 5-10 个与 A 股投资相关的热点话题（产业、政策、公司、宏观事件等）。
要求：
- 话题名简洁（4-12 字），能对应到股市板块或产业方向
- 每个话题给出 2-5 个关键词、关联的新闻编号列表
- 纯娱乐/体育/社会新闻除非有明确产业影响，否则不要纳入
- 如果话题不足 5 个，给出实际数量即可

输出 JSON 格式：
{{"topics": [{{"name": "话题名", "keywords": ["关键词"], "news_indexes": [1, 2]}}]}}"""

_BOARD_SYSTEM = (
    "你是 A 股板块映射助手。把话题映射到给定的板块清单中，只能从清单中选择，"
    "禁止编造清单外的板块名。只输出 JSON。"
)

_BOARD_USER_TEMPLATE = """话题列表：
{topics_text}

可选板块清单（只能从中选择）：
概念板块：{concept_names}
行业板块：{industry_names}

任务：为每个话题选出最相关的 1-2 个板块（优先概念板块，找不到合适概念时用行业板块）；
确实没有相关板块的话题输出空数组。

输出 JSON 格式：
{{"mapping": [{{"topic": "话题名", "boards": ["板块名"]}}]}}"""


def extract_topics(news: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """LLM 聚合热榜为财经话题，返回 [{name, keywords, news_indexes}]。"""
    lines = [f"{i + 1}|{item['source_name']}|{item['title']}" for i, item in enumerate(news)]
    result = invoke_json(
        _TOPIC_SYSTEM,
        _TOPIC_USER_TEMPLATE.format(news_text="\n".join(lines)),
        model=model,
        max_tokens=2000,
    )
    topics = []
    for topic in result.get("topics", []):
        name = str(topic.get("name") or "").strip()
        indexes = [i for i in topic.get("news_indexes", []) if isinstance(i, int) and 1 <= i <= len(news)]
        if not name or not indexes:
            continue
        topics.append({
            "name": name[:100],
            "keywords": [str(k)[:50] for k in topic.get("keywords", [])][:5],
            "news_indexes": indexes,
        })
    return topics


def map_boards(
    topics: List[Dict[str, Any]], boards: List[Dict[str, Any]], model: str
) -> List[Dict[str, Any]]:
    """把话题映射到真实板块清单（约束选择），返回的每个话题附 boards 字段。"""
    by_name: Dict[str, Dict[str, Any]] = {b["name"]: b for b in boards}
    concept_names = "、".join(b["name"] for b in boards if b["type"] == "concept")
    industry_names = "、".join(b["name"] for b in boards if b["type"] == "industry")
    topics_text = "\n".join(
        f"- {t['name']}（关键词：{'、'.join(t['keywords'])}）" for t in topics
    )
    result = invoke_json(
        _BOARD_SYSTEM,
        _BOARD_USER_TEMPLATE.format(
            topics_text=topics_text,
            concept_names=concept_names,
            industry_names=industry_names,
        ),
        model=model,
        max_tokens=1500,
    )
    mapping = {
        str(item.get("topic") or ""): [
            by_name[name] for name in item.get("boards", []) if name in by_name
        ]
        for item in result.get("mapping", [])
    }
    for topic in topics:
        topic["boards"] = mapping.get(topic["name"], [])[:2]
    return topics


def save_topics(trade_date: date, topics: List[Dict[str, Any]]) -> None:
    with get_engine().begin() as conn:
        for topic in topics:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_topics (trade_date, name, keywords, news_refs, heat_score, heat_z, price_z, boards)
                    VALUES (:trade_date, :name, CAST(:keywords AS JSONB), CAST(:news_refs AS JSONB),
                            :heat_score, :heat_z, :price_z, CAST(:boards AS JSONB))
                    ON CONFLICT (trade_date, name) DO UPDATE SET
                        keywords = EXCLUDED.keywords,
                        news_refs = EXCLUDED.news_refs,
                        heat_score = EXCLUDED.heat_score,
                        heat_z = EXCLUDED.heat_z,
                        price_z = EXCLUDED.price_z,
                        boards = EXCLUDED.boards
                    """
                ),
                {
                    "trade_date": trade_date,
                    "name": topic["name"],
                    "keywords": json.dumps(topic["keywords"], ensure_ascii=False),
                    "news_refs": json.dumps(topic["news_indexes"]),
                    "heat_score": topic.get("heat_score", 0.0),
                    "heat_z": topic.get("heat_z"),
                    "price_z": topic.get("price_z"),
                    "boards": json.dumps(topic.get("boards", []), ensure_ascii=False),
                },
            )
