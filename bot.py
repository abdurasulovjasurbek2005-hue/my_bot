import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, Update
from aiogram.filters import CommandStart
from yt_dlp import YoutubeDL
from aiohttp import web

# --- SOZLAMALAR ---
BOT_TOKEN = "8936241092:AAHL4PnXKmWP6ARJUoR6MmxDunO7dlOsgyY"

# Render sizga taqdim etadigan URL (Buni Render guruhida olasiz, pastda tushuntirilgan)
# Masalan: https://ashula-bot.onrender.com
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "") 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'quiet': True
}

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        f"Salom {message.from_user.full_name}!\n"
        "Men Renderda ishlayotgan ashula botman. 🎶\n"
        "Menga qo'shiq nomini yozib yuboring!"
    )

@dp.message(F.text)
async def search_and_send_music(message: Message):
    search_query = message.text
    status_message = await message.answer("🔍 Qo'shiq qidirilmoqda, iltimos kuting...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        loop = asyncio.get_event_loop()
        def download():
            with YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)
                if 'entries' in info and len(info['entries']) > 0:
                    return ydl.prepare_filename(info['entries'][0])
                return None

        file_path = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            await status_message.edit_text("🚀 Ashula topildi! Yuklanmoqda...")
            audio_file = FSInputFile(file_path)
            await message.answer_audio(audio=audio_file, caption="🎶 Ashula bot orqali topildi.")
            await status_message.delete()
            os.remove(file_path)
        else:
            await status_message.edit_text("😔 Afsuski, bunday qo'shiq topilmadi.")
    except Exception as e:
        print(f"Xatolik: {e}")
        await status_message.edit_text("❌ Yuklashda xatolik yuz berdi.")

# --- WEB SERVER QISMI (RENDER UCHUN) ---
async def handle_webhook(request):
    json_data = await request.json()
    update = Update.model_validate(json_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return web.Response()

async def on_startup(app):
    if RENDER_EXTERNAL_URL:
        await bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")
        print(f"Webhook o'rnatildi: {RENDER_EXTERNAL_URL}/webhook")

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Render avtomatik beradigan PORT da ishga tushadi
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()