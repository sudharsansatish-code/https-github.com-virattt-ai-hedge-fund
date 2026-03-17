"""Dashboard API endpoints for performance analytics.

Provides:
  - Recent runs list with returns/Sharpe
  - Agent accuracy leaderboard
  - Daily portfolio snapshots for P&L charting
  - Trade log with transaction costs
  - Strategy config listing
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard")


def _get_perf_db():
    """Lazily import performance DB to avoid import errors if not configured."""
    try:
        from src.utils.performance_db import perf_db
        return perf_db
    except Exception:
        return None


@router.get("/runs")
def list_runs(limit: int = Query(default=20, ge=1, le=100)):
    """List recent backtest runs with key metrics."""
    db = _get_perf_db()
    if not db:
        return {"runs": [], "error": "Performance DB not available"}

    runs = db.get_recent_runs(limit=limit)
    return {"runs": runs}


@router.get("/runs/{run_id}")
def get_run_detail(run_id: str):
    """Get detailed info about a specific run."""
    db = _get_perf_db()
    if not db:
        return {"error": "Performance DB not available"}

    summary = db.get_run_summary(run_id)
    if not summary:
        return {"error": f"Run '{run_id}' not found"}

    return {"run": summary}


@router.get("/runs/{run_id}/snapshots")
def get_run_snapshots(run_id: str):
    """Get daily portfolio snapshots for a run (for P&L charting)."""
    db = _get_perf_db()
    if not db:
        return {"snapshots": [], "error": "Performance DB not available"}

    try:
        snapshots = db.query_snapshots(run_id)
        return {"run_id": run_id, "snapshots": snapshots}
    except Exception as e:
        logger.error(f"Failed to fetch snapshots: {e}")
        return {"snapshots": [], "error": str(e)}


@router.get("/runs/{run_id}/trades")
def get_run_trades(run_id: str):
    """Get trade log for a specific run."""
    db = _get_perf_db()
    if not db:
        return {"trades": [], "error": "Performance DB not available"}

    try:
        trades = db.query_trades(run_id)
        return {"run_id": run_id, "trades": trades}
    except Exception as e:
        logger.error(f"Failed to fetch trades: {e}")
        return {"trades": [], "error": str(e)}


@router.get("/agents/leaderboard")
def agent_leaderboard(limit: int = Query(default=50, ge=1, le=200)):
    """Get agent signal accuracy leaderboard."""
    db = _get_perf_db()
    if not db:
        return {"agents": [], "error": "Performance DB not available"}

    try:
        agents = db.query_agent_leaderboard(limit=limit)

        # Round floats
        for a in agents:
            if a.get("avg_confidence") is not None:
                a["avg_confidence"] = round(a["avg_confidence"], 1)

        return {"agents": agents}
    except Exception as e:
        logger.error(f"Failed to fetch agent leaderboard: {e}")
        return {"agents": [], "error": str(e)}


@router.get("/strategies")
def list_strategies():
    """List available strategy config files."""
    try:
        from src.config.strategy import list_strategies as _list_strategies, load_strategy
        names = _list_strategies()
        strategies = []
        for name in names:
            try:
                cfg = load_strategy(name)
                strategies.append({
                    "name": cfg.name,
                    "description": cfg.description,
                    "tickers": cfg.tickers,
                    "model_name": cfg.model_name,
                    "model_provider": cfg.model_provider,
                    "initial_cash": cfg.initial_cash,
                })
            except Exception:
                strategies.append({"name": name, "error": "Failed to load"})
        return {"strategies": strategies}
    except Exception as e:
        return {"strategies": [], "error": str(e)}


@router.get("/cost-summary")
def cost_summary():
    """Get LLM and transaction cost tracking summary."""
    result = {}

    # LLM costs
    try:
        from src.utils.costs import cost_tracker
        result["llm_costs"] = cost_tracker.get_summary()
    except Exception:
        result["llm_costs"] = {"error": "Cost tracker not available"}

    return result
