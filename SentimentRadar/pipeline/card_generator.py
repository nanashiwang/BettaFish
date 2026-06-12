"""预判卡生成：把真实信号数据交给 LLM 产出当日 Top3 预判卡与头条判断。"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List

from sqlalchemy import text

from SentimentRadar.db import get_engine
from SentimentRadar.pipeline.llm import invoke_json

_SYSTEM = (
    "你是 A 股舆情雷达的分析师。基于给定的真实信号数据（舆情热度、板块行情、关联新闻）"
    "撰写预判卡。要求：客观克制、只描述舆情与价格的observable事实和风险，"
    "禁止使用'买入/卖出/加仓/目标价'等投资建议词汇。只输出 JSON。"
)

_USER_TEMPLATE = """今日日期：{today}

以下是今日筛选出的 {count} 个舆情-价格信号（数据均为真实计算结果）：

{signals_text}

场景说明：
- 先闻后动：舆情热度已起、板块价格尚未明显反应，存在关注窗口，但需警惕消息有效性
- 同步共振：舆情与板块价格同步走强，主线确认但需警惕过热
- 先动后闻：板块价格先动、舆情后起，存在消息兑现/出货风险，定调必须是警惕提醒

任务：为每个信号生成一张预判卡，并给出一句话当日头条（headline，60 字内，概括今日主线与最大风险）。

输出 JSON 格式：
{{
  "headline": "...",
  "cards": [
    {{
      "signal_index": 1,
      "title": "12 字内标题",
      "judgement": "一句话核心判断（40 字内）",
      "reason": "依据（50 字内，引用热度与行情数据）",
      "risk": "风险（40 字内）",
      "next": "后续观察点（40 字内）",
      "tags": ["话题词", "场景", "板块"],
      "detail": {{
        "summary": "80 字内综合解读",
        "why": ["判断依据 1", "判断依据 2", "判断依据 3"],
        "timeline": [{{"time": "今日", "label": "舆情信号", "text": "..."}}],
        "evidence_chain": [{{"source": "来源名", "count": 1, "credibility": "高/较高/中/中低", "note": "说明"}}],
        "risk_boundary": ["该判断失效的条件 1", "条件 2"],
        "next_watch": ["观察点 1", "观察点 2"]
      }}
    }}
  ]
}}

注意：evidence_chain 的来源与数量必须基于给到的真实新闻来源统计；timeline 基于真实信息，不要编造具体时刻。"""


def _fmt_num(value: Any, suffix: str = "", default: str = "-") -> str:
    if value is None or value == "":
        return default
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    return f"{num:+.2f}{suffix}" if suffix == "%" else f"{num:.2f}{suffix}"


def _fmt_amount(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "-"
    if abs(num) >= 10000:
        return f"{num / 10000:+.2f}亿"
    return f"{num:+.0f}万"


def _stock_line(item: Dict[str, Any]) -> str:
    profile = item.get("company_profile") or {}
    financial = item.get("financial") or {}
    quote = item.get("quote_metrics") or {}
    announcements = item.get("announcements") or []
    money_flow = item.get("money_flow") or {}
    board_flow = item.get("board_money_flow") or {}

    parts = [
        f"{item['name']}({item['code']}) {item['label']}",
        f"3日{_fmt_num(item.get('return_3d'), '%')}",
        f"量比{_fmt_num(item.get('volume_ratio'))}",
    ]
    if quote:
        parts.append(
            f"换手{_fmt_num(quote.get('turnover_rate'), '%')} PE{_fmt_num(quote.get('pe'))}"
        )
    if profile:
        parts.append(
            f"{profile.get('soe_tag') or '股权待核验'} {profile.get('industry') or ''}".strip()
        )
    if financial:
        parts.append(
            f"营收{_fmt_num(financial.get('revenue_yoy'), '%')} 净利{_fmt_num(financial.get('profit_yoy'), '%')} ROE{_fmt_num(financial.get('roe'), '%')}"
        )
    if announcements:
        latest = announcements[0]
        parts.append(f"公告[{latest.get('type')}] {str(latest.get('title') or '')[:28]}")
    if money_flow:
        parts.append(
            f"个股资金{_fmt_amount(money_flow.get('net_mf_amount'))} 占比{_fmt_num(money_flow.get('net_mf_ratio'), '%')}"
        )
    if board_flow:
        parts.append(f"板块资金{_fmt_amount(board_flow.get('net_mf_amount'))}")
    return " / ".join(part for part in parts if part and part != "-")


def _stock_evidence_summary(stocks: List[Dict[str, Any]]) -> str:
    if not stocks:
        return "个股证据 0 项"
    return (
        f"行情增强 {sum(1 for s in stocks if s.get('quote_metrics'))} / "
        f"基础资料 {sum(1 for s in stocks if s.get('company_profile'))} / "
        f"财务 {sum(1 for s in stocks if s.get('financial'))} / "
        f"公告 {sum(len(s.get('announcements') or []) for s in stocks)} / "
        f"资金流 {sum(1 for s in stocks if s.get('money_flow'))}"
    )


def _signal_text(index: int, signal: Dict[str, Any], news: List[Dict[str, Any]]) -> str:
    topic = signal["topic"]
    board = signal["board"]
    metrics = signal["metrics"]
    stocks = signal.get("stock_candidates") or []
    titles = []
    source_counts: Dict[str, int] = {}
    for news_index in topic["news_indexes"][:8]:
        item = news[news_index - 1]
        titles.append(f"  - [{item['source_name']}] {item['title']}")
    for news_index in topic["news_indexes"]:
        name = news[news_index - 1]["source_name"]
        source_counts[name] = source_counts.get(name, 0) + 1
    sources = "、".join(f"{name}{count}条" for name, count in source_counts.items())
    stock_text = "暂无"
    if stocks:
        stock_text = "；".join(_stock_line(item) for item in stocks[:6])
    return (
        f"信号 {index}：{topic['name']}（场景：{signal['scenario']}，强度：{signal['strength']}）\n"
        f"- 舆情：热度分 {topic['heat_score']}（z={topic['heat_z']}），覆盖来源：{sources}\n"
        f"- 板块：{board['name']}（{board['type']}），近 3 日涨幅 {metrics['return_3d']}%"
        f"（z={metrics['price_z']}），量比 {metrics['volume_ratio']}\n"
        f"- 个股观察池：{stock_text}\n"
        f"- 个股证据覆盖：{_stock_evidence_summary(stocks)}\n"
        f"- 关联热榜：\n" + "\n".join(titles)
    )


def generate_cards(
    trade_date: date,
    signals: List[Dict[str, Any]],
    news: List[Dict[str, Any]],
    model: str,
) -> List[Dict[str, Any]]:
    """LLM 生成预判卡并落库，返回卡片记录。"""
    top = signals[:3]
    signals_text = "\n\n".join(_signal_text(i + 1, s, news) for i, s in enumerate(top))
    result = invoke_json(
        _SYSTEM,
        _USER_TEMPLATE.format(today=trade_date.isoformat(), count=len(top), signals_text=signals_text),
        model=model,
        max_tokens=4000,
    )
    headline = str(result.get("headline") or "").strip()[:300]
    cards = []
    for rank, card in enumerate(result.get("cards", [])[: len(top)], start=1):
        signal = top[(card.get("signal_index") or rank) - 1]
        topic = signal["topic"]
        news_count = len(topic["news_indexes"])
        detail = card.get("detail") or {}
        detail["stock_candidates"] = signal.get("stock_candidates", [])
        record = {
            "trade_date": trade_date,
            "rank": rank,
            "card_id": f"{trade_date.strftime('%Y%m%d')}-{rank}",
            "scenario": signal["scenario"],
            "strength": signal["strength"],
            "title": str(card.get("title") or topic["name"])[:200],
            "judgement": str(card.get("judgement") or ""),
            "reason": str(card.get("reason") or ""),
            "risk": str(card.get("risk") or ""),
            "next_watch": str(card.get("next") or ""),
            "tags": (card.get("tags") or [topic["name"], signal["scenario"]])[:4],
            "evidence_summary": (
                f"热榜 {news_count} 条 / 热度z {topic['heat_z']} / "
                f"价格z {signal['metrics']['price_z']} / {_stock_evidence_summary(signal.get('stock_candidates', []))}"
            ),
            "detail": detail,
            "boards": signal["all_boards"],
            "stock_candidates": signal.get("stock_candidates", []),
            "heat_z": topic["heat_z"],
            "price_z": signal["metrics"]["price_z"],
            "headline": headline,
        }
        cards.append(record)

    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM radar_predictions WHERE trade_date = :d"), {"d": trade_date})
        for record in cards:
            conn.execute(
                text(
                    """
                    INSERT INTO radar_predictions
                        (trade_date, rank, card_id, scenario, strength, title, judgement, reason,
                         risk, next_watch, tags, evidence_summary, detail, boards, stock_candidates,
                         heat_z, price_z, headline)
                    VALUES
                        (:trade_date, :rank, :card_id, :scenario, :strength, :title, :judgement, :reason,
                         :risk, :next_watch, CAST(:tags AS JSONB), :evidence_summary, CAST(:detail AS JSONB),
                         CAST(:boards AS JSONB), CAST(:stock_candidates AS JSONB), :heat_z, :price_z, :headline)
                    """
                ),
                {
                    **record,
                    "tags": json.dumps(record["tags"], ensure_ascii=False),
                    "detail": json.dumps(record["detail"], ensure_ascii=False),
                    "boards": json.dumps(record["boards"], ensure_ascii=False),
                    "stock_candidates": json.dumps(record["stock_candidates"], ensure_ascii=False),
                },
            )
    return cards
