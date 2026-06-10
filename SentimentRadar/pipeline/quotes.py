"""行情数据层：tushare 优先（需 token），akshare 兜底；板块清单与板块日线。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger


class QuoteError(Exception):
    pass


# board: {"code": str, "name": str, "type": "concept"|"industry"}


class TushareProvider:
    """同花顺板块指数（ths_index/ths_daily，需要 tushare 积分）。"""

    name = "tushare"

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
                })
        if not boards:
            raise QuoteError("tushare ths_index 返回空（可能积分不足）")
        return boards

    def board_history(self, board: Dict[str, Any], start: date, end: date) -> List[Dict[str, Any]]:
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
                "close": float(row["close"]) if row["close"] is not None else None,
                "pct_chg": float(row["pct_change"]) if row["pct_change"] is not None else None,
                "volume": float(row["vol"]) if row["vol"] is not None else None,
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
            })
        industry = ak.stock_board_industry_name_em()
        for _, row in industry.iterrows():
            boards.append({
                "code": str(row["板块代码"]),
                "name": str(row["板块名称"]),
                "type": "industry",
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
                logger.warning(f"tushare 初始化失败，跳过: {exc}")
        self.providers.append(AkshareProvider())
        self.used_provider: Optional[str] = None

    def _try_chain(self, action: str, func_name: str, *args) -> Any:
        errors = []
        for provider in self.providers:
            try:
                result = getattr(provider, func_name)(*args)
                self.used_provider = provider.name
                return result
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                logger.warning(f"{action} 经 {provider.name} 失败: {exc}")
        raise QuoteError(f"{action} 全部数据源失败 -> {'; '.join(errors)}")

    def list_boards(self) -> List[Dict[str, Any]]:
        return self._try_chain("获取板块清单", "list_boards")

    def board_history(self, board: Dict[str, Any], days: int = 90) -> List[Dict[str, Any]]:
        end = date.today()
        start = end - timedelta(days=days)
        return self._try_chain(f"获取板块日线[{board['name']}]", "board_history", board, start, end)
