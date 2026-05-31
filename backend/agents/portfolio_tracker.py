from typing import List, Dict


def compute_portfolio_stats(trades: List[Dict]) -> Dict:
    if not trades:
        return {"total_trades": 0, "open_trades": 0, "closed_trades": 0, "win_rate": 0,
                "total_pnl": 0, "avg_pnl": 0, "best_trade": 0, "worst_trade": 0, "profit_factor": 0}
    closed = [t for t in trades if t.get("status") == "closed"]
    open_trades = [t for t in trades if t.get("status") == "open"]
    winners = [t for t in closed if (t.get("pnl") or 0) > 0]
    losers = [t for t in closed if (t.get("pnl") or 0) < 0]
    total_pnl = sum(t.get("pnl") or 0 for t in closed)
    gross_profit = sum(t.get("pnl") or 0 for t in winners)
    gross_loss = abs(sum(t.get("pnl") or 0 for t in losers))
    pnl_values = [t.get("pnl") or 0 for t in closed]
    return {
        "total_trades": len(trades), "open_trades": len(open_trades), "closed_trades": len(closed),
        "win_rate": round(len(winners) / len(closed) * 100, 1) if closed else 0,
        "total_pnl": round(total_pnl, 2), "avg_pnl": round(total_pnl / len(closed), 2) if closed else 0,
        "best_trade": round(max(pnl_values), 2) if pnl_values else 0,
        "worst_trade": round(min(pnl_values), 2) if pnl_values else 0,
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0,
        "winners": len(winners), "losers": len(losers),
    }


def calculate_trade_pnl(trade: Dict, exit_price: float) -> Dict:
    entry = trade.get("entry_price", 0)
    qty = trade.get("quantity", 0)
    direction = trade.get("signal_type", "BUY")
    pnl = (exit_price - entry) * qty if direction == "BUY" else (entry - exit_price) * qty
    pnl_pct = (pnl / (entry * qty)) * 100 if entry and qty else 0
    return {"pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2), "exit_price": exit_price}
