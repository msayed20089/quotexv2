import random
from datetime import datetime
from config import UTC3_TZ

class TradingEngine:
    def __init__(self):
        from config import TRADING_PAIRS
        self.pairs = TRADING_PAIRS
        
    def analyze_and_decide(self):
        """تحليل عشوائي واتخاذ قرار التداول"""
        pair = random.choice(self.pairs)
        direction = random.choice(['BUY', 'SELL'])
        
        # وقت UTC+3 مع ثواني = 00
        utc3_time = datetime.now(UTC3_TZ)
        trade_time = utc3_time.replace(second=0, microsecond=0).strftime("%H:%M:%S")
        
        return {
            'pair': pair,
            'direction': direction,
            'trade_time': trade_time,
            'duration': 30
        }
