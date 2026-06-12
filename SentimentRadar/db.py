"""雷达模块共享的 PostgreSQL 连接与建表管理。

连接串通过 RADAR_DB_URL 环境变量配置，默认指向宿主机映射端口（本地开发），
容器内由 compose 注入指向 db 服务。数据库不可用时由调用方降级处理。
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DB_URL = "postgresql+psycopg://bettafish:bettafish@127.0.0.1:5444/bettafish"

# 全部幂等：CREATE TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS
_SCHEMAS = [
    # 注册用户
    """
    CREATE TABLE IF NOT EXISTS radar_users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        username VARCHAR(50) NOT NULL DEFAULT '',
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
    """,
    "ALTER TABLE radar_users ADD COLUMN IF NOT EXISTS username VARCHAR(50) NOT NULL DEFAULT ''",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_radar_users_username "
    "ON radar_users (LOWER(username)) WHERE username <> ''",
    # 管线配置（后台可改的键值对）
    """
    CREATE TABLE IF NOT EXISTS radar_config (
        key TEXT PRIMARY KEY,
        value JSONB NOT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    # 每日热榜快照
    """
    CREATE TABLE IF NOT EXISTS radar_news (
        id SERIAL PRIMARY KEY,
        source VARCHAR(64) NOT NULL,
        source_name VARCHAR(64) NOT NULL,
        title TEXT NOT NULL,
        url TEXT,
        rank INTEGER NOT NULL DEFAULT 0,
        crawl_date DATE NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (source, title, crawl_date)
    )
    """,
    # 话题与热度
    """
    CREATE TABLE IF NOT EXISTS radar_topics (
        id SERIAL PRIMARY KEY,
        trade_date DATE NOT NULL,
        name VARCHAR(100) NOT NULL,
        keywords JSONB NOT NULL DEFAULT '[]',
        news_refs JSONB NOT NULL DEFAULT '[]',
        heat_score DOUBLE PRECISION NOT NULL DEFAULT 0,
        heat_z DOUBLE PRECISION,
        boards JSONB NOT NULL DEFAULT '[]',
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (trade_date, name)
    )
    """,
    # 板块行情缓存
    """
    CREATE TABLE IF NOT EXISTS radar_board_quotes (
        board_code VARCHAR(32) NOT NULL,
        board_name VARCHAR(64) NOT NULL,
        board_type VARCHAR(16) NOT NULL,
        trade_date DATE NOT NULL,
        close DOUBLE PRECISION,
        pct_chg DOUBLE PRECISION,
        volume DOUBLE PRECISION,
        PRIMARY KEY (board_code, trade_date)
    )
    """,
    # 预判卡（管线最终输出）
    """
    CREATE TABLE IF NOT EXISTS radar_predictions (
        id SERIAL PRIMARY KEY,
        trade_date DATE NOT NULL,
        rank INTEGER NOT NULL,
        card_id VARCHAR(64) NOT NULL,
        scenario VARCHAR(32) NOT NULL,
        strength VARCHAR(16) NOT NULL,
        title VARCHAR(200) NOT NULL,
        judgement TEXT NOT NULL DEFAULT '',
        reason TEXT NOT NULL DEFAULT '',
        risk TEXT NOT NULL DEFAULT '',
        next_watch TEXT NOT NULL DEFAULT '',
        tags JSONB NOT NULL DEFAULT '[]',
        evidence_summary VARCHAR(200) NOT NULL DEFAULT '',
        detail JSONB NOT NULL DEFAULT '{}',
        boards JSONB NOT NULL DEFAULT '[]',
        stock_candidates JSONB NOT NULL DEFAULT '[]',
        heat_z DOUBLE PRECISION,
        price_z DOUBLE PRECISION,
        headline TEXT NOT NULL DEFAULT '',
        return_1d DOUBLE PRECISION,
        return_3d DOUBLE PRECISION,
        return_5d DOUBLE PRECISION,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (trade_date, rank)
    )
    """,
    # 管线运行记录
    """
    CREATE TABLE IF NOT EXISTS radar_pipeline_runs (
        id SERIAL PRIMARY KEY,
        started_at TIMESTAMP NOT NULL DEFAULT NOW(),
        finished_at TIMESTAMP,
        status VARCHAR(16) NOT NULL DEFAULT 'running',
        stage VARCHAR(32) NOT NULL DEFAULT '',
        message TEXT NOT NULL DEFAULT '',
        stats JSONB NOT NULL DEFAULT '{}'
    )
    """,
    # 用户关注（股票/主题/板块）
    """
    CREATE TABLE IF NOT EXISTS radar_watchlist (
        id SERIAL PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        item_type VARCHAR(16) NOT NULL,
        name VARCHAR(64) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (user_email, item_type, name)
    )
    """,
    # 在线购买订单（易支付回调后开通订阅）
    """
    CREATE TABLE IF NOT EXISTS radar_orders (
        id SERIAL PRIMARY KEY,
        out_trade_no VARCHAR(64) NOT NULL UNIQUE,
        user_email VARCHAR(255) NOT NULL,
        user_name VARCHAR(100) NOT NULL DEFAULT '',
        plan_id VARCHAR(32) NOT NULL,
        plan_name VARCHAR(64) NOT NULL,
        period VARCHAR(16) NOT NULL DEFAULT 'month',
        amount NUMERIC(10, 2) NOT NULL,
        subject VARCHAR(200) NOT NULL,
        pay_type VARCHAR(32) NOT NULL DEFAULT 'alipay',
        status VARCHAR(16) NOT NULL DEFAULT 'pending',
        provider VARCHAR(32) NOT NULL DEFAULT 'epay',
        provider_trade_no VARCHAR(128) NOT NULL DEFAULT '',
        raw_notify JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        paid_at TIMESTAMP
    )
    """,
    # 个股行情增强快照
    """
    CREATE TABLE IF NOT EXISTS radar_stock_quote_metrics (
        code VARCHAR(32) NOT NULL,
        trade_date VARCHAR(16) NOT NULL,
        close DOUBLE PRECISION,
        pct_chg DOUBLE PRECISION,
        turnover_rate DOUBLE PRECISION,
        volume_ratio DOUBLE PRECISION,
        amount DOUBLE PRECISION,
        pe DOUBLE PRECISION,
        pb DOUBLE PRECISION,
        total_mv DOUBLE PRECISION,
        circ_mv DOUBLE PRECISION,
        source VARCHAR(32) NOT NULL DEFAULT '',
        raw JSONB NOT NULL DEFAULT '{}',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (code, trade_date)
    )
    """,
    # 个股基础资料与国资属性推断
    """
    CREATE TABLE IF NOT EXISTS radar_stock_profiles (
        code VARCHAR(32) PRIMARY KEY,
        name VARCHAR(64) NOT NULL DEFAULT '',
        industry VARCHAR(100) NOT NULL DEFAULT '',
        area VARCHAR(64) NOT NULL DEFAULT '',
        market VARCHAR(64) NOT NULL DEFAULT '',
        list_date VARCHAR(16) NOT NULL DEFAULT '',
        main_business TEXT NOT NULL DEFAULT '',
        top_holder VARCHAR(200) NOT NULL DEFAULT '',
        controller VARCHAR(200) NOT NULL DEFAULT '',
        is_state_owned BOOLEAN NOT NULL DEFAULT FALSE,
        soe_tag VARCHAR(32) NOT NULL DEFAULT '',
        source VARCHAR(32) NOT NULL DEFAULT '',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    # 财务核心指标快照
    """
    CREATE TABLE IF NOT EXISTS radar_stock_financials (
        code VARCHAR(32) NOT NULL,
        period VARCHAR(16) NOT NULL,
        ann_date VARCHAR(16) NOT NULL DEFAULT '',
        revenue_yoy DOUBLE PRECISION,
        profit_yoy DOUBLE PRECISION,
        gross_margin DOUBLE PRECISION,
        roe DOUBLE PRECISION,
        debt_to_assets DOUBLE PRECISION,
        ocf_to_revenue DOUBLE PRECISION,
        rd_exp DOUBLE PRECISION,
        source VARCHAR(32) NOT NULL DEFAULT '',
        raw JSONB NOT NULL DEFAULT '{}',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (code, period)
    )
    """,
    # 最新公告索引（标题/类型/链接，不存全文）
    """
    CREATE TABLE IF NOT EXISTS radar_stock_announcements (
        code VARCHAR(32) NOT NULL,
        ann_date VARCHAR(16) NOT NULL,
        title TEXT NOT NULL,
        type VARCHAR(32) NOT NULL DEFAULT '其他公告',
        url TEXT NOT NULL DEFAULT '',
        source VARCHAR(32) NOT NULL DEFAULT '',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (code, ann_date, title)
    )
    """,
    # 个股资金流
    """
    CREATE TABLE IF NOT EXISTS radar_stock_moneyflow (
        code VARCHAR(32) NOT NULL,
        trade_date VARCHAR(16) NOT NULL,
        net_mf_amount DOUBLE PRECISION,
        net_mf_ratio DOUBLE PRECISION,
        source VARCHAR(32) NOT NULL DEFAULT '',
        raw JSONB NOT NULL DEFAULT '{}',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (code, trade_date)
    )
    """,
    # 板块资金流（优先真实板块资金流，失败时由候选股资金流聚合）
    """
    CREATE TABLE IF NOT EXISTS radar_board_moneyflow (
        board_code VARCHAR(32) NOT NULL,
        trade_date VARCHAR(16) NOT NULL,
        board_name VARCHAR(64) NOT NULL DEFAULT '',
        net_mf_amount DOUBLE PRECISION,
        net_mf_ratio DOUBLE PRECISION,
        source VARCHAR(32) NOT NULL DEFAULT '',
        raw JSONB NOT NULL DEFAULT '{}',
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (board_code, trade_date)
    )
    """,
    # 话题补充价格 z 分（象限散点图使用）
    "ALTER TABLE radar_topics ADD COLUMN IF NOT EXISTS price_z DOUBLE PRECISION",
    # 预判卡补充个股观察池
    "ALTER TABLE radar_predictions ADD COLUMN IF NOT EXISTS stock_candidates JSONB NOT NULL DEFAULT '[]'",
]

_engine: Optional[Engine] = None
_available: Optional[bool] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = os.getenv("RADAR_DB_URL", DEFAULT_DB_URL)
        _engine = create_engine(url, future=True, pool_pre_ping=True)
    return _engine


def available() -> bool:
    """惰性探测数据库可用性并初始化全部表结构，进程内只探测一次。"""
    global _available
    if _available is None:
        try:
            with get_engine().begin() as conn:
                for schema in _SCHEMAS:
                    conn.execute(text(schema))
            _available = True
            logger.info("雷达数据库已连接（表结构就绪）")
        except Exception as exc:
            _available = False
            logger.warning(f"雷达数据库不可用，相关功能将降级: {exc}")
    return _available
