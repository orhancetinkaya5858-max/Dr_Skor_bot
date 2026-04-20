import os
import json
import threading
import asyncio
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask

# 1. Flask
app = Flask(__name__)
@app.route('/')
def home(): return "Bot aktif!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# 2. Ayarlar
API_TOKEN = os.environ.get('BOT_TOKEN')
GROUP_ID = -100123456789 # KENDİ ID'N
DATA_FILE = "data.json"
TZ = pytz.timezone("Europe/Istanbul")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Scheduler'ı burada tanımla ama BAŞLATMA
scheduler = AsyncIOScheduler(timezone=TZ)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": {}, "last_report_date": datetime.now(TZ).strftime("%Y-%m-%d")}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

async def send_daily_report():
    data = load_data()
    users = data.get("users", {})
    if not users: return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1]['daily'], reverse=True)
    msg = f"📊 **GÜNLÜK SMS RAPORU** ({datetime.now(TZ).strftime('%d.%m.%Y')})\n\n"
    for uid, info in sorted_users:
        msg += f"{info['name']}: {info['daily']}\n"
    
    await bot.send_message(GROUP_ID, msg + "\nBu gecelik bu kadar.")
    
    for uid in users: users[uid]['daily'] = 0
    data["last_report_date"] = datetime.now(TZ).strftime("%Y-%m-%d")
    save_data(data)

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def count_messages(message: types.Message):
    data = load_data()
    current_date = datetime.now(TZ).strftime("%Y-%m-%d")
    if data.get("last_report_date") != current_date:
        await send_daily_report()
        data = load_data()

    uid = str(message.from_user.id)
    name = message.from_user.first_name or "İsimsiz"
    if uid not in data["users"]: data["users"][uid] = {"name": name, "daily": 0}
    data["users"][uid]["daily"] += 1
    save_data(data)

# 3. İŞTE BURASI: Hata Çözümü
async def on_startup(dp):
    loop = asyncio.get_event_loop() # Aktif olan döngüyü yakala
    scheduler.configure(event_loop=loop) # Zamanlayıcıyı bu döngüye kilitle
    scheduler.add_job(send_daily_report, 'cron', hour=0, minute=0)
    scheduler.start()
    print("Bot ve Zamanlayıcı başarıyla bağlandı!")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
