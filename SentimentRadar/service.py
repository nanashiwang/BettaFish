"""极简预判版舆情雷达数据服务。

「今日预判」读取管线产出的真实数据（radar_predictions 等表）；
「我的关注 / 设置」仍为原型 Mock，待个人关注体系建设后替换。
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from SentimentRadar import db

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
        "my_related": {"summary": "暂无数据", "highlight": message, "items": []},
        "top_risk": {"title": "暂无风险信号", "level": "-", "scope": "-", "reason": message},
        "evidence_overview": [],
    }


def _latest_trade_date(conn) -> Optional[Any]:
    return conn.execute(text("SELECT MAX(trade_date) FROM radar_predictions")).scalar_one()


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


# ====================== 以下为原型 Mock（我的关注 / 设置） ======================

SETTINGS = {
    "focus_targets": {
        "stocks": ["寒武纪", "中科曙光", "宁德时代"],
        "themes": ["AI 算力", "半导体", "固态电池"],
        "sectors": ["计算机设备", "电子", "新能源"],
    },
    "push_templates": [
        {"id": "morning", "name": "早间 3 条", "enabled": True, "time": "08:30"},
        {"id": "noon", "name": "午间变化", "enabled": True, "time": "11:45"},
        {"id": "close", "name": "收盘复盘", "enabled": True, "time": "15:30"},
        {"id": "risk", "name": "高风险即时提醒", "enabled": True, "time": "实时"},
    ],
    "risk_preferences": ["消息兑现风险", "过热风险", "来源不明", "负面扩散"],
    "channels": ["站内信", "邮件", "企业微信"],
}


def get_my_focus() -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "disclaimer": DISCLAIMER,
        "hits": [
            {
                "name": "寒武纪",
                "type": "股票",
                "match": "AI 算力主线",
                "scenario": "同步共振",
                "risk": "讨论过热",
                "next": "观察公告或订单证据补充",
            },
            {
                "name": "半导体",
                "type": "板块",
                "match": "景气周期延续",
                "scenario": "先闻后动",
                "risk": "业绩分化",
                "next": "观察产业数据与头部公司披露",
            },
            {
                "name": "固态电池",
                "type": "主题",
                "match": "午后讨论升温",
                "scenario": "闻而不动",
                "risk": "市场反馈有限",
                "next": "观察是否扩散到板块联动",
            },
        ],
        "settings": deepcopy(SETTINGS),
    }


def get_settings() -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "settings": deepcopy(SETTINGS),
    }


def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 原型阶段仅回显前端提交内容，不写入磁盘，避免误改用户配置。
    merged = deepcopy(SETTINGS)
    if isinstance(payload, dict):
        for key in ("focus_targets", "push_templates", "risk_preferences", "channels"):
            if key in payload:
                merged[key] = payload[key]
    return {
        "success": True,
        "message": "设置已保存（原型内存态）",
        "updated_at": _timestamp(),
        "settings": merged,
    }
