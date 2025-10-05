import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
from config import UTC3_TZ

class TradingScheduler:
    def __init__(self):
        from qx_broker import QXBrokerManager
        from telegram_bot import TelegramBot
        from trading_engine import TradingEngine
        from monitoring_system import MonitoringSystem
        
        self.qx_manager = QXBrokerManager()
        self.telegram_bot = TelegramBot()
        self.trading_engine = TradingEngine()
        self.monitoring_system = MonitoringSystem(self.trading_engine, self.telegram_bot)
        
        self.stats = {
            'total_trades': 0,
            'win_trades': 0,
            'loss_trades': 0,
            'net_profit': 0,
            'session_start': datetime.now(UTC3_TZ),
            'last_trade_time': None
        }
        
        self.pending_trades = {}
        self.regular_schedule_started = False
        
    def get_utc3_time(self):
        """الحصول على وقت UTC+3"""
        return datetime.now(UTC3_TZ)
    
    def keep_browser_alive(self):
        """الحفاظ على نشاط المتصفح بين الصفقات"""
        try:
            self.qx_manager.keep_alive()
            logging.debug("✅ تم الحفاظ على نشاط المتصفح")
        except Exception as e:
            logging.error(f"❌ خطأ في الحفاظ على نشاط المتصفح: {e}")
    
    def start_24h_trading(self):
        """بدء التداول 24 ساعة بتوقيت UTC+3"""
        logging.info("🚀 بدء التداول 24 ساعة بتوقيت UTC+3...")
        
        current_time = self.get_utc3_time().strftime("%H:%M:%S")
        self.telegram_bot.send_message(
            f"🎯 <b>بدء تشغيل البوت بنجاح!</b>\n\n"
            f"📊 البوت يعمل الآن 24 ساعة\n"
            f"🔄 صفقة كل 3 دقائق\n"
            f"⏰ الوقت الحالي: {current_time} (UTC+3)\n\n"
            f"🚀 <i>استعد لفرص ربح مستمرة!</i>"
        )
        
        # بدء أول صفقة فورية
        self.start_immediate_trade()
        
        # جدولة الصفقات المنتظمة كل 3 دقائق
        self.schedule_regular_trades()
        
        # جدولة المهام الدورية
        self.schedule_periodic_tasks()
    
    def start_immediate_trade(self):
        """بدء أول صفقة فورية"""
        try:
            now_utc3 = self.get_utc3_time()
            next_trade_time = now_utc3.replace(second=0, microsecond=0) + timedelta(minutes=1)
            time_until_trade = (next_trade_time - now_utc3).total_seconds()
            
            logging.info(f"⏰ أول صفقة بعد: {time_until_trade:.0f} ثانية - الساعة: {next_trade_time.strftime('%H:%M:%S')} (UTC+3)")
            
            threading.Timer(time_until_trade, self.execute_trade_cycle).start()
            
        except Exception as e:
            logging.error(f"❌ خطأ في الصفقة الفورية: {e}")
    
    def schedule_regular_trades(self):
        """جدولة الصفقات كل 3 دقائق بتوقيت UTC+3"""
        schedule.clear()
        
        # جدولة صفقة كل 3 دقائق على مدار 24 ساعة
        for hour in range(0, 24):
            for minute in range(0, 60, 3):
                schedule_time = f"{hour:02d}:{minute:02d}"
                schedule.every().day.at(schedule_time).do(self.execute_trade_cycle)
        
        logging.info("✅ تم جدولة الصفقات كل 3 دقائق بتوقيت UTC+3")
    
    def schedule_periodic_tasks(self):
        """جدولة المهام الدورية"""
        # الحفاظ على نشاط المتصفح كل 5 دقائق
        schedule.every(5).minutes.do(self.keep_browser_alive)
        
        # إرسال تقرير الصحة كل ساعة
        schedule.every().hour.do(self.send_health_report)
        
        logging.info("✅ تم جدولة المهام الدورية")
    
    def execute_trade_cycle(self):
        """دورة تنفيذ الصفقة الكاملة"""
        try:
            # تحديث وقت آخر نشاط
            self.stats['last_trade_time'] = self.get_utc3_time()
            
            # تحليل واتخاذ قرار
            trade_data = self.trading_engine.analyze_and_decide()
            
            # وقت التنفيذ بعد 60 ثانية
            execute_time = self.get_utc3_time() + timedelta(seconds=60)
            execute_time_str = execute_time.replace(second=0, microsecond=0).strftime("%H:%M:%S")
            
            # تخزين بيانات الصفقة
            trade_id = f"{execute_time_str}_{trade_data['pair']}_{trade_data['direction']}"
            self.pending_trades[trade_id] = {
                'data': trade_data,
                'start_time': execute_time
            }
            
            # إرسال إشارة الصفقة
            self.telegram_bot.send_trade_signal(
                trade_data['pair'],
                trade_data['direction'],
                execute_time_str
            )
            
            logging.info(f"📤 إشارة صفقة: {trade_data['pair']} - {trade_data['direction']} - {execute_time_str} (UTC+3)")
            
            # تنفيذ الصفقة بعد 60 ثانية بالضبط
            threading.Timer(60, self.start_trade_execution, [trade_id]).start()
            
        except Exception as e:
            logging.error(f"❌ خطأ في دورة الصفقة: {e}")
    
    def start_trade_execution(self, trade_id):
        """بدء تنفيذ الصفقة في المنصة"""
        try:
            if trade_id not in self.pending_trades:
                logging.error(f"❌ لم يتم العثور على الصفقة: {trade_id}")
                return
                
            trade_info = self.pending_trades[trade_id]
            trade_data = trade_info['data']
            
            # تنفيذ الصفقة في المنصة
            success = self.qx_manager.execute_trade(
                trade_data['pair'],
                trade_data['direction'],
                trade_data['duration']
            )
            
            if success:
                logging.info(f"✅ بدء صفقة في المنصة: {trade_data['pair']} - {trade_data['direction']}")
                
                # جدولة نشر النتيجة بعد 35 ثانية
                threading.Timer(35, self.publish_trade_result, [trade_id]).start()
            else:
                logging.error(f"❌ فشل تنفيذ الصفقة في المنصة: {trade_data['pair']}")
                
        except Exception as e:
            logging.error(f"❌ خطأ في تنفيذ الصفقة: {e}")
    
    def publish_trade_result(self, trade_id):
        """نشر نتيجة الصفقة"""
        try:
            if trade_id not in self.pending_trades:
                logging.error(f"❌ لم يتم العثور على الصفقة للنشر: {trade_id}")
                return
                
            trade_info = self.pending_trades[trade_id]
            trade_data = trade_info['data']
            
            # الحصول على النتيجة من المنصة
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
            
            current_time = self.get_utc3_time().strftime("%H:%M:%S")
            logging.info(f"🎯 نتيجة صفقة: {trade_data['pair']} - {result} - الوقت: {current_time} (UTC+3)")
            
            # مسح الصفقة
            del self.pending_trades[trade_id]
            
        except Exception as e:
            logging.error(f"❌ خطأ في نشر النتيجة: {e}")
    
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
    
    def run_scheduler(self):
        """تشغيل الجدولة"""
        try:
            self.start_24h_trading()
            
            logging.info("✅ بدء تشغيل الجدولة...")
            
            # حلقة التشغيل الرئيسية
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"❌ خطأ في حلقة الجدولة: {e}")
                    time.sleep(5)
                    
        except Exception as e:
            logging.error(f"❌ خطأ فادح في تشغيل الجدولة: {e}")
            # إعادة التشغيل بعد 30 ثانية
            logging.info("🔄 إعادة تشغيل الجدولة بعد 30 ثانية...")
            time.sleep(30)
            self.run_scheduler()
