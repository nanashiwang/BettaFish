"""雷达在线购买订单存储。"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from SentimentRadar.db import available, get_engine

ORDERS: Dict[str, Dict[str, Any]] = {}


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _row_to_order(row: Any) -> Dict[str, Any]:
    paid_at = row.paid_at.strftime("%Y-%m-%d %H:%M:%S") if row.paid_at else ""
    created_at = row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else ""
    return {
        "id": row.id,
        "out_trade_no": row.out_trade_no,
        "user_email": row.user_email,
        "user_name": row.user_name,
        "plan_id": row.plan_id,
        "plan_name": row.plan_name,
        "period": row.period,
        "amount": _to_float(row.amount),
        "subject": row.subject,
        "pay_type": row.pay_type,
        "status": row.status,
        "provider": row.provider,
        "provider_trade_no": row.provider_trade_no,
        "raw_notify": row.raw_notify or {},
        "created_at": created_at,
        "paid_at": paid_at,
    }


def create_order(order: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(order)
    data.setdefault("status", "pending")
    data.setdefault("provider", "epay")
    data.setdefault("provider_trade_no", "")
    data.setdefault("raw_notify", {})
    data.setdefault("created_at", _timestamp())
    data.setdefault("paid_at", "")

    if available():
        with get_engine().begin() as conn:
            row = conn.execute(
                text(
                    """
                    INSERT INTO radar_orders
                        (out_trade_no, user_email, user_name, plan_id, plan_name, period,
                         amount, subject, pay_type, status, provider, provider_trade_no, raw_notify)
                    VALUES
                        (:out_trade_no, :user_email, :user_name, :plan_id, :plan_name, :period,
                         :amount, :subject, :pay_type, :status, :provider, :provider_trade_no,
                         CAST(:raw_notify AS JSONB))
                    RETURNING *
                    """
                ),
                {
                    **data,
                    "raw_notify": json.dumps(data.get("raw_notify") or {}, ensure_ascii=False),
                },
            ).fetchone()
        return _row_to_order(row)

    ORDERS[data["out_trade_no"]] = data
    return deepcopy(data)


def get_order(out_trade_no: str) -> Optional[Dict[str, Any]]:
    trade_no = str(out_trade_no or "").strip()
    if not trade_no:
        return None
    if available():
        with get_engine().begin() as conn:
            row = conn.execute(
                text("SELECT * FROM radar_orders WHERE out_trade_no = :out_trade_no"),
                {"out_trade_no": trade_no},
            ).fetchone()
        return _row_to_order(row) if row else None
    order = ORDERS.get(trade_no)
    return deepcopy(order) if order else None


def mark_order_paid(out_trade_no: str, provider_trade_no: str, raw_notify: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    trade_no = str(out_trade_no or "").strip()
    if available():
        with get_engine().begin() as conn:
            row = conn.execute(
                text(
                    """
                    UPDATE radar_orders
                    SET status = 'paid', provider_trade_no = :provider_trade_no,
                        raw_notify = CAST(:raw_notify AS JSONB), paid_at = COALESCE(paid_at, NOW())
                    WHERE out_trade_no = :out_trade_no
                    RETURNING *
                    """
                ),
                {
                    "out_trade_no": trade_no,
                    "provider_trade_no": provider_trade_no,
                    "raw_notify": json.dumps(raw_notify, ensure_ascii=False),
                },
            ).fetchone()
        return _row_to_order(row) if row else None

    order = ORDERS.get(trade_no)
    if not order:
        return None
    order["status"] = "paid"
    order["provider_trade_no"] = provider_trade_no
    order["raw_notify"] = deepcopy(raw_notify)
    order["paid_at"] = order.get("paid_at") or _timestamp()
    return deepcopy(order)


def list_orders_for_user(email: str) -> List[Dict[str, Any]]:
    user_email = str(email or "").strip().lower()
    if not user_email:
        return []
    if available():
        with get_engine().begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT * FROM radar_orders
                    WHERE user_email = :email
                    ORDER BY created_at DESC
                    LIMIT 50
                    """
                ),
                {"email": user_email},
            ).fetchall()
        return [_row_to_order(row) for row in rows]
    return [deepcopy(order) for order in ORDERS.values() if order.get("user_email") == user_email]
