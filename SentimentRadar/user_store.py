"""雷达注册用户的 PostgreSQL 持久化存储。

依赖 docker-compose 中的 bettafish-db 服务；连接串通过 RADAR_DB_URL 环境变量配置，
默认指向宿主机映射端口（本地开发），容器内由 compose 注入指向 db 服务。
数据库不可用时由调用方（platform_service）降级为内存存储。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DB_URL = "postgresql+psycopg://bettafish:bettafish@127.0.0.1:5444/bettafish"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS radar_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'subscriber',
    role_label VARCHAR(32) NOT NULL DEFAULT '订阅用户',
    plan_id VARCHAR(32) NOT NULL DEFAULT 'free',
    risk_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    risk_version VARCHAR(32) NOT NULL DEFAULT '',
    subscription JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
)
"""

_engine: Optional[Engine] = None
_available: Optional[bool] = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = os.getenv("RADAR_DB_URL", DEFAULT_DB_URL)
        _engine = create_engine(url, future=True, pool_pre_ping=True)
    return _engine


def available() -> bool:
    """惰性探测数据库可用性，进程内只探测一次。"""
    global _available
    if _available is None:
        try:
            with _get_engine().begin() as conn:
                conn.execute(text(_SCHEMA))
            _available = True
            logger.info("雷达用户库已连接（radar_users 表就绪）")
        except Exception as exc:
            _available = False
            logger.warning(f"雷达用户库不可用，注册用户将使用内存存储: {exc}")
    return _available


def _row_to_user(row: Any) -> Dict[str, Any]:
    """数据库行转为前端使用的 user dict（不含密码哈希）。"""
    last_login = row.last_login_at or row.created_at
    return {
        "id": f"u_{row.id}",
        "name": row.name,
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
    with _get_engine().begin() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM radar_users")).scalar_one()


def get_user(email: str) -> Optional[Dict[str, Any]]:
    """返回 {user, password_hash, subscription}，不存在返回 None。"""
    with _get_engine().begin() as conn:
        row = conn.execute(
            text("SELECT * FROM radar_users WHERE email = :email"),
            {"email": email},
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
    password_hash: str,
    name: str,
    role: str,
    role_label: str,
    risk_confirmed: bool,
    risk_version: str,
    subscription: Dict[str, Any],
) -> Dict[str, Any]:
    with _get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO radar_users
                    (email, password_hash, name, role, role_label, plan_id,
                     risk_confirmed, risk_version, subscription, last_login_at)
                VALUES
                    (:email, :password_hash, :name, :role, :role_label, :plan_id,
                     :risk_confirmed, :risk_version, CAST(:subscription AS JSONB), NOW())
                RETURNING *
                """
            ),
            {
                "email": email,
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
    with _get_engine().begin() as conn:
        conn.execute(
            text(
                "UPDATE radar_users SET last_login_at = NOW(), risk_confirmed = :confirmed "
                "WHERE email = :email"
            ),
            {"email": email, "confirmed": risk_confirmed},
        )


def update_subscription(email: str, subscription: Dict[str, Any]) -> bool:
    """更新注册用户的订阅信息；账号未注册返回 False。"""
    with _get_engine().begin() as conn:
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
