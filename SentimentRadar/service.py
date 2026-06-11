"""极简预判版舆情雷达数据服务。

「今日预判」读取管线产出的真实数据（radar_predictions 等表）；
「我的关注 / 设置」仍为原型 Mock，待个人关注体系建设后替换。
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from SentimentRadar import db, watchlist
from SentimentRadar.pipeline.signals import classify

DISCLAIMER = "仅供舆情观察 · 不构成投资建议"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _empty_briefing(message: str) -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "product": "A 股舆情雷达",
        "version": "信号版",
        "disclaimer": DISCLAIMER,
        "headline": message,
        "cards": [],
        "signals_scatter": [],
        "my_related": {"summary": "暂无数据", "highlight": message, "items": []},
        "top_risk": {"title": "暂无风险信号", "level": "-", "scope": "-", "reason": message},
        "evidence_overview": [],
    }


def _latest_trade_date(conn) -> Optional[Any]:
    return conn.execute(text("SELECT MAX(trade_date) FROM radar_predictions")).scalar_one()


def _board_trend(board_code: Optional[str], days: int = 30) -> List[float]:
    """板块近 N 个交易日收盘价（迷你走势图用）。"""
    if not board_code:
        return []
    with db.get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT close FROM radar_board_quotes WHERE board_code = :code "
                "ORDER BY trade_date DESC LIMIT :days"
            ),
            {"code": board_code, "days": days},
        ).fetchall()
    return [row.close for row in reversed(rows) if row.close is not None]


def get_today_briefing() -> Dict[str, Any]:
    """返回最近一个有预判数据的交易日的完整简报。"""
    if not db.available():
        return _empty_briefing("数据服务暂不可用")
    with db.get_engine().begin() as conn:
        trade_date = _latest_trade_date(conn)
        if not trade_date:
            return _empty_briefing("暂无预判数据：管线尚未运行，管理员可在后台「平台设置」中立即运行")
        rows = conn.execute(
            text("SELECT * FROM radar_predictions WHERE trade_date = :d ORDER BY rank"),
            {"d": trade_date},
        ).fetchall()
        topic_count = conn.execute(
            text("SELECT COUNT(*) FROM radar_topics WHERE trade_date = :d"), {"d": trade_date}
        ).scalar_one()
        news_overview = conn.execute(
            text(
                "SELECT source_name, COUNT(*) AS cnt FROM radar_news "
                "WHERE crawl_date = :d GROUP BY source_name ORDER BY cnt DESC LIMIT 5"
            ),
            {"d": trade_date},
        ).fetchall()
        updated_at = conn.execute(
            text("SELECT MAX(created_at) FROM radar_predictions WHERE trade_date = :d"),
            {"d": trade_date},
        ).scalar_one()
        # 象限散点：当日全部已计算价格指标的话题
        scatter_rows = conn.execute(
            text(
                "SELECT name, heat_z, price_z FROM radar_topics "
                "WHERE trade_date = :d AND price_z IS NOT NULL AND heat_z IS NOT NULL"
            ),
            {"d": trade_date},
        ).fetchall()

    cards: List[Dict[str, Any]] = []
    board_names: List[str] = []
    for row in rows:
        tags = row.tags if isinstance(row.tags, list) else []
        boards = row.boards if isinstance(row.boards, list) else []
        board_names.extend(b.get("name", "") for b in boards)
        cards.append({
            "id": row.card_id,
            "rank": row.rank,
            "title": row.title,
            "scenario": row.scenario,
            "strength": row.strength,
            "judgement": row.judgement,
            "reason": row.reason,
            "risk": row.risk,
            "next": row.next_watch,
            "evidence": row.evidence_summary,
            "tags": tags,
            "heat_z": row.heat_z,
            "price_z": row.price_z,
            "board_name": boards[0].get("name") if boards else "",
            "board_trend": _board_trend(boards[0].get("code")) if boards else [],
        })

    headline = rows[0].headline if rows else ""
    # 重点风险：优先「先动后闻」场景，否则取首卡风险
    risk_row = next((r for r in rows if r.scenario == "先动后闻"), rows[0] if rows else None)
    top_risk = {
        "title": f"今日重点风险：{risk_row.title}" if risk_row else "暂无风险信号",
        "level": risk_row.strength if risk_row else "-",
        "scope": "、".join(filter(None, board_names)) or "-",
        "reason": risk_row.risk if risk_row else "-",
    }

    return {
        "success": True,
        "updated_at": (updated_at or datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
        "product": "A 股舆情雷达",
        "version": "信号版",
        "disclaimer": DISCLAIMER,
        "headline": headline or f"{trade_date} 共识别 {len(cards)} 条舆情-价格信号",
        "cards": cards,
        "signals_scatter": [
            {
                "name": row.name,
                "heat_z": row.heat_z,
                "price_z": row.price_z,
                "scenario": classify(row.heat_z, row.price_z),
            }
            for row in scatter_rows
        ],
        "my_related": {
            "summary": f"今日识别话题 {topic_count} 个 / 信号 {len(cards)} 条",
            "highlight": headline,
            "items": [
                {"label": "候选话题", "value": f"{topic_count} 个"},
                {"label": "背离信号", "value": f"{len(cards)} 条"},
                {"label": "覆盖板块", "value": "、".join(filter(None, board_names))[:40] or "-"},
            ],
        },
        "top_risk": top_risk,
        "evidence_overview": [
            {"name": row.source_name, "count": row.cnt} for row in news_overview
        ],
    }


def get_prediction_detail(card_id: str) -> Dict[str, Any]:
    """返回单条预判的证据链解析（来自管线落库的 detail JSONB）。"""
    if not db.available():
        return {"success": False, "message": "数据服务暂不可用"}
    with db.get_engine().begin() as conn:
        row = conn.execute(
            text("SELECT * FROM radar_predictions WHERE card_id = :card_id"),
            {"card_id": card_id},
        ).fetchone()
    if not row:
        return {"success": False, "message": "未找到对应预判解析"}
    detail = row.detail if isinstance(row.detail, dict) else {}
    return {
        "success": True,
        "id": card_id,
        "updated_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "disclaimer": DISCLAIMER,
        "detail": {
            "title": row.title,
            "scenario": row.scenario,
            "summary": detail.get("summary", row.judgement),
            "why": detail.get("why", []),
            "timeline": detail.get("timeline", []),
            "evidence_chain": detail.get("evidence_chain", []),
            "risk_boundary": detail.get("risk_boundary", []),
            "next_watch": detail.get("next_watch", []),
        },
    }


def get_history(limit: int = 200) -> Dict[str, Any]:
    """历史预判（含回填收益）与胜率统计。"""
    if not db.available():
        return {"success": True, "stats": {}, "days": []}
    with db.get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT * FROM radar_predictions ORDER BY trade_date DESC, rank LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()

    days: Dict[str, List[Dict[str, Any]]] = {}
    evaluated: List[Any] = []
    by_scenario: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        date_key = row.trade_date.isoformat()
        days.setdefault(date_key, []).append({
            "id": row.card_id,
            "title": row.title,
            "scenario": row.scenario,
            "strength": row.strength,
            "judgement": row.judgement,
            "boards": row.boards if isinstance(row.boards, list) else [],
            "heat_z": row.heat_z,
            "price_z": row.price_z,
            "return_1d": row.return_1d,
            "return_3d": row.return_3d,
            "return_5d": row.return_5d,
        })
        bucket = by_scenario.setdefault(row.scenario, {"count": 0, "evaluated": 0, "wins": 0})
        bucket["count"] += 1
        if row.return_3d is not None:
            evaluated.append(row.return_3d)
            bucket["evaluated"] += 1
            if row.return_3d > 0:
                bucket["wins"] += 1

    for bucket in by_scenario.values():
        bucket["win_rate"] = (
            round(bucket["wins"] / bucket["evaluated"] * 100, 1) if bucket["evaluated"] else None
        )

    stats = {
        "total": len(rows),
        "evaluated": len(evaluated),
        "win_rate_3d": round(len([r for r in evaluated if r > 0]) / len(evaluated) * 100, 1)
        if evaluated
        else None,
        "avg_return_3d": round(sum(evaluated) / len(evaluated), 2) if evaluated else None,
        "by_scenario": by_scenario,
    }
    return {
        "success": True,
        "disclaimer": DISCLAIMER,
        "stats": stats,
        "days": [{"date": key, "cards": value} for key, value in days.items()],
    }


# ====================== 我的关注（真实关注表） ======================

PUSH_TEMPLATES_PREVIEW = [
    {"id": "morning", "name": "早间信号推送", "enabled": False, "time": "即将上线"},
    {"id": "risk", "name": "高风险即时提醒", "enabled": False, "time": "即将上线"},
]


def _match_watchlist(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """关注项与最近交易日话题/预判做包含匹配，返回命中列表。"""
    if not items:
        return []
    with db.get_engine().begin() as conn:
        trade_date = conn.execute(text("SELECT MAX(trade_date) FROM radar_topics")).scalar_one()
        if not trade_date:
            return []
        topics = conn.execute(
            text("SELECT name, keywords, boards, heat_z FROM radar_topics WHERE trade_date = :d"),
            {"d": trade_date},
        ).fetchall()
        predictions = conn.execute(
            text("SELECT card_id, title, scenario, risk, next_watch, tags FROM radar_predictions WHERE trade_date = :d"),
            {"d": trade_date},
        ).fetchall()

    hits = []
    for item in items:
        for topic in topics:
            keywords = topic.keywords if isinstance(topic.keywords, list) else []
            boards = topic.boards if isinstance(topic.boards, list) else []
            haystack = [topic.name, *keywords, *(b.get("name", "") for b in boards)]
            if not any(item["name"] in h or h in item["name"] for h in haystack if h):
                continue
            # 找到对应的预判卡（标题/标签包含话题名）
            prediction = next(
                (
                    p
                    for p in predictions
                    if topic.name in p.title
                    or any(topic.name in str(t) for t in (p.tags if isinstance(p.tags, list) else []))
                ),
                None,
            )
            hits.append({
                "name": item["name"],
                "type": watchlist.TYPE_LABELS.get(item["type"], item["type"]),
                "match": topic.name,
                "scenario": prediction.scenario if prediction else "观察中",
                "risk": prediction.risk if prediction else f"热度 z 分 {topic.heat_z}，暂未形成显著信号",
                "next": prediction.next_watch if prediction else "继续跟踪舆情与板块联动",
                "card_id": prediction.card_id if prediction else None,
            })
            break
    return hits


def get_my_focus(user_email: str) -> Dict[str, Any]:
    if not db.available():
        return {"success": True, "updated_at": _timestamp(), "disclaimer": DISCLAIMER, "hits": [], "watchlist": []}
    items = watchlist.list_items(user_email)
    return {
        "success": True,
        "updated_at": _timestamp(),
        "disclaimer": DISCLAIMER,
        "hits": _match_watchlist(items),
        "watchlist": items,
    }


def get_settings(user_email: str) -> Dict[str, Any]:
    items = watchlist.list_items(user_email) if db.available() else []
    return {
        "success": True,
        "updated_at": _timestamp(),
        "settings": {
            "watchlist": items,
            "push_templates": deepcopy(PUSH_TEMPLATES_PREVIEW),
        },
    }
