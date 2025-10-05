import logging
from datetime import datetime
from config import UTC3_TZ

class MonitoringSystem:
    """نظام مراقبة مبسط لأداء البوت"""
    
    def __init__(self, trading_engine=None, telegram_bot=None):
        self.trading_engine = trading_engine
        self.telegram_bot = telegram_bot
        
    def log_error(self, error_type, error_message):
        """تسجيل الأخطاء"""
        logging.warning(f"⚠️ خطأ مسجل: {error_type} - {error_message}")
    
    def log_success(self):
        """تسجيل نجاح الصفقة"""
        logging.info("✅ تم تسجيل نجاح الصفقة")
