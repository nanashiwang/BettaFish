"""行情数据层：tushare 优先（需 token），akshare 兜底；板块清单与板块日线。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger


class QuoteError(Exception):
    pass


# board: {"code": str, "name": str, "type": "concept"|"industry"}


def _row_value(row: Any, *keys: str) -> Any:
    """兼容不同 Tushare 指数字段命名。"""
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class TushareProvider:
    """同花顺板块指数（ths_index/ths_daily，需要 tushare 积分）。"""

    name = "tushare_ths"

    def __init__(self, token: str):
        import tushare as ts

        self._pro = ts.pro_api(token)

    def list_boards(self) -> List[Dict[str, Any]]:
        boards: List[Dict[str, Any]] = []
        for ths_type, board_type in (("N", "concept"), ("I", "industry")):
            df = self._pro.ths_index(exchange="A", type=ths_type)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                boards.append({
                    "code": str(row["ts_code"]),
                    "name": str(row["name"]),
                    "type": board_type,
                    "provider": self.name,
                })
        if not boards:
            raise QuoteError("tushare ths_index 返回空（可能积分不足）")
        return boards

    def board_history(self, board: Dict[str, Any], start: date, end: date) -> List[Dict[str, Any]]:
        if board.get("provider") and board.get("provider") != self.name:
            raise QuoteError("非同花顺板块，跳过")
        df = self._pro.ths_daily(
            ts_code=board["code"],
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            fields="trade_date,close,pct_change,vol",
        )
        if df is None or df.empty:
            raise QuoteError(f"tushare ths_daily 返回空: {board['name']}")
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "trade_date": str(row["trade_date"]),
                "close": _to_float(row["close"]),
                "pct_chg": _to_float(_row_value(row, "pct_change", "pct_chg")),
                "volume": _to_float(row["vol"]),
            })
        rows.sort(key=lambda item: item["trade_date"])
        return rows


class TushareSWIndustryProvider:
    """申万一级行业降级源：保留 Tushare，但不依赖同花顺 ths_* 权限。"""

    name = "tushare_sw_industry"

    def __init__(self, token: str):
        import tushare as ts

        self._pro = ts.pro_api(token)

    def list_boards(self) -> List[Dict[str, Any]]:
        df = self._pro.index_classify(
            src="SW2021",
            level="L1",
            fields="index_code,industry_name,level,industry_code,is_pub,parent_code",
        )
        if df is None or df.empty:
            raise QuoteError("tushare index_classify 返回空（申万行业降级源不可用）")

        boards: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            code = str(row.get("index_code") or "").strip()
            name = str(row.get("industry_name") or "").strip()
            if not code or not name:
                continue
            boards.append({
                "code": code,
                "name": name,
                "type": "industry",
                "provider": self.name,
            })
        if not boards:
            raise QuoteError("tushare index_classify 未解析到申万一级行业")
        return boards

    def board_history(self, board: Dict[str, Any], start: date, end: date) -> List[Dict[str, Any]]:
        if board.get("provider") and board.get("provider") != self.name:
            raise QuoteError("非申万行业板块，跳过")

        # index_daily 对部分申万代码可能为空；先尝试日线，失败后用周线保证降级可用。
        daily_rows = self._fetch_index_history("index_daily", board, start, end)
        if len(daily_rows) >= 15:
            return daily_rows

        weekly_start = min(start, end - timedelta(days=260))
        weekly_rows = self._fetch_index_history("index_weekly", board, weekly_start, end)
        if len(weekly_rows) < 15:
            raise QuoteError(f"tushare 申万行业行情不足: {board['name']}")
        return weekly_rows

    def _fetch_index_history(
        self, api_name: str, board: Dict[str, Any], start: date, end: date
    ) -> List[Dict[str, Any]]:
        api = getattr(self._pro, api_name)
        df = api(
            ts_code=board["code"],
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            fields="trade_date,close,pct_chg,vol",
        )
        if df is None or df.empty:
            return []

        rows: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            close = _to_float(_row_value(row, "close"))
            if close is None:
                continue
            rows.append({
                "trade_date": str(_row_value(row, "trade_date")),
                "close": close,
                "pct_chg": _to_float(_row_value(row, "pct_chg", "pct_change")),
                "volume": _to_float(_row_value(row, "vol", "volume")),
            })
        rows.sort(key=lambda item: item["trade_date"])
        return rows


class AkshareProvider:
    """东财板块（akshare 免费接口；境外 IPv4 出口可能被 eastmoney 拒绝）。"""

    name = "akshare"

    def list_boards(self) -> List[Dict[str, Any]]:
        import akshare as ak

        boards: List[Dict[str, Any]] = []
        concept = ak.stock_board_concept_name_em()
        for _, row in concept.iterrows():
            boards.append({
                "code": str(row["板块代码"]),
                "name": str(row["板块名称"]),
                "type": "concept",
                "provider": self.name,
            })
        industry = ak.stock_board_industry_name_em()
        for _, row in industry.iterrows():
            boards.append({
                "code": str(row["板块代码"]),
                "name": str(row["板块名称"]),
                "type": "industry",
                "provider": self.name,
            })
        if not boards:
            raise QuoteError("akshare 板块清单为空")
        return boards

    def board_history(self, board: Dict[str, Any], start: date, end: date) -> List[Dict[str, Any]]:
        import akshare as ak

        fetch = (
            ak.stock_board_concept_hist_em
            if board["type"] == "concept"
            else ak.stock_board_industry_hist_em
        )
        df = fetch(
            symbol=board["name"],
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )
        if df is None or df.empty:
            raise QuoteError(f"akshare 板块日线为空: {board['name']}")
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "trade_date": str(row["日期"]).replace("-", ""),
                "close": float(row["收盘"]),
                "pct_chg": float(row["涨跌幅"]),
                "volume": float(row["成交量"]),
            })
        rows.sort(key=lambda item: item["trade_date"])
        return rows


class QuoteService:
    """按提供方链依次尝试，记录实际使用的源。"""

    def __init__(self, tushare_token: str = ""):
        self.providers: List[Any] = []
        if tushare_token:
            try:
                self.providers.append(TushareProvider(tushare_token))
            except Exception as exc:
                logger.warning(f"tushare 同花顺源初始化失败，跳过: {exc}")
            try:
                self.providers.append(TushareSWIndustryProvider(tushare_token))
            except Exception as exc:
                logger.warning(f"tushare 申万行业降级源初始化失败，跳过: {exc}")
        self.providers.append(AkshareProvider())
        self.used_provider: Optional[str] = None

    def _try_chain(self, action: str, func_name: str, *args) -> Any:
        errors = []
        providers = self.providers
        if func_name == "board_history" and args and isinstance(args[0], dict):
            preferred_name = args[0].get("provider")
            if preferred_name:
                preferred = [p for p in self.providers if p.name == preferred_name]
                others = [p for p in self.providers if p.name != preferred_name]
                providers = preferred + others
        for provider in providers:
            try:
                result = getattr(provider, func_name)(*args)
                self.used_provider = provider.name
                return result
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                if "跳过" in str(exc):
                    logger.debug(f"{action} 经 {provider.name} 跳过: {exc}")
                else:
                    logger.warning(f"{action} 经 {provider.name} 失败: {exc}")
        raise QuoteError(f"{action} 全部数据源失败 -> {'; '.join(errors)}")

    def list_boards(self) -> List[Dict[str, Any]]:
        return self._try_chain("获取板块清单", "list_boards")

    def board_history(self, board: Dict[str, Any], days: int = 90) -> List[Dict[str, Any]]:
        end = date.today()
        start = end - timedelta(days=days)
        return self._try_chain(f"获取板块日线[{board['name']}]", "board_history", board, start, end)
