import logging
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, executor, types

# 1. Flask Ayarları (Render'ın portu görmesi için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Bot Ayarları
API_TOKEN = os.environ.get('BOT_TOKEN') # Render'da 'Environment' kısmındaki isimle aynı olmalı
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 3. Komutlar
@dp.message_handler(commands=['skor'])
async def skor_komutu(message: types.Message):
    # Buraya kendi analiz mantığını ekleyebilirsin
    await message.reply("📊 **Kişisel Analiz**\n\n🔹 Günlük: 5\n🔹 Toplam: 5")

# 4. Ana Çalıştırma Bloğu
if __name__ == '__main__':
    # Flask'ı arka planda başlat
    threading.Thread(target=run_flask).start()
    
    # Botu başlat (skip_updates=True çakışmayı önler)
    print("Bot başlatılıyor...")
    executor.start_polling(dp, skip_updates=True)
