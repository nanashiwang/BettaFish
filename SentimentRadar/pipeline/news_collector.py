"""热榜采集：newsnow 聚合 API，13 个平台，财经源加权。"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any, Dict, List

import httpx
from loguru import logger
from sqlalchemy import text

from SentimentRadar.db import get_engine

BASE_URL = "https://newsnow.busiyi.world"

# source_id -> (中文名, 热度权重)：财经源权重更高
SOURCES: Dict[str, tuple] = {
    "cls-hot": ("财联社", 2.0),
    "wallstreetcn": ("华尔街见闻", 2.0),
    "xueqiu": ("雪球热榜", 2.0),
    "weibo": ("微博热搜", 1.0),
    "zhihu": ("知乎热榜", 1.0),
    "toutiao": ("今日头条", 1.0),
    "douyin": ("抖音热榜", 0.8),
    "bilibili-hot-search": ("B站热搜", 0.8),
    "thepaper": ("澎湃新闻", 1.2),
    "tieba": ("百度贴吧", 0.8),
    "coolapk": ("酷安热榜", 0.5),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


async def _fetch_source(client: httpx.AsyncClient, source: str) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/api/s?id={source}&latest"
    source_name, _ = SOURCES[source]
    try:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        items = response.json().get("items", [])
    except Exception as exc:
        logger.warning(f"热榜源 {source_name}({source}) 采集失败: {exc}")
        return []
    news = []
    for rank, item in enumerate(items, start=1):
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        news.append({
            "source": source,
            "source_name": source_name,
            "title": title[:500],
            "url": str(item.get("url") or item.get("mobileUrl") or ""),
            "rank": rank,
        })
    return news


async def _collect_all() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        results = await asyncio.gather(*(_fetch_source(client, s) for s in SOURCES))
    return [item for sublist in results for item in sublist]


def collect_news(crawl_date: date) -> List[Dict[str, Any]]:
    """采集全部热榜并落库，返回当日全部新闻（含此前批次已入库的）。"""
    news = asyncio.run(_collect_all())
    if news:
        with get_engine().begin() as conn:
            for item in news:
                conn.execute(
                    text(
                        "INSERT INTO radar_news (source, source_name, title, url, rank, crawl_date) "
                        "VALUES (:source, :source_name, :title, :url, :rank, :crawl_date) "
                        "ON CONFLICT (source, title, crawl_date) DO UPDATE SET rank = EXCLUDED.rank"
                    ),
                    {**item, "crawl_date": crawl_date},
                )
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, source, source_name, title, url, rank FROM radar_news "
                "WHERE crawl_date = :d ORDER BY source, rank"
            ),
            {"d": crawl_date},
        ).fetchall()
    return [dict(row._mapping) for row in rows]


def source_weight(source: str) -> float:
    return SOURCES.get(source, ("", 1.0))[1]
