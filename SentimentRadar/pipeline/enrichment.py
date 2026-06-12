"""候选股增强数据：基础资料、财务、公告与资金流。

所有外部数据源都按 best-effort 处理：能取多少补多少，失败不阻塞当日信号管线。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from SentimentRadar.db import get_engine


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _row_value(row: Any, *keys: str) -> Any:
    for key in keys:
        try:
            value = row.get(key)
        except AttributeError:
            value = row[key] if key in row else None
        if value is not None and value != "":
            return value
    return None


def _rows(df: Any) -> List[Dict[str, Any]]:
    if df is None or getattr(df, "empty", True):
        return []
    return [dict(row) for _, row in df.iterrows()]


def _plain_code(ts_code: str) -> str:
    return (ts_code or "").split(".")[0]


_STATE_OWNED_HINTS = (
    "国资委",
    "国有资产",
    "人民政府",
    "财政局",
    "财政厅",
    "财政部",
    "国有资本",
    "国投",
    "国新",
    "中央汇金",
    "中国证券金融",
    "中建",
    "中交",
    "中铁",
    "中电",
    "中国电子",
    "中国移动",
    "中国电信",
    "中国联通",
    "中国石化",
    "中国石油",
    "国家电网",
    "南方电网",
    "地方国资",
)


def _looks_state_owned(*parts: str) -> bool:
    text_blob = " ".join(part for part in parts if part)
    return any(hint in text_blob for hint in _STATE_OWNED_HINTS)


def classify_announcement(title: str) -> str:
    title = title or ""
    rules = [
        ("业绩预告", ("业绩预告", "业绩快报", "盈利预", "扭亏")),
        ("定期报告", ("年度报告", "半年度报告", "季度报告", "一季报", "三季报")),
        ("订单合同", ("合同", "订单", "框架协议", "战略合作")),
        ("中标", ("中标", "候选人", "项目预中标")),
        ("产能项目", ("投产", "产线", "产能", "募投项目", "建设项目", "环评")),
        ("并购重组", ("收购", "并购", "重组", "资产购买", "股权转让")),
        ("融资定增", ("定增", "非公开发行", "可转债", "募集资金", "再融资")),
        ("减持质押", ("减持", "质押", "解除质押")),
        ("风险提示", ("风险提示", "澄清", "异常波动", "问询函", "监管函")),
    ]
    for label, keywords in rules:
        if any(keyword in title for keyword in keywords):
            return label
    return "其他公告"


class StockEnrichmentService:
    """补齐与当前候选股逻辑最贴近的五类公开数据。"""

    def __init__(self, tushare_token: str = ""):
        self._pro = None
        self._quote_cache: Dict[str, Dict[str, Any]] = {}
        self._profile_cache: Dict[str, Dict[str, Any]] = {}
        self._financial_cache: Dict[str, Dict[str, Any]] = {}
        self._ann_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._moneyflow_cache: Dict[str, Dict[str, Any]] = {}
        if tushare_token:
            try:
                import tushare as ts

                self._pro = ts.pro_api(tushare_token)
            except Exception as exc:  # pragma: no cover - depends on optional credentials
                logger.warning(f"Tushare 增强数据源初始化失败，跳过: {exc}")

    @property
    def enabled(self) -> bool:
        return self._pro is not None

    def enrich_candidates(
        self,
        candidates: List[Dict[str, Any]],
        board: Dict[str, Any],
        trade_date: date,
    ) -> Dict[str, int]:
        """就地增强候选股，返回各类数据补齐数量。"""
        stats = {
            "quote_metrics": 0,
            "profiles": 0,
            "financials": 0,
            "announcements": 0,
            "stock_moneyflow": 0,
            "board_moneyflow": 0,
        }
        if not candidates:
            return stats

        for item in candidates:
            code = item.get("code", "")
            quote_metrics = self.stock_quote_metrics(code, trade_date)
            if quote_metrics:
                item["quote_metrics"] = quote_metrics
                stats["quote_metrics"] += 1

            profile = self.company_profile(code, item.get("name", ""))
            if profile:
                item["company_profile"] = profile
                stats["profiles"] += 1

            financial = self.financial_metrics(code)
            if financial:
                item["financial"] = financial
                stats["financials"] += 1

            anns = self.announcements(code, trade_date)
            if anns:
                item["announcements"] = anns[:3]
                stats["announcements"] += len(anns[:3])

            money_flow = self.stock_moneyflow(code, trade_date)
            if money_flow:
                item["money_flow"] = money_flow
                stats["stock_moneyflow"] += 1

        board_flow = self.board_moneyflow(board, candidates, trade_date)
        if board_flow:
            for item in candidates:
                item.setdefault("board_money_flow", board_flow)
            stats["board_moneyflow"] = 1
        return stats

    def stock_quote_metrics(self, code: str, trade_date: date) -> Dict[str, Any]:
        """补充换手率、估值、市值等与候选股行情最贴近的指标。"""
        if not code or not self.enabled:
            return {}
        cache_key = f"{code}-{trade_date:%Y%m%d}"
        if cache_key in self._quote_cache:
            return self._quote_cache[cache_key]

        start = trade_date - timedelta(days=30)
        try:
            daily_rows: List[Dict[str, Any]] = []
            try:
                daily = self._pro.daily(
                    ts_code=code,
                    start_date=start.strftime("%Y%m%d"),
                    end_date=trade_date.strftime("%Y%m%d"),
                    fields="ts_code,trade_date,close,pct_chg,amount,vol",
                )
                daily_rows = _rows(daily)
            except Exception as exc:
                logger.debug(f"个股日线增强拉取失败 {code}: {exc}")

            basic_rows: List[Dict[str, Any]] = []
            try:
                basic = self._pro.daily_basic(
                    ts_code=code,
                    start_date=start.strftime("%Y%m%d"),
                    end_date=trade_date.strftime("%Y%m%d"),
                    fields=(
                        "ts_code,trade_date,turnover_rate,volume_ratio,pe,pb,"
                        "total_mv,circ_mv"
                    ),
                )
                basic_rows = _rows(basic)
            except Exception as exc:
                logger.debug(f"个股 daily_basic 拉取失败 {code}: {exc}")

            daily_rows.sort(key=lambda r: str(r.get("trade_date") or ""), reverse=True)
            basic_rows.sort(key=lambda r: str(r.get("trade_date") or ""), reverse=True)
            if not daily_rows and not basic_rows:
                return {}

            daily_row = daily_rows[0] if daily_rows else {}
            basic_row = basic_rows[0] if basic_rows else {}
            trade_date_value = str(
                _row_value(daily_row, "trade_date") or _row_value(basic_row, "trade_date") or ""
            )
            metrics = {
                "code": code,
                "trade_date": trade_date_value,
                "close": _to_float(_row_value(daily_row, "close")),
                "pct_chg": _to_float(_row_value(daily_row, "pct_chg")),
                "turnover_rate": _to_float(_row_value(basic_row, "turnover_rate")),
                "volume_ratio": _to_float(_row_value(basic_row, "volume_ratio")),
                "amount": _to_float(_row_value(daily_row, "amount")),
                "pe": _to_float(_row_value(basic_row, "pe")),
                "pb": _to_float(_row_value(basic_row, "pb")),
                "total_mv": _to_float(_row_value(basic_row, "total_mv")),
                "circ_mv": _to_float(_row_value(basic_row, "circ_mv")),
                "source": "tushare",
            }
            self._save_quote_metrics(metrics, {**basic_row, **daily_row})
            self._quote_cache[cache_key] = metrics
            return metrics
        except Exception as exc:
            logger.debug(f"个股行情增强失败 {code}: {exc}")
            return {}

    def company_profile(self, code: str, fallback_name: str = "") -> Dict[str, Any]:
        if not code:
            return {}
        if code in self._profile_cache:
            return self._profile_cache[code]
        if not self.enabled:
            return {}

        profile = {
            "code": code,
            "name": fallback_name,
            "industry": "",
            "area": "",
            "market": "",
            "list_date": "",
            "main_business": "",
            "top_holder": "",
            "controller": "",
            "is_state_owned": False,
            "soe_tag": "",
            "source": "",
        }

        try:
            basic = _rows(self._pro.stock_basic(ts_code=code, fields="ts_code,name,area,industry,market,list_date"))
            if basic:
                row = basic[0]
                profile.update({
                    "name": str(row.get("name") or fallback_name),
                    "industry": str(row.get("industry") or ""),
                    "area": str(row.get("area") or ""),
                    "market": str(row.get("market") or ""),
                    "list_date": str(row.get("list_date") or ""),
                    "source": "tushare",
                })
        except Exception as exc:
            logger.debug(f"股票基础资料拉取失败 {code}: {exc}")

        try:
            company = _rows(self._pro.stock_company(ts_code=code))
            if company:
                row = company[0]
                profile["main_business"] = str(
                    _row_value(row, "main_business", "business_scope", "introduction") or ""
                )[:500]
                profile["controller"] = str(_row_value(row, "chairman", "manager") or "")
                profile["source"] = profile["source"] or "tushare"
        except Exception as exc:
            logger.debug(f"公司资料拉取失败 {code}: {exc}")

        try:
            holders = _rows(self._pro.top10_holders(ts_code=code))
            holders.sort(key=lambda r: (str(r.get("end_date") or ""), _to_float(r.get("hold_ratio")) or 0), reverse=True)
            if holders:
                profile["top_holder"] = str(_row_value(holders[0], "holder_name") or "")[:200]
                profile["source"] = profile["source"] or "tushare"
        except Exception as exc:
            logger.debug(f"前十大股东拉取失败 {code}: {exc}")

        profile["is_state_owned"] = _looks_state_owned(
            profile.get("top_holder", ""), profile.get("controller", ""), profile.get("main_business", "")
        )
        profile["soe_tag"] = "国资相关" if profile["is_state_owned"] else "非国资/待核验"
        if not profile["source"]:
            self._profile_cache[code] = {}
            return {}
        self._save_profile(profile)
        self._profile_cache[code] = profile
        return profile

    def financial_metrics(self, code: str) -> Dict[str, Any]:
        if not code:
            return {}
        if code in self._financial_cache:
            return self._financial_cache[code]
        if not self.enabled:
            return {}

        try:
            try:
                df = self._pro.fina_indicator(
                    ts_code=code,
                    fields=(
                        "ts_code,ann_date,end_date,or_yoy,netprofit_yoy,grossprofit_margin,"
                        "roe,debt_to_assets,ocf_to_or,rd_exp"
                    ),
                )
            except Exception:
                df = self._pro.fina_indicator(ts_code=code)
            rows = _rows(df)
            rows.sort(key=lambda r: (str(r.get("end_date") or ""), str(r.get("ann_date") or "")), reverse=True)
            if not rows:
                return {}
            row = rows[0]
            metrics = {
                "code": code,
                "period": str(_row_value(row, "end_date") or ""),
                "ann_date": str(_row_value(row, "ann_date") or ""),
                "revenue_yoy": _to_float(_row_value(row, "or_yoy", "q_sales_yoy", "tr_yoy")),
                "profit_yoy": _to_float(_row_value(row, "netprofit_yoy", "q_profit_yoy", "dt_netprofit_yoy")),
                "gross_margin": _to_float(_row_value(row, "grossprofit_margin", "gross_margin")),
                "roe": _to_float(_row_value(row, "roe", "roe_dt")),
                "debt_to_assets": _to_float(_row_value(row, "debt_to_assets")),
                "ocf_to_revenue": _to_float(_row_value(row, "ocf_to_or")),
                "rd_exp": _to_float(_row_value(row, "rd_exp")),
                "source": "tushare",
            }
            self._save_financial(metrics, row)
            self._financial_cache[code] = metrics
            return metrics
        except Exception as exc:
            logger.debug(f"财务指标拉取失败 {code}: {exc}")
            return {}

    def announcements(self, code: str, trade_date: date, limit: int = 5) -> List[Dict[str, Any]]:
        if not code:
            return []
        cache_key = f"{code}-{trade_date:%Y%m%d}-{limit}"
        if cache_key in self._ann_cache:
            return self._ann_cache[cache_key]
        if not self.enabled:
            return []

        start = trade_date - timedelta(days=180)
        try:
            try:
                df = self._pro.anns(
                    ts_code=code,
                    start_date=start.strftime("%Y%m%d"),
                    end_date=trade_date.strftime("%Y%m%d"),
                    fields="ts_code,ann_date,title,url",
                )
            except Exception:
                df = self._pro.anns(
                    ts_code=code,
                    start_date=start.strftime("%Y%m%d"),
                    end_date=trade_date.strftime("%Y%m%d"),
                )
            rows = _rows(df)
            rows.sort(key=lambda r: str(r.get("ann_date") or ""), reverse=True)
            anns: List[Dict[str, Any]] = []
            for row in rows[:limit]:
                title = str(_row_value(row, "title", "ann_title") or "")[:300]
                if not title:
                    continue
                ann = {
                    "code": code,
                    "ann_date": str(_row_value(row, "ann_date") or ""),
                    "title": title,
                    "type": classify_announcement(title),
                    "url": str(_row_value(row, "url", "ann_url") or ""),
                    "source": "tushare",
                }
                anns.append(ann)
            if anns:
                self._save_announcements(anns)
            self._ann_cache[cache_key] = anns
            return anns
        except Exception as exc:
            logger.debug(f"公告拉取失败 {code}: {exc}")
            return []

    def stock_moneyflow(self, code: str, trade_date: date) -> Dict[str, Any]:
        if not code:
            return {}
        cache_key = f"{code}-{trade_date:%Y%m%d}"
        if cache_key in self._moneyflow_cache:
            return self._moneyflow_cache[cache_key]
        if not self.enabled:
            return {}

        start = trade_date - timedelta(days=30)
        try:
            try:
                df = self._pro.moneyflow(
                    ts_code=code,
                    start_date=start.strftime("%Y%m%d"),
                    end_date=trade_date.strftime("%Y%m%d"),
                    fields=(
                        "ts_code,trade_date,buy_sm_amount,sell_sm_amount,buy_md_amount,sell_md_amount,"
                        "buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount,net_mf_amount"
                    ),
                )
            except Exception:
                df = self._pro.moneyflow(
                    ts_code=code,
                    start_date=start.strftime("%Y%m%d"),
                    end_date=trade_date.strftime("%Y%m%d"),
                )
            rows = _rows(df)
            rows.sort(key=lambda r: str(r.get("trade_date") or ""), reverse=True)
            if not rows:
                return {}
            row = rows[0]
            net = _to_float(_row_value(row, "net_mf_amount"))
            total = sum(
                _to_float(_row_value(row, key)) or 0.0
                for key in (
                    "buy_sm_amount", "sell_sm_amount", "buy_md_amount", "sell_md_amount",
                    "buy_lg_amount", "sell_lg_amount", "buy_elg_amount", "sell_elg_amount",
                )
            )
            ratio = round(net / total * 100, 4) if net is not None and total else None
            money_flow = {
                "code": code,
                "trade_date": str(_row_value(row, "trade_date") or ""),
                "net_mf_amount": net,
                "net_mf_ratio": ratio,
                "source": "tushare",
            }
            self._save_stock_moneyflow(money_flow, row)
            self._moneyflow_cache[cache_key] = money_flow
            return money_flow
        except Exception as exc:
            logger.debug(f"个股资金流拉取失败 {code}: {exc}")
            return {}

    def board_moneyflow(
        self, board: Dict[str, Any], candidates: List[Dict[str, Any]], trade_date: date
    ) -> Dict[str, Any]:
        flow = self._akshare_board_moneyflow(board, trade_date)
        if flow:
            self._save_board_moneyflow(flow)
            return flow

        amounts = [c.get("money_flow", {}).get("net_mf_amount") for c in candidates]
        amounts = [value for value in amounts if isinstance(value, (int, float))]
        ratios = [c.get("money_flow", {}).get("net_mf_ratio") for c in candidates]
        ratios = [value for value in ratios if isinstance(value, (int, float))]
        if not amounts:
            return {}
        flow = {
            "board_code": board.get("code", ""),
            "board_name": board.get("name", ""),
            "trade_date": trade_date.strftime("%Y%m%d"),
            "net_mf_amount": round(sum(amounts), 4),
            "net_mf_ratio": round(sum(ratios) / len(ratios), 4) if ratios else None,
            "source": "candidate_sum",
        }
        self._save_board_moneyflow(flow)
        return flow

    def _akshare_board_moneyflow(self, board: Dict[str, Any], trade_date: date) -> Dict[str, Any]:
        try:
            import akshare as ak

            sector_type = "概念资金流" if board.get("type") == "concept" else "行业资金流"
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type=sector_type)
            rows = _rows(df)
            target = board.get("name", "")
            row = next((item for item in rows if str(item.get("名称") or item.get("板块名称") or "") == target), None)
            if not row:
                return {}
            net = _to_float(_row_value(row, "今日主力净流入-净额", "主力净流入-净额", "净流入"))
            ratio = _to_float(_row_value(row, "今日主力净流入-净占比", "主力净流入-净占比", "净占比"))
            return {
                "board_code": board.get("code", ""),
                "board_name": target,
                "trade_date": trade_date.strftime("%Y%m%d"),
                "net_mf_amount": net,
                "net_mf_ratio": ratio,
                "source": "akshare",
            }
        except Exception as exc:
            logger.debug(f"板块资金流拉取失败 {board.get('name')}: {exc}")
            return {}

    def _save_quote_metrics(self, metrics: Dict[str, Any], raw: Dict[str, Any]) -> None:
        if not metrics.get("trade_date"):
            return
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_stock_quote_metrics
                        (code, trade_date, close, pct_chg, turnover_rate, volume_ratio, amount,
                         pe, pb, total_mv, circ_mv, source, raw, updated_at)
                    VALUES
                        (:code, :trade_date, :close, :pct_chg, :turnover_rate, :volume_ratio, :amount,
                         :pe, :pb, :total_mv, :circ_mv, :source, CAST(:raw AS JSONB), NOW())
                    ON CONFLICT (code, trade_date) DO UPDATE SET
                        close = EXCLUDED.close,
                        pct_chg = EXCLUDED.pct_chg,
                        turnover_rate = EXCLUDED.turnover_rate,
                        volume_ratio = EXCLUDED.volume_ratio,
                        amount = EXCLUDED.amount,
                        pe = EXCLUDED.pe,
                        pb = EXCLUDED.pb,
                        total_mv = EXCLUDED.total_mv,
                        circ_mv = EXCLUDED.circ_mv,
                        source = EXCLUDED.source,
                        raw = EXCLUDED.raw,
                        updated_at = NOW()
                    """
                ),
                {**metrics, "raw": json.dumps(raw, ensure_ascii=False, default=str)},
            )

    def _save_profile(self, profile: Dict[str, Any]) -> None:
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_stock_profiles
                        (code, name, industry, area, market, list_date, main_business, top_holder,
                         controller, is_state_owned, soe_tag, source, updated_at)
                    VALUES
                        (:code, :name, :industry, :area, :market, :list_date, :main_business, :top_holder,
                         :controller, :is_state_owned, :soe_tag, :source, NOW())
                    ON CONFLICT (code) DO UPDATE SET
                        name = EXCLUDED.name,
                        industry = EXCLUDED.industry,
                        area = EXCLUDED.area,
                        market = EXCLUDED.market,
                        list_date = EXCLUDED.list_date,
                        main_business = EXCLUDED.main_business,
                        top_holder = EXCLUDED.top_holder,
                        controller = EXCLUDED.controller,
                        is_state_owned = EXCLUDED.is_state_owned,
                        soe_tag = EXCLUDED.soe_tag,
                        source = EXCLUDED.source,
                        updated_at = NOW()
                    """
                ),
                profile,
            )

    def _save_financial(self, metrics: Dict[str, Any], raw: Dict[str, Any]) -> None:
        if not metrics.get("period"):
            return
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_stock_financials
                        (code, period, ann_date, revenue_yoy, profit_yoy, gross_margin, roe,
                         debt_to_assets, ocf_to_revenue, rd_exp, source, raw, updated_at)
                    VALUES
                        (:code, :period, :ann_date, :revenue_yoy, :profit_yoy, :gross_margin, :roe,
                         :debt_to_assets, :ocf_to_revenue, :rd_exp, :source, CAST(:raw AS JSONB), NOW())
                    ON CONFLICT (code, period) DO UPDATE SET
                        ann_date = EXCLUDED.ann_date,
                        revenue_yoy = EXCLUDED.revenue_yoy,
                        profit_yoy = EXCLUDED.profit_yoy,
                        gross_margin = EXCLUDED.gross_margin,
                        roe = EXCLUDED.roe,
                        debt_to_assets = EXCLUDED.debt_to_assets,
                        ocf_to_revenue = EXCLUDED.ocf_to_revenue,
                        rd_exp = EXCLUDED.rd_exp,
                        source = EXCLUDED.source,
                        raw = EXCLUDED.raw,
                        updated_at = NOW()
                    """
                ),
                {**metrics, "raw": json.dumps(raw, ensure_ascii=False, default=str)},
            )

    def _save_announcements(self, anns: List[Dict[str, Any]]) -> None:
        with get_engine().begin() as conn:
            for ann in anns:
                conn.execute(
                    text(
                        """
                        INSERT INTO radar_stock_announcements
                            (code, ann_date, title, type, url, source, updated_at)
                        VALUES
                            (:code, :ann_date, :title, :type, :url, :source, NOW())
                        ON CONFLICT (code, ann_date, title) DO UPDATE SET
                            type = EXCLUDED.type,
                            url = EXCLUDED.url,
                            source = EXCLUDED.source,
                            updated_at = NOW()
                        """
                    ),
                    ann,
                )

    def _save_stock_moneyflow(self, flow: Dict[str, Any], raw: Dict[str, Any]) -> None:
        if not flow.get("trade_date"):
            return
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_stock_moneyflow
                        (code, trade_date, net_mf_amount, net_mf_ratio, source, raw, updated_at)
                    VALUES
                        (:code, :trade_date, :net_mf_amount, :net_mf_ratio, :source, CAST(:raw AS JSONB), NOW())
                    ON CONFLICT (code, trade_date) DO UPDATE SET
                        net_mf_amount = EXCLUDED.net_mf_amount,
                        net_mf_ratio = EXCLUDED.net_mf_ratio,
                        source = EXCLUDED.source,
                        raw = EXCLUDED.raw,
                        updated_at = NOW()
                    """
                ),
                {**flow, "raw": json.dumps(raw, ensure_ascii=False, default=str)},
            )

    def _save_board_moneyflow(self, flow: Dict[str, Any]) -> None:
        if not flow.get("trade_date") or not flow.get("board_code"):
            return
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_board_moneyflow
                        (board_code, trade_date, board_name, net_mf_amount, net_mf_ratio, source, raw, updated_at)
                    VALUES
                        (:board_code, :trade_date, :board_name, :net_mf_amount, :net_mf_ratio,
                         :source, CAST(:raw AS JSONB), NOW())
                    ON CONFLICT (board_code, trade_date) DO UPDATE SET
                        board_name = EXCLUDED.board_name,
                        net_mf_amount = EXCLUDED.net_mf_amount,
                        net_mf_ratio = EXCLUDED.net_mf_ratio,
                        source = EXCLUDED.source,
                        raw = EXCLUDED.raw,
                        updated_at = NOW()
                    """
                ),
                {**flow, "raw": json.dumps(flow, ensure_ascii=False, default=str)},
            )
