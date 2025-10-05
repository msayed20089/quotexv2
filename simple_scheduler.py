import time
import logging
from datetime import datetime, timedelta
from config import UTC3_TZ

class SimpleTradingScheduler:
    def __init__(self):
        from qx_broker import QXBrokerManager
        from telegram_bot import TelegramBot
        from trading_engine import TradingEngine
        
        self.qx_manager = QXBrokerManager()
        self.telegram_bot = TelegramBot()
        self.trading_engine = TradingEngine()
        
        self.stats = {
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'net_profit': 0,
            'session_start': datetime.now(UTC3_TZ),
            'last_trade_time': None
        }
        
        self.next_trade_time = None
        self.trade_in_progress = False
        
    def get_utc3_time(self):
        """الحصول على وقت UTC+3"""
        return datetime.now(UTC3_TZ)
    
    def calculate_next_trade_time(self):
        """حساب وقت الصفقة التالية"""
        now = self.get_utc3_time()
        # الصفقات كل 3 دقائق (0, 3, 6, 9, ...)
        next_minute = ((now.minute // 3) + 1) * 3
        if next_minute >= 60:
            next_minute = 0
            next_hour = now.hour + 1
        else:
            next_hour = now.hour
            
        next_trade = now.replace(hour=next_hour % 24, minute=next_minute, second=0, microsecond=0)
        if next_trade <= now:
            next_trade += timedelta(hours=1)
            
        return next_trade
    
    def start_24h_trading(self):
        """بدء التداول 24 ساعة"""
        logging.info("🚀 بدء التداول 24 ساعة بتوقيت UTC+3...")
        
        current_time = self.get_utc3_time().strftime("%H:%M:%S")
        self.telegram_bot.send_message(
            f"🎯 <b>بدء تشغيل البوت بنجاح!</b>\n\n"
            f"📊 البوت يعمل الآن 24 ساعة\n"
            f"🔄 صفقة كل 3 دقائق\n"
            f"⏰ الوقت الحالي: {current_time} (UTC+3)\n\n"
            f"🚀 <i>استعد لفرص ربح مستمرة!</i>"
        )
        
        self.next_trade_time = self.calculate_next_trade_time()
        logging.info(f"⏰ أول صفقة: {self.next_trade_time.strftime('%H:%M:%S')} (UTC+3)")
    
    def execute_trade_cycle(self):
        """تنفيذ دورة الصفقة الكاملة"""
        if self.trade_in_progress:
            return
            
        try:
            self.trade_in_progress = True
            
            # تحليل واتخاذ قرار
            trade_data = self.trading_engine.analyze_and_decide()
            trade_time = self.get_utc3_time().strftime("%H:%M:%S")
            
            # إرسال إشارة الصفقة
            self.telegram_bot.send_trade_signal(
                trade_data['pair'],
                trade_data['direction'],
                trade_time
            )
            
            logging.info(f"📤 إشارة صفقة: {trade_data['pair']} - {trade_data['direction']} - {trade_time} (UTC+3)")
            
            # تنفيذ الصفقة بعد 5 ثواني (بدل 60)
            time.sleep(5)
            
            # تنفيذ الصفقة في المنصة
            success = self.qx_manager.execute_trade(
                trade_data['pair'],
                trade_data['direction'],
                trade_data['duration']
            )
            
            if success:
                logging.info(f"✅ تم تنفيذ صفقة: {trade_data['pair']} - {trade_data['direction']}")
                
                # انتظار النتيجة
                time.sleep(35)
                
                # الحصول على النتيجة
                result = self.qx_manager.get_trade_result()
                
                # تحديث الإحصائيات
                self.stats['total_trades'] += 1
                if result == 'WIN':
                    self.stats['win_trades'] += 1
                else:
                    self.stats['loss_trades'] += 1
                self.stats['net_profit'] = self.stats['win_trades'] - self.stats['loss_trades']
                
                # إرسال النتيجة
                self.telegram_bot.send_trade_result(
                    trade_data['pair'],
                    result,
                    self.stats
                )
                
                logging.info(f"🎯 نتيجة صفقة: {trade_data['pair']} - {result}")
                
            else:
                logging.error(f"❌ فشل تنفيذ الصفقة: {trade_data['pair']}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في دورة الصفقة: {e}")
        finally:
            self.trade_in_progress = False
            self.stats['last_trade_time'] = self.get_utc3_time()
    
    def keep_alive(self):
        """الحفاظ على نشاط النظام"""
        try:
            self.qx_manager.keep_alive()
            
            # إرسال تقرير صحة كل 30 دقيقة
            current_time = self.get_utc3_time()
            if self.stats['last_trade_time']:
                time_since_last_trade = (current_time - self.stats['last_trade_time']).total_seconds()
                if time_since_last_trade > 1800:  # 30 دقيقة
                    self.send_health_report()
                    self.stats['last_trade_time'] = current_time
                    
        except Exception as e:
            logging.error(f"❌ خطأ في الحفاظ على النشاط: {e}")
    
    def send_health_report(self):
        """إرسال تقرير صحة النظام"""
        try:
            current_time = self.get_utc3_time().strftime("%H:%M:%S")
            session_duration = self.get_utc3_time() - self.stats['session_start']
            hours, remainder = divmod(session_duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            health_report = f"""
🩺 <b>تقرير صحة النظام</b>

⏰ وقت التشغيل: {int(hours)}h {int(minutes)}m
📊 إجمالي الصفقات: {self.stats['total_trades']}
✅ الصفقات الرابحة: {self.stats['win_trades']}
❌ الصفقات الخاسرة: {self.stats['loss_trades']}
💰 صافي الربح: {self.stats['net_profit']}

🕒 آخر تحديث: {current_time} (UTC+3)

🎯 <i>النظام يعمل بشكل طبيعي</i>
"""
            self.telegram_bot.send_message(health_report)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال تقرير الصحة: {e}")
    
    def run(self):
        """تشغيل الجدولة المبسطة"""
        try:
            self.start_24h_trading()
            
            logging.info("✅ بدء تشغيل الجدولة المبسطة...")
            
            # الحلقة الرئيسية
            while True:
                current_time = self.get_utc3_time()
                
                # التحقق إذا حان وقت الصفقة
                if self.next_trade_time and current_time >= self.next_trade_time and not self.trade_in_progress:
                    logging.info(f"⏰ بدء صفقة جديدة: {current_time.strftime('%H:%M:%S')}")
                    self.execute_trade_cycle()
                    self.next_trade_time = self.calculate_next_trade_time()
                    logging.info(f"⏰ الصفقة القادمة: {self.next_trade_time.strftime('%H:%M:%S')}")
                
                # الحفاظ على النشاط
                self.keep_alive()
                
                # انتظار 10 ثواني قبل التكرار
                time.sleep(10)
                    
        except Exception as e:
            logging.error(f"❌ خطأ فادح في التشغيل: {e}")
            logging.info("🔄 إعادة التشغيل بعد 30 ثانية...")
            time.sleep(30)
            self.run()
