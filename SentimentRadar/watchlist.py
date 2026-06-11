"""用户关注列表（股票/主题/板块）的持久化管理。"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from SentimentRadar.db import get_engine

VALID_TYPES = {"stock", "theme", "sector"}

TYPE_LABELS = {"stock": "股票", "theme": "主题", "sector": "板块"}


def list_items(user_email: str) -> List[Dict[str, Any]]:
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, item_type, name FROM radar_watchlist "
                "WHERE user_email = :email ORDER BY item_type, id"
            ),
            {"email": user_email.lower()},
        ).fetchall()
    return [{"id": row.id, "type": row.item_type, "name": row.name} for row in rows]


def add_item(user_email: str, item_type: str, name: str) -> Dict[str, Any]:
    name = str(name or "").strip()
    if item_type not in VALID_TYPES:
        return {"success": False, "message": "无效的关注类型"}
    if not 1 <= len(name) <= 30:
        return {"success": False, "message": "名称需为 1-30 个字符"}
    with get_engine().begin() as conn:
        existing = conn.execute(
            text(
                "SELECT id FROM radar_watchlist "
                "WHERE user_email = :email AND item_type = :type AND name = :name"
            ),
            {"email": user_email.lower(), "type": item_type, "name": name},
        ).fetchone()
        if existing:
            return {"success": False, "message": "已在关注列表中"}
        count = conn.execute(
            text("SELECT COUNT(*) FROM radar_watchlist WHERE user_email = :email"),
            {"email": user_email.lower()},
        ).scalar_one()
        if count >= 100:
            return {"success": False, "message": "关注数量已达上限（100）"}
        conn.execute(
            text(
                "INSERT INTO radar_watchlist (user_email, item_type, name) "
                "VALUES (:email, :type, :name)"
            ),
            {"email": user_email.lower(), "type": item_type, "name": name},
        )
    return {"success": True, "message": "已添加关注", "items": list_items(user_email)}


def remove_item(user_email: str, item_id: int) -> Dict[str, Any]:
    with get_engine().begin() as conn:
        result = conn.execute(
            text("DELETE FROM radar_watchlist WHERE id = :id AND user_email = :email"),
            {"id": item_id, "email": user_email.lower()},
        )
    if result.rowcount == 0:
        return {"success": False, "message": "关注项不存在"}
    return {"success": True, "message": "已取消关注", "items": list_items(user_email)}
