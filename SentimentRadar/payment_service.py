"""易支付（EPay）签名与跳转 URL 生成。"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any, Dict, Mapping
from urllib.parse import urlencode


def _settings():
    from config import reload_settings

    return reload_settings()


def epay_enabled() -> bool:
    settings = _settings()
    return bool(settings.EPAY_ENABLED)


def epay_configured() -> bool:
    settings = _settings()
    return bool(settings.EPAY_API_URL and settings.EPAY_PID and settings.EPAY_KEY)


def epay_submit_endpoint() -> str:
    settings = _settings()
    base_url = str(settings.EPAY_API_URL or "").strip()
    if not base_url:
        raise ValueError("请先配置 EPAY_API_URL")
    if base_url.endswith(".php"):
        return base_url
    return f"{base_url.rstrip('/')}/submit.php"


def sign_params(params: Mapping[str, Any], key: str) -> str:
    items = []
    for name in sorted(params.keys()):
        if name in {"sign", "sign_type"}:
            continue
        value = params[name]
        if value is None or value == "":
            continue
        items.append(f"{name}={value}")
    raw = "&".join(items) + key
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def verify_epay_notify(params: Mapping[str, Any]) -> bool:
    settings = _settings()
    sign = str(params.get("sign") or "").lower()
    if not sign or not settings.EPAY_KEY:
        return False
    expected = sign_params(params, settings.EPAY_KEY).lower()
    return sign == expected


def create_epay_url(order: Mapping[str, Any], base_url: str) -> str:
    settings = _settings()
    if not epay_configured():
        raise ValueError("请先完整配置易支付参数")

    notify_url = settings.EPAY_NOTIFY_URL or f"{base_url.rstrip('/')}/api/payment/epay/notify"
    return_url = settings.EPAY_RETURN_URL or f"{base_url.rstrip('/')}/api/payment/epay/return"
    money = Decimal(str(order["amount"])).quantize(Decimal("0.01"))
    params: Dict[str, Any] = {
        "pid": settings.EPAY_PID,
        "type": order.get("pay_type") or settings.EPAY_TYPE or "alipay",
        "out_trade_no": order["out_trade_no"],
        "notify_url": notify_url,
        "return_url": return_url,
        "name": order["subject"],
        "money": f"{money:.2f}",
        "sitename": settings.EPAY_NAME_PREFIX or "BettaFish",
    }
    params["sign"] = sign_params(params, settings.EPAY_KEY or "")
    params["sign_type"] = "MD5"
    return f"{epay_submit_endpoint()}?{urlencode(params)}"
