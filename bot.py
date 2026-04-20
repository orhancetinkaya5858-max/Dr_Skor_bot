import os
import json
import threading
import asyncio
import pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

# 1. Flask (Render ayakta tutma)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# 2. Ayarlar
API_TOKEN = os.environ.get('BOT_TOKEN')
GROUP_ID = -100123456789 # KENDİ GRUP ID'Nİ YAZ
DATA_FILE = "data.json"
TZ = pytz.timezone("Europe/Istanbul")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Scheduler'ı bağımsız başlatan sistem
scheduler = BackgroundScheduler(timezone=TZ)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {"users": {}, "last_report_date": datetime.now(TZ).strftime("%Y-%m-%d")}
    return {"users": {}, "last_report_date": datetime.now(TZ).strftime("%Y-%m-%d")}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# Asenkron raporlama fonksiyonu
async def send_daily_report():
    data = load_data()
    users = data.get("users", {})
    if not users: return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]['daily'], reverse=True)
    msg = f"📊 **GÜNLÜK SMS RAPORU** ({datetime.now(TZ).strftime('%d.%m.%Y')})\n\n"
    for uid, info in sorted_users:
        msg += f"{info['name']}: {info['daily']}\n"
    
    try:
        await bot.send_message(GROUP_ID, msg + "\nBu gecelik bu kadar.")
    except Exception as e:
        print(f"Mesaj gönderilemedi: {e}")
    
    # Sıfırlama
    for uid in users: users[uid]['daily'] = 0
    data["last_report_date"] = datetime.now(TZ).strftime("%Y-%m-%d")
    save_data(data)

# Zamanlayıcı için köprü (Thread güvenli)
def job_wrapper():
    asyncio.run_coroutine_threadsafe(send_daily_report(), bot.loop)

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def count_messages(message: types.Message):
    data = load_data()
    current_date = datetime.now(TZ).strftime("%Y-%m-%d")
    
    # Günlük kontrol
    if data.get("last_report_date") != current_date:
        await send_daily_report()
        data = load_data()

    uid = str(message.from_user.id)
    name = message.from_user.first_name or "İsimsiz"
    
    if uid not in data["users"]: data["users"][uid] = {"name": name, "daily": 0}
    data["users"][uid]["daily"] += 1
    save_data(data)

if __name__ == '__main__':
    # Scheduler'ı burada başlatıyoruz
    scheduler.add_job(job_wrapper, 'cron', hour=0, minute=0)
    scheduler.start()
    
    threading.Thread(target=run_flask).start()
    executor.start_polling(dp, skip_updates=True)
