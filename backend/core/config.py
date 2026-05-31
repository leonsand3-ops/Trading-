from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./trading.db"
    symbols: List[str] = ["AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD", "SPY", "QQQ"]
    max_risk_per_trade_pct: float = 1.0
    default_account_size: float = 10000.0

    class Config:
        env_file = ".env"


settings = Settings()
