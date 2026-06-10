"""雷达注册用户的 PostgreSQL 持久化存储。

连接与建表统一由 SentimentRadar.db 管理；数据库不可用时由调用方
（platform_service）降级为内存存储。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import text

from SentimentRadar.db import available, get_engine

__all__ = ["available", "count_users", "get_user", "create_user", "touch_login", "update_subscription"]


def _row_to_user(row: Any) -> Dict[str, Any]:
    """数据库行转为前端使用的 user dict（不含密码哈希）。"""
    last_login = row.last_login_at or row.created_at
    return {
        "id": f"u_{row.id}",
        "name": row.name,
        "username": row.username,
        "email": row.email,
        "phone": "",
        "role": row.role,
        "role_label": row.role_label,
        "plan_id": row.plan_id,
        "risk_confirmed": row.risk_confirmed,
        "risk_version": row.risk_version,
        "last_login_at": last_login.strftime("%Y-%m-%d %H:%M:%S"),
    }


def count_users() -> int:
    with get_engine().begin() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM radar_users")).scalar_one()


def get_user(account: str) -> Optional[Dict[str, Any]]:
    """按邮箱或用户名（均大小写不敏感）查找，返回 {user, password_hash, subscription}，不存在返回 None。"""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                "SELECT * FROM radar_users "
                "WHERE email = :account OR (username <> '' AND LOWER(username) = :account)"
            ),
            {"account": account.strip().lower()},
        ).fetchone()
    if not row:
        return None
    return {
        "user": _row_to_user(row),
        "password_hash": row.password_hash,
        "subscription": row.subscription,
    }


def create_user(
    email: str,
    username: str,
    password_hash: str,
    name: str,
    role: str,
    role_label: str,
    risk_confirmed: bool,
    risk_version: str,
    subscription: Dict[str, Any],
) -> Dict[str, Any]:
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO radar_users
                    (email, username, password_hash, name, role, role_label, plan_id,
                     risk_confirmed, risk_version, subscription, last_login_at)
                VALUES
                    (:email, :username, :password_hash, :name, :role, :role_label, :plan_id,
                     :risk_confirmed, :risk_version, CAST(:subscription AS JSONB), NOW())
                RETURNING *
                """
            ),
            {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "name": name,
                "role": role,
                "role_label": role_label,
                "plan_id": subscription.get("plan_id", "free"),
                "risk_confirmed": risk_confirmed,
                "risk_version": risk_version,
                "subscription": json.dumps(subscription, ensure_ascii=False),
            },
        ).fetchone()
    return _row_to_user(row)


def touch_login(email: str, risk_confirmed: bool) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            text(
                "UPDATE radar_users SET last_login_at = NOW(), risk_confirmed = :confirmed "
                "WHERE email = :email"
            ),
            {"email": email, "confirmed": risk_confirmed},
        )


def update_subscription(email: str, subscription: Dict[str, Any]) -> bool:
    """更新注册用户的订阅信息；账号未注册返回 False。"""
    with get_engine().begin() as conn:
        result = conn.execute(
            text(
                "UPDATE radar_users SET subscription = CAST(:subscription AS JSONB), plan_id = :plan_id "
                "WHERE email = :email"
            ),
            {
                "email": email,
                "plan_id": subscription.get("plan_id", "free"),
                "subscription": json.dumps(subscription, ensure_ascii=False),
            },
        )
    return result.rowcount > 0
