from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
import json

from ..core.models import get_db, Signal, PaperTrade
from ..core.config import settings
from ..agents.market_analyst import analyze_market
from ..agents.signal_generator import generate_signal
from ..agents.risk_manager import validate_and_size
from ..agents.portfolio_tracker import compute_portfolio_stats, calculate_trade_pnl
from pydantic import BaseModel

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def broadcast(self, data: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


class GenerateSignalRequest(BaseModel):
    symbol: str
    timeframe: str
    account_size: Optional[float] = None


class CloseTrade(BaseModel):
    exit_price: float
    notes: Optional[str] = None


class OpenTradeRequest(BaseModel):
    signal_id: int
    account_size: Optional[float] = None


@router.post("/signals/generate")
async def generate_trading_signal(req: GenerateSignalRequest, db: AsyncSession = Depends(get_db)):
    market_data = analyze_market(req.symbol.upper(), req.timeframe)
    if not market_data:
        raise HTTPException(status_code=422, detail=f"Could not fetch data for {req.symbol}")
    signal = generate_signal(market_data)
    if not signal:
        raise HTTPException(status_code=500, detail="Signal generation failed")
    signal = validate_and_size(signal, req.account_size)
    db_signal = Signal(
        symbol=req.symbol.upper(), timeframe=req.timeframe, signal_type=signal["signal"],
        price=signal.get("price", 0), stop_loss=signal.get("stop_loss"),
        take_profit=signal.get("take_profit"), confidence=signal.get("confidence"),
        reasoning=signal.get("reasoning"), indicators=json.dumps(signal.get("indicators", {})),
    )
    db.add(db_signal)
    await db.commit()
    await db.refresh(db_signal)
    signal["id"] = db_signal.id
    await manager.broadcast({"type": "new_signal", "data": signal})
    return signal


@router.get("/signals")
async def list_signals(symbol: Optional[str] = None, timeframe: Optional[str] = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(Signal).order_by(desc(Signal.created_at)).limit(limit)
    if symbol:
        query = query.where(Signal.symbol == symbol.upper())
    if timeframe:
        query = query.where(Signal.timeframe == timeframe)
    result = await db.execute(query)
    return [_signal_to_dict(s) for s in result.scalars().all()]


@router.get("/signals/scan")
async def scan_all(timeframe: str = "day", db: AsyncSession = Depends(get_db)):
    results = []
    for symbol in settings.symbols:
        market_data = analyze_market(symbol, timeframe)
        if not market_data:
            continue
        signal = generate_signal(market_data)
        if not signal:
            continue
        signal = validate_and_size(signal)
        db_signal = Signal(
            symbol=symbol, timeframe=timeframe, signal_type=signal["signal"],
            price=signal.get("price", 0), stop_loss=signal.get("stop_loss"),
            take_profit=signal.get("take_profit"), confidence=signal.get("confidence"),
            reasoning=signal.get("reasoning"), indicators=json.dumps(signal.get("indicators", {})),
        )
        db.add(db_signal)
        signal["id"] = None
        results.append(signal)
    await db.commit()
    await manager.broadcast({"type": "scan_complete", "data": {"count": len(results), "timeframe": timeframe}})
    return results


@router.post("/trades/open")
async def open_paper_trade(req: OpenTradeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Signal).where(Signal.id == req.signal_id))
    sig = result.scalar_one_or_none()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")
    indicators = json.loads(sig.indicators or "{}")
    atr = indicators.get("atr", sig.price * 0.01)
    account_size = req.account_size or settings.default_account_size
    max_risk = account_size * (settings.max_risk_per_trade_pct / 100)
    risk_per_share = abs(sig.price - sig.stop_loss) if sig.stop_loss else atr * 2
    quantity = max_risk / risk_per_share if risk_per_share else 1
    trade = PaperTrade(
        symbol=sig.symbol, timeframe=sig.timeframe, signal_type=sig.signal_type,
        entry_price=sig.price, stop_loss=sig.stop_loss, take_profit=sig.take_profit,
        quantity=round(quantity, 4), status="open",
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return _trade_to_dict(trade)


@router.post("/trades/{trade_id}/close")
async def close_paper_trade(trade_id: int, req: CloseTrade, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaperTrade).where(PaperTrade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.status != "open":
        raise HTTPException(status_code=400, detail="Trade already closed")
    pnl_data = calculate_trade_pnl(_trade_to_dict(trade), req.exit_price)
    trade.exit_price = req.exit_price
    trade.pnl = pnl_data["pnl"]
    trade.pnl_pct = pnl_data["pnl_pct"]
    trade.status = "closed"
    trade.closed_at = datetime.utcnow()
    if req.notes:
        trade.notes = req.notes
    await db.commit()
    await db.refresh(trade)
    await manager.broadcast({"type": "trade_closed", "data": _trade_to_dict(trade)})
    return _trade_to_dict(trade)


@router.get("/trades")
async def list_trades(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(PaperTrade).order_by(desc(PaperTrade.opened_at))
    if status:
        query = query.where(PaperTrade.status == status)
    result = await db.execute(query)
    return [_trade_to_dict(t) for t in result.scalars().all()]


@router.get("/portfolio/stats")
async def portfolio_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaperTrade))
    trades = [_trade_to_dict(t) for t in result.scalars().all()]
    return compute_portfolio_stats(trades)


@router.get("/watchlist")
async def get_watchlist():
    return {"symbols": settings.symbols}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _signal_to_dict(s: Signal) -> dict:
    return {
        "id": s.id, "symbol": s.symbol, "timeframe": s.timeframe, "signal": s.signal_type,
        "price": s.price, "stop_loss": s.stop_loss, "take_profit": s.take_profit,
        "confidence": s.confidence, "reasoning": s.reasoning,
        "created_at": s.created_at.isoformat() if s.created_at else None, "is_active": s.is_active,
    }


def _trade_to_dict(t: PaperTrade) -> dict:
    return {
        "id": t.id, "symbol": t.symbol, "timeframe": t.timeframe, "signal_type": t.signal_type,
        "entry_price": t.entry_price, "exit_price": t.exit_price, "stop_loss": t.stop_loss,
        "take_profit": t.take_profit, "quantity": t.quantity, "status": t.status,
        "pnl": t.pnl, "pnl_pct": t.pnl_pct,
        "opened_at": t.opened_at.isoformat() if t.opened_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None, "notes": t.notes,
    }
