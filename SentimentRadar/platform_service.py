"""A 股舆情雷达平台能力 Mock 服务。

该模块提供登录、订阅、账户和管理后台的可运行 API 数据结构。
当前为原型内存态，后续可以替换为数据库、支付和真实权限系统。
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List


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


# 原型内存注册用户表：键为小写邮箱，密码与用户资料分开存放，避免随 user 返回前端。
REGISTERED_USERS: Dict[str, Dict[str, Any]] = {}


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
        "email": "wang@example.com",
        "phone": "138****2688",
        "role": "订阅用户",
        "plan": "标准版",
        "expires_at": _date_after(30),
        "usage": "3条 / 14关注",
        "status": "正常",
        "last_active": "2 分钟前",
        "note": "用户多次查看 AI 算力主题证据链，未出现异常调用。",
    },
    {
        "id": "u_10002",
        "name": "内容号 A",
        "email": "creator@radar.cn",
        "phone": "139****1024",
        "role": "创作者",
        "plan": "创作者版",
        "expires_at": _date_after(180),
        "usage": "3条 / 186关注",
        "status": "高用量",
        "last_active": "18 分钟前",
        "note": "素材导出频率较高，成本仍在套餐范围内。",
    },
    {
        "id": "u_10003",
        "name": "李女士",
        "email": "li@example.com",
        "phone": "138****9120",
        "role": "免费用户",
        "plan": "免费版",
        "expires_at": "-",
        "usage": "1条 / 5关注",
        "status": "未订阅",
        "last_active": "1 小时前",
        "note": "多次点击订阅页，适合运营触达。",
    },
    {
        "id": "u_10004",
        "name": "测试账号",
        "email": "test@example.com",
        "phone": "137****0001",
        "role": "订阅用户",
        "plan": "专业版",
        "expires_at": _date_after(16),
        "usage": "3条 / 82关注",
        "status": "冻结",
        "last_active": "昨天",
        "note": "测试用账号，禁止真实推送。",
    },
    {
        "id": "u_10005",
        "name": "运营账号",
        "email": "ops@radar.cn",
        "phone": "136****7788",
        "role": "管理员",
        "plan": "内部",
        "expires_at": "-",
        "usage": "不限",
        "status": "正常",
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


def register(payload: Dict[str, Any]) -> Dict[str, Any]:
    """原型注册：写入内存用户表，新用户默认免费版套餐。"""
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    if "@" not in email:
        return {"success": False, "message": "请输入有效邮箱"}
    if len(password) < 6:
        return {"success": False, "message": "密码至少 6 位"}
    if email in REGISTERED_USERS or email == CURRENT_USER["email"]:
        return {"success": False, "message": "该邮箱已注册，请直接登录"}

    user = deepcopy(CURRENT_USER)
    user.update({
        "id": f"u_{10100 + len(REGISTERED_USERS)}",
        "name": email.split("@")[0],
        "email": email,
        "phone": "",
        "plan_id": "free",
        "risk_confirmed": bool(payload.get("risk_confirmed", True)),
        "risk_version": "v2026.06",
        "last_login_at": _timestamp(),
    })
    subscription = deepcopy(FREE_SUBSCRIPTION)
    subscription["started_at"] = datetime.now().strftime("%Y-%m-%d")
    REGISTERED_USERS[email] = {"user": user, "password": password, "subscription": subscription}
    return {
        "success": True,
        "message": "注册成功（原型模式）",
        "token": "mock-radar-session-token",
        "user": deepcopy(user),
        "subscription": deepcopy(subscription),
    }


def login(payload: Dict[str, Any]) -> Dict[str, Any]:
    account = payload.get("account") or payload.get("email") or CURRENT_USER["email"]
    confirmed = bool(payload.get("risk_confirmed", True))

    # 已注册账号：校验密码；未注册账号走下方原型任意登录（保留演示账号行为）。
    registered = REGISTERED_USERS.get(str(account).strip().lower())
    if registered:
        if str(payload.get("password") or payload.get("code") or "") != registered["password"]:
            return {"success": False, "message": "账号或密码错误"}
        registered["user"]["risk_confirmed"] = confirmed
        registered["user"]["last_login_at"] = _timestamp()
        return {
            "success": True,
            "message": "登录成功（原型模式）",
            "token": "mock-radar-session-token",
            "user": deepcopy(registered["user"]),
            "subscription": deepcopy(registered["subscription"]),
        }

    user = deepcopy(CURRENT_USER)
    user["email"] = account if "@" in str(account) else CURRENT_USER["email"]
    user["phone"] = account if "@" not in str(account) else CURRENT_USER["phone"]
    user["risk_confirmed"] = confirmed
    user["last_login_at"] = _timestamp()
    subscription = deepcopy(SUBSCRIPTION)

    # 原型阶段用账号区分普通用户和管理员，后续替换为正式 RBAC。
    account_text = str(account).lower()
    if "ops" in account_text or "admin" in account_text:
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


def get_plans() -> Dict[str, Any]:
    return {
        "success": True,
        "plans": deepcopy(PLANS),
        "current_plan_id": SUBSCRIPTION["plan_id"],
        "disclaimer": "订阅只增加舆情摘要、证据链深度、关注数量和推送能力，不构成投资建议。",
    }


def subscribe(payload: Dict[str, Any]) -> Dict[str, Any]:
    plan_id = payload.get("plan_id", "standard")
    plan = next((item for item in PLANS if item["id"] == plan_id), PLANS[1])
    SUBSCRIPTION.update({
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "status": "active",
        "started_at": datetime.now().strftime("%Y-%m-%d"),
        "expires_at": _date_after(30),
    })
    return {
        "success": True,
        "message": f"已切换为 {plan['name']}（原型模式，未发起真实支付）",
        "subscription": deepcopy(SUBSCRIPTION),
    }


def get_subscription() -> Dict[str, Any]:
    return {
        "success": True,
        "subscription": deepcopy(SUBSCRIPTION),
        "plan": next((deepcopy(item) for item in PLANS if item["id"] == SUBSCRIPTION["plan_id"]), deepcopy(PLANS[1])),
    }


def get_usage() -> Dict[str, Any]:
    return {"success": True, "usage": deepcopy(USAGE), "updated_at": _timestamp()}


def get_bills() -> Dict[str, Any]:
    return {"success": True, "bills": deepcopy(BILLS)}


def get_account() -> Dict[str, Any]:
    return {
        "success": True,
        "user": deepcopy(CURRENT_USER),
        "subscription": deepcopy(SUBSCRIPTION),
        "usage": deepcopy(USAGE),
        "bills": deepcopy(BILLS),
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
            for key in ("status", "plan", "note", "role"):
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
