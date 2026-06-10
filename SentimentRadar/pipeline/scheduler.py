"""调度线程：每分钟比对后台配置的运行时间，命中即触发管线（当日同一时间只跑一次）。"""

from __future__ import annotations

import threading
import time
from datetime import datetime

from loguru import logger

from SentimentRadar import db
from SentimentRadar.pipeline import config_store, runner

_started = False
_triggered: set = set()  # {(date_str, "HH:MM")}


def _loop() -> None:
    while True:
        try:
            if db.available():
                config = config_store.get_config()
                if config.get("enabled"):
                    now = datetime.now()
                    mark = (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"))
                    if mark[1] in config.get("run_times", []) and mark not in _triggered:
                        _triggered.add(mark)
                        logger.info(f"调度触发雷达管线: {mark}")
                        threading.Thread(target=runner.run_pipeline, daemon=True).start()
                # 防止集合无限增长
                if len(_triggered) > 100:
                    _triggered.clear()
        except Exception as exc:
            logger.warning(f"雷达调度循环异常: {exc}")
        time.sleep(30)


def start() -> None:
    """启动调度线程（幂等）。"""
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, daemon=True, name="radar-scheduler").start()
    logger.info("雷达管线调度线程已启动")
