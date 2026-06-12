"""A 股舆情雷达平台能力 Mock 服务。

该模块提供登录、订阅、账户和管理后台的可运行 API 数据结构。
当前为原型内存态，后续可以替换为数据库、支付和真实权限系统。
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger
from werkzeug.security import check_password_hash, generate_password_hash

from SentimentRadar import email_service, order_store, payment_service, user_store


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _date_after(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


CURRENT_USER = {
    "id": "u_10001",
    "name": "王先生",
    "email": "user@example.com",
    "phone": "138****2688",
    "role": "subscriber",
    "role_label": "订阅用户",
    "plan_id": "standard",
    "risk_confirmed": True,
    "risk_version": "v2026.06",
    "last_login_at": _timestamp(),
}


# 数据库不可用时的内存降级存储：键为小写邮箱，密码哈希与用户资料分开存放。
REGISTERED_USERS: Dict[str, Dict[str, Any]] = {}

# 演示管理员白名单：仅这些账号经原型任意登录可获得管理员身份。
DEMO_ADMIN_ACCOUNTS = {"ops@radar.cn"}


FREE_SUBSCRIPTION = {
    "plan_id": "free",
    "plan_name": "免费版",
    "status": "active",
    "renewal": False,
    "started_at": "",
    "expires_at": "-",
}


PLANS = [
    {
        "id": "free",
        "name": "免费版",
        "price_month": 0,
        "price_year": 0,
        "audience": "轻度用户",
        "status": "上架中",
        "summary": "适合只想快速了解今日主线的用户。",
        "features": ["今日一句话", "1 条摘要预览", "5 个关注对象", "不含完整证据链"],
        "limits": {
            "today_predictions": 1,
            "evidence_depth": "摘要",
            "watchlist_limit": 5,
            "push_templates": ["站内摘要"],
            "history_days": 0,
            "ai_quota": 10,
        },
    },
    {
        "id": "standard",
        "name": "标准版",
        "price_month": 29,
        "price_year": 299,
        "audience": "普通投资者",
        "status": "上架中",
        "recommended": True,
        "summary": "每天看完 3 条重点，适合多数普通用户。",
        "features": ["今日 3 条完整卡片", "标准证据链", "20 个关注对象", "早间 / 收盘推送"],
        "limits": {
            "today_predictions": 3,
            "evidence_depth": "标准",
            "watchlist_limit": 20,
            "push_templates": ["早间 3 条", "收盘复盘"],
            "history_days": 7,
            "ai_quota": 100,
        },
    },
    {
        "id": "pro",
        "name": "专业版",
        "price_month": 69,
        "price_year": 699,
        "audience": "深度用户",
        "status": "上架中",
        "summary": "适合需要关注多个主题和高风险提醒的用户。",
        "features": ["完整证据链", "100 个关注对象", "高风险即时提醒", "90 天历史回看"],
        "limits": {
            "today_predictions": 3,
            "evidence_depth": "完整",
            "watchlist_limit": 100,
            "push_templates": ["早间 3 条", "午间变化", "收盘复盘", "高风险即时提醒"],
            "history_days": 90,
            "ai_quota": 500,
        },
    },
    {
        "id": "creator",
        "name": "创作者版",
        "price_month": 199,
        "price_year": 1999,
        "audience": "财经内容用户",
        "status": "上架中",
        "summary": "适合财经内容选题和素材整理。",
        "features": ["主题摘要与素材导出", "批量关注池", "更高 AI 解析额度", "内容素材导出"],
        "limits": {
            "today_predictions": 3,
            "evidence_depth": "完整 + 导出",
            "watchlist_limit": 300,
            "push_templates": ["早间 3 条", "午间变化", "收盘复盘", "高风险即时提醒"],
            "history_days": 180,
            "ai_quota": 2000,
        },
    },
]


SUBSCRIPTION = {
    "plan_id": "standard",
    "plan_name": "标准版",
    "status": "active",
    "renewal": False,
    "started_at": datetime.now().strftime("%Y-%m-%d"),
    "expires_at": _date_after(30),
}


USAGE = {
    "today_predictions": {"label": "今日 3 条查看", "used": 3, "limit": 3},
    "watchlist": {"label": "关注对象", "used": 14, "limit": 20},
    "ai_analysis": {"label": "AI 解析额度", "used": 38, "limit": 100},
    "push": {"label": "推送额度", "used": 6, "limit": 30},
}


BILLS = [
    {"id": "BF20260608001", "plan": "标准版月付", "amount": 29, "status": "已支付", "paid_at": "2026-06-08"},
    {"id": "BF20260508007", "plan": "标准版月付", "amount": 29, "status": "已支付", "paid_at": "2026-05-08"},
    {"id": "BF20260408003", "plan": "标准版月付", "amount": 29, "status": "已完成", "paid_at": "2026-04-08"},
]


RISK_CONFIRMATIONS = [
    {"version": "v2026.06", "confirmed_at": _timestamp(), "ip": "127.0.0.1", "status": "已确认"},
    {"version": "v2026.05", "confirmed_at": "2026-05-08 09:31:12", "ip": "183.***.***.12", "status": "已确认"},
]


ADMIN_USERS = [
    {
        "id": "u_10001",
        "name": "王先生",
        "username": "wang",
        "email": "wang@example.com",
        "registration_source": "密码注册",
        "register_ip": "111.198.71.33",
        "phone": "138****2688",
        "role": "订阅用户",
        "plan": "标准版",
        "expires_at": _date_after(30),
        "used_balance": "$0.00",
        "group": "default",
        "usage": "3条 / 14关注",
        "status": "已启用",
        "last_active": "2 分钟前",
        "note": "用户多次查看 AI 算力主题证据链，未出现异常调用。",
    },
    {
        "id": "u_10002",
        "name": "内容号 A",
        "username": "creator_a",
        "email": "creator@radar.cn",
        "registration_source": "密码注册",
        "register_ip": "117.186.43.154",
        "phone": "139****1024",
        "role": "创作者",
        "plan": "创作者版",
        "expires_at": _date_after(180),
        "used_balance": "$41.31",
        "group": "default",
        "usage": "3条 / 186关注",
        "status": "已启用",
        "last_active": "18 分钟前",
        "note": "素材导出频率较高，成本仍在套餐范围内。",
    },
    {
        "id": "u_10003",
        "name": "李女士",
        "username": "li",
        "email": "li@example.com",
        "registration_source": "密码注册",
        "register_ip": "222.20.193.43",
        "phone": "138****9120",
        "role": "免费用户",
        "plan": "无套餐",
        "expires_at": "-",
        "used_balance": "$2.08",
        "group": "default",
        "usage": "1条 / 5关注",
        "status": "已启用",
        "last_active": "1 小时前",
        "note": "多次点击订阅页，适合运营触达。",
    },
    {
        "id": "u_10004",
        "name": "测试账号",
        "username": "test",
        "email": "test@example.com",
        "registration_source": "管理员创建",
        "register_ip": "23.151.104.146",
        "phone": "137****0001",
        "role": "订阅用户",
        "plan": "专业版",
        "expires_at": _date_after(16),
        "used_balance": "$0.34",
        "group": "default",
        "usage": "3条 / 82关注",
        "status": "已禁用",
        "last_active": "昨天",
        "note": "测试用账号，禁止真实推送。",
    },
    {
        "id": "u_10005",
        "name": "运营账号",
        "username": "ops",
        "email": "ops@radar.cn",
        "registration_source": "管理员创建",
        "register_ip": "36.112.18.139",
        "phone": "136****7788",
        "role": "管理员",
        "plan": "内部",
        "expires_at": "-",
        "used_balance": "$0.00",
        "group": "internal",
        "usage": "不限",
        "status": "已启用",
        "last_active": "刚刚",
        "note": "后台运营账号。",
    },
]


ADMIN_SETTINGS = {
    "today_rules": {
        "topic_heat_weight": 62,
        "heat_growth_weight": 58,
        "user_relevance_weight": 64,
        "risk_penalty_enabled": True,
    },
    "scenario_windows": {
        "news_before_move": "新闻领先异动 0-2 小时",
        "move_before_news": "异动领先新闻 0-6 小时",
        "sync_resonance": "新闻 / 舆情 / 行情 30 分钟内",
        "move_without_news": "12 小时等待补证",
    },
    "risk_rules": {
        "cash_out": True,
        "overheat": True,
        "unknown_source": True,
        "regulatory": True,
    },
    "compliance": {
        "forbidden_words": ["买入", "卖出", "追涨", "杀跌", "仓位", "目标价", "收益保证"],
        "disclaimer": "仅供舆情观察，不构成投资建议。",
    },
    "push": {
        "morning": {"enabled": True, "time": "08:45"},
        "noon": {"enabled": True, "time": "12:15"},
        "close": {"enabled": True, "time": "15:30"},
    },
    "model": {
        "primary_model": "gpt-4.1 / deepseek-chat",
        "daily_cost_limit": 8000,
        "timeout_seconds": 60,
    },
}


def get_current_user() -> Dict[str, Any]:
    return {
        "success": True,
        "user": deepcopy(CURRENT_USER),
        "subscription": deepcopy(SUBSCRIPTION),
        "updated_at": _timestamp(),
    }


def _new_free_subscription() -> Dict[str, Any]:
    subscription = deepcopy(FREE_SUBSCRIPTION)
    subscription["started_at"] = datetime.now().strftime("%Y-%m-%d")
    return subscription


def _auth_success(user: Dict[str, Any], subscription: Dict[str, Any], message: str) -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "token": "mock-radar-session-token",
        "user": user,
        "subscription": subscription,
    }


def register(payload: Dict[str, Any]) -> Dict[str, Any]:
    """注册：优先写入 PostgreSQL（radar_users 表），数据库不可用时降级为内存存储。"""
    email = str(payload.get("email") or "").strip().lower()
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    if "@" not in email:
        return {"success": False, "message": "请输入有效邮箱"}
    if not 2 <= len(username) <= 20:
        return {"success": False, "message": "用户名需为 2-20 个字符"}
    if "@" in username:
        return {"success": False, "message": "用户名不能包含 @ 符号"}
    if len(password) < 6:
        return {"success": False, "message": "密码至少 6 位"}
    if email == CURRENT_USER["email"]:
        return {"success": False, "message": "该邮箱已注册，请直接登录"}

    risk_confirmed = bool(payload.get("risk_confirmed", True))
    subscription = _new_free_subscription()

    if user_store.available():
        if user_store.get_user(email):
            return {"success": False, "message": "该邮箱已注册，请直接登录"}
        if user_store.get_user(username):
            return {"success": False, "message": "该用户名已被占用"}
        # 首个注册用户自动成为超级管理员，便于自部署后接管后台。
        is_first = user_store.count_users() == 0
        user = user_store.create_user(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            name=username,
            role="super_admin" if is_first else "subscriber",
            role_label="超级管理员" if is_first else "订阅用户",
            risk_confirmed=risk_confirmed,
            risk_version="v2026.06",
            subscription=subscription,
        )
        return _auth_success(user, subscription, "注册成功")

    # ---- 内存降级 ----
    if email in REGISTERED_USERS:
        return {"success": False, "message": "该邮箱已注册，请直接登录"}
    if any(
        item["user"].get("username", "").lower() == username.lower()
        for item in REGISTERED_USERS.values()
    ):
        return {"success": False, "message": "该用户名已被占用"}
    user = deepcopy(CURRENT_USER)
    user.update({
        "id": f"u_{10100 + len(REGISTERED_USERS)}",
        "name": username,
        "username": username,
        "email": email,
        "phone": "",
        "plan_id": "free",
        "risk_confirmed": risk_confirmed,
        "risk_version": "v2026.06",
        "last_login_at": _timestamp(),
    })
    if not REGISTERED_USERS:
        user["role"] = "super_admin"
        user["role_label"] = "超级管理员"
    REGISTERED_USERS[email] = {
        "user": user,
        "password_hash": generate_password_hash(password),
        "subscription": subscription,
    }
    return _auth_success(deepcopy(user), deepcopy(subscription), "注册成功（内存模式，重启后失效）")


def login(payload: Dict[str, Any]) -> Dict[str, Any]:
    account = payload.get("account") or payload.get("email") or CURRENT_USER["email"]
    confirmed = bool(payload.get("risk_confirmed", True))
    account_text = str(account).strip().lower()
    password = str(payload.get("password") or payload.get("code") or "")

    # 已注册账号（邮箱或用户名）：校验密码哈希；未注册账号走下方原型任意登录（保留演示账号行为）。
    if user_store.available():
        stored = user_store.get_user(account_text)
        if stored:
            if not check_password_hash(stored["password_hash"], password):
                return {"success": False, "message": "账号或密码错误"}
            user_store.touch_login(stored["user"]["email"], confirmed)
            user = stored["user"]
            user["risk_confirmed"] = confirmed
            user["last_login_at"] = _timestamp()
            return _auth_success(user, stored["subscription"] or _new_free_subscription(), "登录成功")
    else:
        registered = REGISTERED_USERS.get(account_text) or next(
            (
                item
                for item in REGISTERED_USERS.values()
                if item["user"].get("username", "").lower() == account_text
            ),
            None,
        )
        if registered:
            if not check_password_hash(registered["password_hash"], password):
                return {"success": False, "message": "账号或密码错误"}
            registered["user"]["risk_confirmed"] = confirmed
            registered["user"]["last_login_at"] = _timestamp()
            return _auth_success(
                deepcopy(registered["user"]),
                deepcopy(registered["subscription"]),
                "登录成功（内存模式）",
            )

    user = deepcopy(CURRENT_USER)
    user["email"] = account if "@" in str(account) else CURRENT_USER["email"]
    user["phone"] = account if "@" not in str(account) else CURRENT_USER["phone"]
    user["risk_confirmed"] = confirmed
    user["last_login_at"] = _timestamp()
    subscription = deepcopy(SUBSCRIPTION)

    # 演示管理员仅限白名单账号，避免任意含 admin 字样的账号被提权。
    if account_text in DEMO_ADMIN_ACCOUNTS:
        user["role"] = "admin"
        user["role_label"] = "管理员"
        user["plan_id"] = "internal"
        subscription.update({
            "plan_id": "internal",
            "plan_name": "内部账号",
            "status": "active",
            "expires_at": "-",
        })

    return {
        "success": True,
        "message": "登录成功（原型模式）",
        "token": "mock-radar-session-token",
        "user": user,
        "subscription": subscription,
    }


def confirm_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    version = payload.get("version") or "v2026.06"
    record = {
        "version": version,
        "confirmed_at": _timestamp(),
        "ip": "127.0.0.1",
        "status": "已确认",
    }
    RISK_CONFIRMATIONS.insert(0, record)
    return {"success": True, "message": "风险声明已确认", "record": record}


def _plan_by_id(plan_id: str) -> Dict[str, Any]:
    return next((item for item in PLANS if item["id"] == plan_id), PLANS[1])


def _period_from_payload(payload: Dict[str, Any]) -> str:
    return "year" if payload.get("period") == "year" else "month"


def _period_label(period: str) -> str:
    return "年付" if period == "year" else "月付"


def _plan_amount(plan: Dict[str, Any], period: str) -> Decimal:
    price_key = "price_year" if period == "year" else "price_month"
    return Decimal(str(plan.get(price_key) or 0)).quantize(Decimal("0.01"))


def _subscription_for_plan(plan: Dict[str, Any], period: str, paid_at: str = "") -> Dict[str, Any]:
    days = 365 if period == "year" else 30
    try:
        started = datetime.strptime(paid_at[:10], "%Y-%m-%d") if paid_at else datetime.now()
    except ValueError:
        started = datetime.now()
    return {
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "status": "active",
        "renewal": False,
        "started_at": started.strftime("%Y-%m-%d"),
        "expires_at": (started + timedelta(days=days)).strftime("%Y-%m-%d"),
    }


def _activate_subscription(account: Optional[str], subscription: Dict[str, Any]) -> Dict[str, Any]:
    account_text = str(account or "").strip().lower()
    if account_text:
        if user_store.available():
            user_store.update_subscription(account_text, subscription)
            return subscription
        if account_text in REGISTERED_USERS:
            REGISTERED_USERS[account_text]["subscription"] = deepcopy(subscription)
            REGISTERED_USERS[account_text]["user"]["plan_id"] = subscription.get("plan_id", "free")
            return subscription

    SUBSCRIPTION.update(subscription)
    return deepcopy(SUBSCRIPTION)


def get_plans(current_plan_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "success": True,
        "plans": deepcopy(PLANS),
        "current_plan_id": current_plan_id or SUBSCRIPTION["plan_id"],
        "disclaimer": "订阅只增加舆情摘要、证据链深度、关注数量和推送能力，不构成投资建议。",
    }


def subscribe(payload: Dict[str, Any], account: Optional[str] = None) -> Dict[str, Any]:
    plan_id = payload.get("plan_id", "standard")
    plan = _plan_by_id(plan_id)
    period = _period_from_payload(payload)
    subscription = _subscription_for_plan(plan, period)
    message = f"已切换为 {plan['name']}（原型模式，未发起真实支付）"
    activated = _activate_subscription(account, subscription)
    return {"success": True, "message": message, "subscription": deepcopy(activated)}


def create_payment(payload: Dict[str, Any], account: Optional[str], user: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    """创建在线支付订单；未启用 epay 时保留原型直开通。"""
    plan = _plan_by_id(str(payload.get("plan_id") or "standard"))
    period = _period_from_payload(payload)
    amount = _plan_amount(plan, period)
    account_text = str(account or "").strip().lower()

    if amount <= 0 or not payment_service.epay_enabled():
        return subscribe({"plan_id": plan["id"], "period": period}, account_text)
    if not payment_service.epay_configured():
        return {"success": False, "message": "请先在后台完整配置易支付参数"}
    if not account_text or "@" not in account_text:
        return {"success": False, "message": "当前账号缺少有效邮箱，无法创建订单"}

    from config import reload_settings

    settings = reload_settings()
    out_trade_no = f"BF{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}"
    subject = f"{settings.EPAY_NAME_PREFIX} {plan['name']} {_period_label(period)}"
    order = order_store.create_order({
        "out_trade_no": out_trade_no,
        "user_email": account_text,
        "user_name": user.get("name") or user.get("username") or account_text,
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "period": period,
        "amount": float(amount),
        "subject": subject,
        "pay_type": payload.get("pay_type") or settings.EPAY_TYPE or "alipay",
    })
    payment_url = payment_service.create_epay_url(order, base_url)
    return {
        "success": True,
        "message": "订单已创建，请跳转支付",
        "payment_required": True,
        "payment_url": payment_url,
        "order": order,
    }


def _activate_paid_order(order: Dict[str, Any]) -> Dict[str, Any]:
    plan = _plan_by_id(order.get("plan_id", "standard"))
    subscription = _subscription_for_plan(plan, order.get("period", "month"), order.get("paid_at", ""))
    return _activate_subscription(order.get("user_email"), subscription)


def handle_payment_notify(params: Dict[str, Any]) -> Dict[str, Any]:
    if not payment_service.verify_epay_notify(params):
        return {"success": False, "message": "易支付签名验证失败"}

    trade_status = str(params.get("trade_status") or "").strip()
    if trade_status and trade_status not in {"TRADE_SUCCESS", "TRADE_FINISHED"}:
        return {"success": False, "message": f"支付状态未完成：{trade_status}"}

    out_trade_no = str(params.get("out_trade_no") or "").strip()
    order = order_store.get_order(out_trade_no)
    if not order:
        return {"success": False, "message": "订单不存在"}

    was_paid = order.get("status") == "paid"
    if not was_paid:
        order = order_store.mark_order_paid(
            out_trade_no,
            str(params.get("trade_no") or params.get("api_trade_no") or ""),
            dict(params),
        ) or order
    subscription = _activate_paid_order(order)

    try:
        from config import reload_settings

        settings = reload_settings()
        if settings.SMTP_ENABLED and not was_paid:
            email_service.send_email(
                to_email=order["user_email"],
                subject="BettaFish 舆情雷达订阅已开通",
                text=f"您的 {order['plan_name']} {_period_label(order.get('period', 'month'))} 已支付成功，到期日 {subscription['expires_at']}。",
            )
    except Exception as exc:  # 邮件失败不影响支付入账
        logger.warning(f"支付成功邮件发送失败: {exc}")

    return {"success": True, "message": "支付已确认", "order": order, "subscription": subscription}


def get_subscription(subscription: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    current = deepcopy(subscription or SUBSCRIPTION)
    return {
        "success": True,
        "subscription": current,
        "plan": deepcopy(_plan_by_id(current.get("plan_id", "standard"))),
    }


def get_usage() -> Dict[str, Any]:
    return {"success": True, "usage": deepcopy(USAGE), "updated_at": _timestamp()}


def _order_to_bill(order: Dict[str, Any]) -> Dict[str, Any]:
    status_map = {"paid": "已支付", "pending": "待支付", "closed": "已关闭"}
    paid_at = order.get("paid_at") or order.get("created_at") or ""
    return {
        "id": order.get("out_trade_no", ""),
        "plan": f"{order.get('plan_name', '')}{_period_label(order.get('period', 'month'))}",
        "amount": order.get("amount", 0),
        "status": status_map.get(order.get("status", ""), order.get("status", "")),
        "paid_at": paid_at[:10],
    }


def get_bills(account: Optional[str] = None) -> Dict[str, Any]:
    order_bills = [_order_to_bill(order) for order in order_store.list_orders_for_user(account or "")]
    return {"success": True, "bills": order_bills + deepcopy(BILLS)}


def get_account(user: Optional[Dict[str, Any]] = None, subscription: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    current_user = deepcopy(user or CURRENT_USER)
    current_subscription = deepcopy(subscription or SUBSCRIPTION)
    bills = get_bills(current_user.get("email", "")).get("bills", [])
    return {
        "success": True,
        "user": current_user,
        "subscription": current_subscription,
        "usage": deepcopy(USAGE),
        "bills": bills,
        "risk_confirmations": deepcopy(RISK_CONFIRMATIONS),
    }


def get_admin_overview() -> Dict[str, Any]:
    return {
        "success": True,
        "updated_at": _timestamp(),
        "stats": [
            {"label": "今日活跃用户", "value": "12,846", "trend": "较昨日 +8.6%", "tone": "blue"},
            {"label": "订阅收入", "value": "¥86,420", "trend": "续费率 72%", "tone": "ok"},
            {"label": "AI 成本", "value": "¥4,318", "trend": "成本占比 5.0%", "tone": "warn"},
            {"label": "高风险输出", "value": "42", "trend": "待复核 6 条", "tone": "danger"},
        ],
        "trend": [
            {"day": "周一", "active": 42},
            {"day": "周二", "active": 54},
            {"day": "周三", "active": 49},
            {"day": "周四", "active": 66},
            {"day": "周五", "active": 76},
            {"day": "周六", "active": 58},
            {"day": "今日", "active": 72},
        ],
        "data_sources": [
            {"name": "新闻", "status": "正常", "note": "延迟 2 分钟"},
            {"name": "公告", "status": "正常", "note": "交易所同步"},
            {"name": "股吧 / 论坛", "status": "注意", "note": "部分限流"},
            {"name": "行情", "status": "正常", "note": "15 秒延迟"},
            {"name": "视频评论", "status": "排队", "note": "队列积压"},
        ],
    }


def list_admin_users() -> Dict[str, Any]:
    return {"success": True, "users": deepcopy(ADMIN_USERS), "total": len(ADMIN_USERS)}


def get_admin_user(user_id: str) -> Dict[str, Any]:
    user = next((item for item in ADMIN_USERS if item["id"] == user_id), None)
    if not user:
        return {"success": False, "message": "用户不存在"}
    return {
        "success": True,
        "user": deepcopy(user),
        "subscription": deepcopy(SUBSCRIPTION),
        "usage": deepcopy(USAGE),
        "risk_confirmations": deepcopy(RISK_CONFIRMATIONS[:2]),
        "push_logs": [
            {"template": "早间 3 条", "status": "已送达", "sent_at": "08:45"},
            {"template": "收盘复盘", "status": "等待中", "sent_at": "15:30"},
        ],
    }


def update_admin_user(user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    for user in ADMIN_USERS:
        if user["id"] == user_id:
            for key in ("status", "plan", "note", "role", "group"):
                if key in payload:
                    user[key] = payload[key]
            return {"success": True, "message": "用户已更新（原型内存态）", "user": deepcopy(user)}
    return {"success": False, "message": "用户不存在"}


def get_admin_plans() -> Dict[str, Any]:
    return {"success": True, "plans": deepcopy(PLANS)}


def update_admin_plan(plan_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    for plan in PLANS:
        if plan["id"] == plan_id:
            for key in ("name", "price_month", "price_year", "status", "summary", "limits"):
                if key in payload:
                    plan[key] = payload[key]
            return {"success": True, "message": "套餐已保存（原型内存态）", "plan": deepcopy(plan)}
    return {"success": False, "message": "套餐不存在"}


def get_admin_settings() -> Dict[str, Any]:
    return {"success": True, "settings": deepcopy(ADMIN_SETTINGS)}


def update_admin_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in payload.items():
        if key in ADMIN_SETTINGS and isinstance(value, dict) and isinstance(ADMIN_SETTINGS[key], dict):
            ADMIN_SETTINGS[key].update(value)
        elif key in ADMIN_SETTINGS:
            ADMIN_SETTINGS[key] = value
    return {"success": True, "message": "平台设置已保存（原型内存态）", "settings": deepcopy(ADMIN_SETTINGS)}


def get_audit_logs() -> Dict[str, Any]:
    return {
        "success": True,
        "logs": [
            {"time": _timestamp(), "actor": "ops@radar.cn", "action": "保存平台设置", "target": "合规输出"},
            {"time": "2026-06-08 01:42:12", "actor": "ops@radar.cn", "action": "调整套餐", "target": "标准版"},
            {"time": "2026-06-08 01:21:09", "actor": "system", "action": "拦截输出", "target": "禁止词：目标价"},
        ],
    }
