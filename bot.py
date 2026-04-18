import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from datetime import datetime
from flask import Flask
from threading import Thread

# --- Flask (Botu ayakta tutmak için) ---
app = Flask('')
@app.route('/')
def home(): return "Dr. Skor Bot Aktif!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Veri yapısı: stats[chat_id][user_id] = {'name': ..., 'd': 0}
stats = {}

@dp.message_handler(commands=['skorum', 'profil', 'skor'])
async def my_stats(message: types.Message):
    chat_id = message.chat.id
    uid = message.from_user.id
    if chat_id in stats and uid in stats[chat_id]:
        data = stats[chat_id][uid]
        await message.reply(f"📊 **Kişisel Analiz**\n\n🔹 Günlük: {data['d']}\n🔹 Toplam: {data['m']}")
    else:
        await message.reply("Henüz veriniz bulunmuyor.")

@dp.message_handler()
async def count_messages(message: types.Message):
    if message.chat.type == 'private': return
    
    chat_id = message.chat.id
    uid = message.from_user.id
    name = message.from_user.full_name
    
    if chat_id not in stats: stats[chat_id] = {}
    if uid not in stats[chat_id]:
        stats[chat_id][uid] = {"name": name, "d": 0, "m": 0}
    
    stats[chat_id][uid]["d"] += 1
    stats[chat_id][uid]["m"] += 1

async def send_daily_report():
    for chat_id, users in stats.items():
        # Sıralama (En çok mesaj atan)
        sorted_users = sorted(users.items(), key=lambda x: x[1]['d'], reverse=True)[:15]
        
        total_msg = sum(u['d'] for u in users.values())
        active_users = len([u for u in users.values() if u['d'] > 0])
        
        report_text = "📋 **Grup Günlük Aktiflik Listesi**\n\nKullanıcı → Mesaj\n"
        for i, (uid, data) in enumerate(sorted_users, 1):
            report_text += f"{i}. {data['name']} : {data['d']}\n"
        
        report_text += f"\n📊 Bu Sıralama geçtiğimiz Güne aittir.\n├ Toplam aktif kullanıcı: {active_users}\n└ Toplam mesaj: {total_msg}"
        
        try:
            await bot.send_message(chat_id, report_text)
            # Günlük sayacı sıfırla
            for uid in users: stats[chat_id][uid]['d'] = 0
        except Exception as e:
            print(f"Rapor gönderilemedi: {e}")

async def scheduler():
    while True:
        now = datetime.now()
        # Türkiye saati 00:00 kontrolü (Basit döngü)
        if now.hour == 0 and now.minute == 0:
            await send_daily_report()
            await asyncio.sleep(65) # Bir dakika bekle ki tekrar göndermesin
        await asyncio.sleep(30)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    keep_alive()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
