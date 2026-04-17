import os
import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from datetime import datetime

# Tokeni gizli tutmak için Render ayarlarından alacağız
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Verileri tutmak için geçici sözlük
stats = {}

def get_rank(count):
    if count < 100: return "Tıp Öğrencisi 🎓"
    if count < 500: return "Stajyer Doktor 🩺"
    if count < 2000: return "Uzman Doktor 👨‍⚕️"
    if count < 5000: return "Doçent 🔬"
    if count < 10000: return "Profesör 🏛️"
    return "Başhekim 👑"

@dp.message_handler(commands=['skorum', 'profil', 'skor'])
async def my_stats(message: types.Message):
    uid = message.from_user.id
    if uid in stats:
        data = stats[uid]
        rank = get_rank(data['m'])
        await message.reply(f"📊 **{data['name']} Analiz Raporu**\n\n"
                           f"🔹 Günlük: {data['d']}\n"
                           f"🔹 Haftalık: {data['w']}\n"
                           f"🔹 Aylık: {data['m']}\n"
                           f"🩺 Unvan: {rank}")
    else:
        await message.reply("Henüz bir reçeteniz yok Doktor! Mesaj yazarak başlayın.")

@dp.message_handler()
async def count_messages(message: types.Message):
    if message.chat.type == 'private': return
    uid = message.from_user.id
    if uid not in stats:
        stats[uid] = {"name": message.from_user.full_name, "d": 0, "w": 0, "m": 0, "chat_id": message.chat.id}
    
    stats[uid]["d"] += 1
    stats[uid]["w"] += 1
    stats[uid]["m"] += 1

async def send_report(period_key, title):
    if not stats: return
    
    # Skorları sırala
    sorted_users = sorted(stats.items(), key=lambda x: x[1][period_key], reverse=True)[:10]
    
    report_text = f"📋 **{title}**\n\n"
    target_chat = None
    
    for i, (uid, data) in enumerate(sorted_users, 1):
        rank = get_rank(data[period_key])
        report_text += f"{i}. {data['name']} - {data[period_key]} Mesaj\n   ┗ 💉 {rank}\n"
        target_chat = data["chat_id"]
        
        # Günlük rapor sonrası günlük sayacı sıfırla
        if period_key == "d": data["d"] = 0
        # Haftalık sonrası haftalık sayacı sıfırla
        if period_key == "w": data["w"] = 0
    
    if target_chat:
        await bot.send_message(target_chat, report_text)

async def scheduler():
    # Her gün 00:00'da günlük rapor
    aioschedule.every().day.at("00:00").do(send_report, "d", "Günün Reçetesi")
    
    while True:
        # Pazar günü haftalık rapor ekle
        if datetime.now().weekday() == 6 and datetime.now().strftime("%H:%M") == "23:59":
            await send_report("w", "Haftalık Check-up")
        
        # Ayın 30'u veya son günü aylık rapor
        if datetime.now().day == 30 and datetime.now().strftime("%H:%M") == "23:58":
            await send_report("m", "Aylık Sağlık Raporu")
            
        await aioschedule.run_pending()
        await asyncio.sleep(60)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
