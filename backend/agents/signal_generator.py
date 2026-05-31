import json
import anthropic
from typing import Optional, Dict
from ..core.config import settings

TIMEFRAME_CONTEXT = {
    "15min": "scalping/intraday - short positions, tight stops, quick moves",
    "day": "day trading - enter and exit within the same trading day",
    "swing": "swing trading - hold for 2-10 days, catching medium-term trends",
}

SYSTEM_PROMPT = """You are an expert technical analyst and trading signal generator.
Analyze the provided technical indicators and generate a precise trading signal.

Always respond with valid JSON only, no extra text. Format:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0-1.0,
  "stop_loss": <price or null>,
  "take_profit": <price or null>,
  "reasoning": "<concise 2-3 sentence explanation>",
  "key_factors": ["factor1", "factor2", "factor3"]
}

Rules:
- Only signal BUY or SELL when confidence > 0.60
- Stop loss must respect ATR (typically 1.5-2x ATR from entry)
- Take profit should give at least 1.5:1 reward/risk ratio
- Be conservative - capital preservation is paramount
"""


def generate_signal(market_data: Dict) -> Optional[Dict]:
    if not settings.anthropic_api_key:
        return _rule_based_signal(market_data)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    ind = market_data["indicators"]
    timeframe = market_data["timeframe"]
    symbol = market_data["symbol"]

    user_message = f"""
Symbol: {symbol}
Timeframe: {timeframe} ({TIMEFRAME_CONTEXT.get(timeframe, '')})
Current Price: {ind.get('price')}

Technical Indicators:
- EMA9: {ind.get('ema9')} | EMA21: {ind.get('ema21')} | EMA50: {ind.get('ema50')}
- RSI(14): {ind.get('rsi')}
- MACD: {ind.get('macd')} | Signal: {ind.get('macd_signal')} | Histogram: {ind.get('macd_hist')}
- BB Upper: {ind.get('bb_upper')} | BB Mid: {ind.get('bb_mid')} | BB Lower: {ind.get('bb_lower')}
- ATR(14): {ind.get('atr')}
- OBV Trend: {ind.get('obv_trend')}
- 5-bar High: {ind.get('high_5')} | 5-bar Low: {ind.get('low_5')}
- Previous Close: {ind.get('prev_close')}

Generate a trading signal.
"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        result = json.loads(response.content[0].text)
        result["symbol"] = symbol
        result["timeframe"] = timeframe
        result["price"] = ind.get("price")
        result["indicators"] = ind
        return result
    except Exception:
        return _rule_based_signal(market_data)


def _rule_based_signal(market_data: Dict) -> Dict:
    ind = market_data["indicators"]
    price = ind.get("price", 0)
    rsi = ind.get("rsi")
    ema9 = ind.get("ema9")
    ema21 = ind.get("ema21")
    macd = ind.get("macd")
    macd_signal = ind.get("macd_signal")
    atr = ind.get("atr", price * 0.01)

    bullish_signals = 0
    bearish_signals = 0

    if rsi and rsi < 40: bullish_signals += 1
    if rsi and rsi > 65: bearish_signals += 1
    if ema9 and ema21 and ema9 > ema21: bullish_signals += 1
    elif ema9 and ema21: bearish_signals += 1
    if macd and macd_signal and macd > macd_signal: bullish_signals += 1
    elif macd and macd_signal: bearish_signals += 1
    if price and ind.get("bb_lower") and price < ind["bb_lower"]: bullish_signals += 1
    if price and ind.get("bb_upper") and price > ind["bb_upper"]: bearish_signals += 1

    total = bullish_signals + bearish_signals
    if total == 0:
        signal, confidence = "HOLD", 0.5
    elif bullish_signals > bearish_signals:
        confidence = bullish_signals / (total + 2)
        signal = "BUY" if confidence > 0.55 else "HOLD"
    else:
        confidence = bearish_signals / (total + 2)
        signal = "SELL" if confidence > 0.55 else "HOLD"

    sl = round(price - 2 * atr, 4) if signal == "BUY" else (round(price + 2 * atr, 4) if signal == "SELL" else None)
    tp = round(price + 3 * atr, 4) if signal == "BUY" else (round(price - 3 * atr, 4) if signal == "SELL" else None)

    return {
        "signal": signal, "confidence": round(confidence, 2), "stop_loss": sl, "take_profit": tp,
        "reasoning": f"Rule-based: {bullish_signals} bullish vs {bearish_signals} bearish signals.",
        "key_factors": ["RSI", "EMA crossover", "MACD", "Bollinger Bands"],
        "symbol": market_data["symbol"], "timeframe": market_data["timeframe"], "price": price, "indicators": ind,
    }
