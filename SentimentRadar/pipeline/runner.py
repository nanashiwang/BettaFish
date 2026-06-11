"""管线编排：六阶段执行 + 运行记录 + 收益回填。"""

from __future__ import annotations

import json
import threading
from datetime import date
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import text

from SentimentRadar import db
from SentimentRadar.pipeline import card_generator, config_store, news_collector, signals, topic_extractor
from SentimentRadar.pipeline.quotes import QuoteService

_run_lock = threading.Lock()


def is_running() -> bool:
    with db.get_engine().begin() as conn:
        row = conn.execute(
            text("SELECT COUNT(*) FROM radar_pipeline_runs WHERE status = 'running' AND started_at > NOW() - INTERVAL '30 minutes'")
        ).scalar_one()
    return row > 0


def _start_run() -> int:
    with db.get_engine().begin() as conn:
        return conn.execute(
            text("INSERT INTO radar_pipeline_runs (status, stage) VALUES ('running', 'collect') RETURNING id")
        ).scalar_one()


def _update_run(run_id: int, stage: str = None, status: str = None, message: str = None, stats: Dict = None) -> None:
    sets, params = [], {"id": run_id}
    if stage is not None:
        sets.append("stage = :stage")
        params["stage"] = stage
    if status is not None:
        sets.append("status = :status")
        params["status"] = status
        if status in ("success", "failed"):
            sets.append("finished_at = NOW()")
    if message is not None:
        sets.append("message = :message")
        params["message"] = message[:2000]
    if stats is not None:
        sets.append("stats = CAST(:stats AS JSONB)")
        params["stats"] = json.dumps(stats, ensure_ascii=False)
    if sets:
        with db.get_engine().begin() as conn:
            conn.execute(text(f"UPDATE radar_pipeline_runs SET {', '.join(sets)} WHERE id = :id"), params)


def run_pipeline(trade_date: Optional[date] = None) -> Dict[str, Any]:
    """执行完整管线；返回 {run_id, status, message, stats}。"""
    if not db.available():
        return {"run_id": None, "status": "failed", "message": "数据库不可用"}
    if not _run_lock.acquire(blocking=False):
        return {"run_id": None, "status": "rejected", "message": "管线已在运行中"}
    try:
        trade_date = trade_date or date.today()
        config = config_store.get_config()
        model = config["llm_model"]
        run_id = _start_run()
        stats: Dict[str, Any] = {}
        logger.info(f"雷达管线启动 run={run_id} date={trade_date} model={model}")
        try:
            # 1. 热榜采集
            news = news_collector.collect_news(trade_date)
            stats["news"] = len(news)
            if not news:
                raise RuntimeError("热榜采集结果为空（newsnow API 可能不可用）")
            _update_run(run_id, stage="topics", stats=stats)

            # 2. 话题提取
            topics = topic_extractor.extract_topics(news, model)
            stats["topics"] = len(topics)
            if not topics:
                raise RuntimeError("未提取到 A 股相关话题")
            _update_run(run_id, stage="boards", stats=stats)

            # 3. 板块清单 + 映射
            quote_service = QuoteService(config.get("tushare_token", ""))
            try:
                boards = quote_service.list_boards()
            except Exception as exc:
                hint = (
                    "（未配置 tushare token；akshare 兜底在当前网络不可达。"
                    "请在后台「平台设置 → 雷达管线」填写 tushare token 后重试）"
                    if not config.get("tushare_token")
                    else "（同花顺、申万行业降级源与 akshare 均失败，请检查 token 权限、积分与网络）"
                )
                raise RuntimeError(f"获取板块清单失败{hint}: {exc}")
            stats["board_universe"] = len(boards)
            stats["quote_provider"] = quote_service.used_provider
            topics = topic_extractor.map_boards(topics, boards, model)
            mapped = [t for t in topics if t.get("boards")]
            stats["topics_mapped"] = len(mapped)
            if not mapped:
                raise RuntimeError("没有话题能映射到板块")
            _update_run(run_id, stage="quotes", stats=stats)

            # 4. 板块行情（每板块近 90 自然日日线，缓存落库）
            quotes_by_board: Dict[str, list] = {}
            for topic in mapped:
                for board in topic["boards"]:
                    if board["code"] in quotes_by_board:
                        continue
                    try:
                        history = quote_service.board_history(board)
                        quotes_by_board[board["code"]] = history
                        signals.save_board_quotes(board, history)
                    except Exception as exc:
                        logger.warning(f"板块行情拉取失败 {board['name']}: {exc}")
            stats["boards_quoted"] = len(quotes_by_board)
            if not quotes_by_board:
                raise RuntimeError(
                    "全部板块行情拉取失败：请在后台检查 tushare token 权限，或确认 akshare 网络可用"
                )
            _update_run(run_id, stage="signals", stats=stats)

            # 5. 热度与背离信号（build_signals 会把 price_z 回写到话题，再落库供散点图）
            signals.compute_heat(mapped, news, trade_date)
            signal_list = signals.build_signals(mapped, quotes_by_board)
            stock_candidate_count = 0
            for signal in signal_list[:6]:
                try:
                    candidates = quote_service.stock_candidates(
                        signal["board"], signal.get("scenario", ""), limit=8
                    )
                    signal["stock_candidates"] = candidates
                    stock_candidate_count += len(candidates)
                except Exception as exc:
                    logger.warning(f"个股观察池筛选失败 {signal['board']['name']}: {exc}")
                    signal["stock_candidates"] = []
            stats["stock_candidates"] = stock_candidate_count
            topic_extractor.save_topics(trade_date, mapped)
            stats["signals"] = len(signal_list)
            if not signal_list:
                raise RuntimeError("今日无显著舆情-价格背离信号（属正常情况，可明日再看）")
            _update_run(run_id, stage="cards", stats=stats)

            # 6. 预判卡生成 + 历史收益回填
            cards = card_generator.generate_cards(trade_date, signal_list, news, model)
            stats["cards"] = len(cards)
            stats["returns_backfilled"] = signals.backfill_returns(trade_date)

            _update_run(run_id, stage="done", status="success", message="管线执行成功", stats=stats)
            logger.info(f"雷达管线完成 run={run_id} stats={stats}")
            return {"run_id": run_id, "status": "success", "message": "管线执行成功", "stats": stats}
        except Exception as exc:
            logger.error(f"雷达管线失败 run={run_id}: {exc}")
            _update_run(run_id, status="failed", message=str(exc), stats=stats)
            return {"run_id": run_id, "status": "failed", "message": str(exc), "stats": stats}
    finally:
        _run_lock.release()


def list_runs(limit: int = 20) -> list:
    with db.get_engine().begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, started_at, finished_at, status, stage, message, stats "
                "FROM radar_pipeline_runs ORDER BY id DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()
    runs = []
    for row in rows:
        runs.append({
            "id": row.id,
            "started_at": row.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": row.finished_at.strftime("%Y-%m-%d %H:%M:%S") if row.finished_at else None,
            "status": row.status,
            "stage": row.stage,
            "message": row.message,
            "stats": row.stats or {},
        })
    return runs


if __name__ == "__main__":
    print(run_pipeline())
