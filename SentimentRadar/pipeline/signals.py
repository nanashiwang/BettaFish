"""背离信号计算：话题热度 z 分 × 板块价格 z 分 → 四象限场景分类（纯计算，不调 LLM）。"""

from __future__ import annotations

import json
import statistics
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from SentimentRadar.db import get_engine
from SentimentRadar.pipeline.news_collector import source_weight

# 场景常量（与前端展示文案一致）
SCENARIO_NEWS_FIRST = "先闻后动"
SCENARIO_RESONANCE = "同步共振"
SCENARIO_MOVE_FIRST = "先动后闻"


def compute_heat(topics: List[Dict[str, Any]], news: List[Dict[str, Any]], trade_date: date) -> None:
    """计算话题热度分与 heat_z（历史不足时退化为当日相对 z 分）。"""
    for topic in topics:
        score = 0.0
        for index in topic["news_indexes"]:
            item = news[index - 1]
            rank_weight = max(0.1, 1.0 - (item["rank"] - 1) / 50.0)
            score += source_weight(item["source"]) * rank_weight
        topic["heat_score"] = round(score, 3)

    # 基线：最近 14 天全部话题的热度分布（样本足够时）
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT heat_score FROM radar_topics "
                "WHERE trade_date >= :start AND trade_date < :today"
            ),
            {"start": trade_date - timedelta(days=14), "today": trade_date},
        ).fetchall()
    baseline = [row.heat_score for row in rows]
    if len(baseline) < 10:
        baseline = [topic["heat_score"] for topic in topics]

    mean = statistics.mean(baseline) if baseline else 0.0
    std = statistics.pstdev(baseline) if len(baseline) > 1 else 0.0
    for topic in topics:
        topic["heat_z"] = round((topic["heat_score"] - mean) / std, 3) if std > 0 else 0.0


def compute_price_metrics(history: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    """从板块日线计算近 3 日涨幅的 z 分与量比；数据不足返回 None。"""
    closes = [row["close"] for row in history if row.get("close")]
    volumes = [row["volume"] for row in history if row.get("volume")]
    if len(closes) < 15:
        return None

    def window_return(end_index: int) -> float:
        return (closes[end_index] / closes[end_index - 3] - 1.0) * 100.0

    current = window_return(len(closes) - 1)
    # 基线：过去最多 60 个交易日的滚动 3 日涨幅
    samples = [window_return(i) for i in range(3, len(closes) - 1)][-60:]
    mean = statistics.mean(samples)
    std = statistics.pstdev(samples)
    price_z = (current - mean) / std if std > 0 else 0.0

    volume_ratio = 0.0
    if len(volumes) >= 6 and statistics.mean(volumes[-6:-1]) > 0:
        volume_ratio = volumes[-1] / statistics.mean(volumes[-6:-1])

    return {
        "return_3d": round(current, 2),
        "price_z": round(price_z, 3),
        "volume_ratio": round(volume_ratio, 2),
    }


def classify(heat_z: float, price_z: float) -> Optional[str]:
    """四象限场景分类；无明显信号返回 None。"""
    if heat_z >= 0.8 and price_z <= 0.5:
        return SCENARIO_NEWS_FIRST
    if heat_z >= 0.8 and price_z > 0.5:
        return SCENARIO_RESONANCE
    if heat_z < 0.5 and price_z >= 1.2:
        return SCENARIO_MOVE_FIRST
    return None


def strength_label(heat_z: float, price_z: float) -> str:
    magnitude = max(abs(heat_z), abs(price_z))
    if magnitude >= 2.0:
        return "高"
    if magnitude >= 1.2:
        return "中-高"
    return "中"


def build_signals(topics: List[Dict[str, Any]], quotes_by_board: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """组合话题热度与板块价格指标，产出排序后的信号列表；同时把 price_z 回写到话题（供散点图）。"""
    signals = []
    for topic in topics:
        boards = topic.get("boards") or []
        if not boards:
            continue
        # 多板块时取价格最弱的（更贴近"未启动"判断）
        metrics_list = []
        for board in boards:
            metrics = compute_price_metrics(quotes_by_board.get(board["code"], []))
            if metrics:
                metrics_list.append((board, metrics))
        if not metrics_list:
            continue
        board, metrics = min(metrics_list, key=lambda pair: pair[1]["price_z"])
        topic["price_z"] = metrics["price_z"]
        scenario = classify(topic["heat_z"], metrics["price_z"])
        if not scenario:
            continue
        # 排序分：先闻后动优先级最高（产品核心场景），其次按信号强度
        priority = {SCENARIO_NEWS_FIRST: 2.0, SCENARIO_RESONANCE: 1.0, SCENARIO_MOVE_FIRST: 1.5}[scenario]
        signals.append({
            "topic": topic,
            "board": board,
            "all_boards": boards,
            "metrics": metrics,
            "scenario": scenario,
            "strength": strength_label(topic["heat_z"], metrics["price_z"]),
            "sort_score": priority * (abs(topic["heat_z"]) + abs(metrics["price_z"])),
        })
    signals.sort(key=lambda item: item["sort_score"], reverse=True)
    return signals


def save_board_quotes(board: Dict[str, Any], history: List[Dict[str, Any]]) -> None:
    """缓存板块日线（用于回填收益与减少重复拉取）。"""
    with get_engine().begin() as conn:
        for row in history:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_board_quotes (board_code, board_name, board_type, trade_date, close, pct_chg, volume)
                    VALUES (:code, :name, :type, TO_DATE(:trade_date, 'YYYYMMDD'), :close, :pct_chg, :volume)
                    ON CONFLICT (board_code, trade_date) DO UPDATE SET
                        close = EXCLUDED.close, pct_chg = EXCLUDED.pct_chg, volume = EXCLUDED.volume
                    """
                ),
                {
                    "code": board["code"],
                    "name": board["name"],
                    "type": board["type"],
                    **row,
                },
            )


def backfill_returns(today: date) -> int:
    """回填历史预判的 1/3/5 日板块收益（以信号板块第一个为准），返回更新行数。"""
    updated = 0
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, trade_date, boards FROM radar_predictions "
                "WHERE trade_date < :today AND (return_1d IS NULL OR return_3d IS NULL OR return_5d IS NULL)"
            ),
            {"today": today},
        ).fetchall()
        for row in rows:
            boards = row.boards if isinstance(row.boards, list) else json.loads(row.boards or "[]")
            if not boards:
                continue
            code = boards[0].get("code")
            quotes = conn.execute(
                text(
                    "SELECT trade_date, close FROM radar_board_quotes "
                    "WHERE board_code = :code AND trade_date >= :d ORDER BY trade_date"
                ),
                {"code": code, "d": row.trade_date},
            ).fetchall()
            if len(quotes) < 2 or not quotes[0].close:
                continue
            base = quotes[0].close
            values = {}
            for field, offset in (("return_1d", 1), ("return_3d", 3), ("return_5d", 5)):
                if len(quotes) > offset and quotes[offset].close:
                    values[field] = round((quotes[offset].close / base - 1.0) * 100.0, 2)
            if values:
                sets = ", ".join(f"{k} = :{k}" for k in values)
                conn.execute(
                    text(f"UPDATE radar_predictions SET {sets} WHERE id = :id"),
                    {**values, "id": row.id},
                )
                updated += 1
    return updated
