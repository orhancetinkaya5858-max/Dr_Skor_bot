import os
import json
import threading
import asyncio
import pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

# Flask (Botu ayakta tutmak için)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# Ayarlar
API_TOKEN = os.environ.get('BOT_TOKEN')
GROUP_ID = -100123456789 # KENDİ GRUP ID'Nİ BURAYA YAZ
DATA_FILE = "data.json"
TZ = pytz.timezone("Europe/Istanbul")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Scheduler'ı ana sistemden bağımsız başlatan sistem
scheduler = BackgroundScheduler(timezone=TZ)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# Raporlama Fonksiyonu
async def reset_counts(period_type):
    data = load_data()
    if not data: return
    
    msg = f"📊 **{period_type.upper()} SMS RAPORU**\n\n"
    for uid, info in data.items():
        msg += f"{info.get('name', 'İsimsiz')}: {info.get(period_type, 0)}\n"
    
    try:
        await bot.send_message(GROUP_ID, msg)
        # Sıfırlama
        for uid in data: data[uid][period_type] = 0
        save_data(data)
    except Exception as e:
        print(f"Rapor gönderilemedi: {e}")

# Thread'ler arası köprü (Zamanlayıcıdan botu güvenle yönetmek için)
def job_daily(): asyncio.run_coroutine_threadsafe(reset_counts("daily"), bot.loop)
def job_weekly(): asyncio.run_coroutine_threadsafe(reset_counts("weekly"), bot.loop)
def job_monthly(): asyncio.run_coroutine_threadsafe(reset_counts("monthly"), bot.loop)

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def count_messages(message: types.Message):
    data = load_data()
    uid = str(message.from_user.id)
    name = message.from_user.first_name or "İsimsiz"
    
    if uid not in data:
        data[uid] = {"name": name, "daily": 0, "weekly": 0, "monthly": 0}
    
    data[uid]["daily"] += 1
    data[uid]["weekly"] += 1
    data[uid]["monthly"] += 1
    save_data(data)

if __name__ == '__main__':
    # Scheduler'ı burada başlatıyoruz
    scheduler.add_job(job_daily, 'cron', hour=0, minute=0)
    scheduler.add_job(job_weekly, 'cron', day_of_week='mon', hour=0, minute=0)
    scheduler.add_job(job_monthly, 'cron', day=1, hour=0, minute=0)
    scheduler.start()
    
    threading.Thread(target=run_flask).start()
    executor.start_polling(dp, skip_updates=True)
