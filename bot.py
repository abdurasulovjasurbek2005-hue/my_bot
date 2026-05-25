import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update, URLInputFile
from aiogram.filters import CommandStart
from aiohttp import web, ClientSession

# --- SOZLAMALAR ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "") 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Deezer ochiq API manzili
DEEZER_API_URL = "https://api.deezer.com/search"

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        f"Salom {message.from_user.full_name}!\n"
        "Men ochiq API orqali ishlaydigan tezkor ashula botman. 🎶\n"
        "Menga qo'shiq nomi yoki ijrochini yozib yuboring!"
    )

@dp.message(F.text)
async def search_and_send_music(message: Message):
    search_query = message.text
    status_message = await message.answer("🔍 Qo'shiq qidirilmoqda...")

    try:
        # aiohttp orqali Deezer API-ga so'rov yuboramiz
        async with ClientSession() as session:
            params = {"q": search_query, "limit": 1} # Eng birinchi chiqqan aniq natijani olamiz
            async with session.get(DEEZER_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Agar biror narsa topilsa
                    if data.get("data") and len(data["data"]) > 0:
                        track = data["data"][0]
                        
                        title = track.get("title")
                        artist = track.get("artist", {}).get("name")
                        audio_url = track.get("preview") # Tayyor .mp3 havola (30 soniyalik sifatli preview yoki to'liq)
                        album_cover = track.get("album", {}).get("cover_medium")

                        if audio_url:
                            await status_message.edit_text("🚀 Qo'shiq topildi! Telegramga uzatilmoqda...")
                            
                            # Serverga yuklamasdan, to'g'ridan-to'g'ri havola orqali audio yuborish
                            audio = URLInputFile(audio_url, filename=f"{artist} - {title}.mp3")
                            
                            await message.answer_audio(
                                audio=audio,
                                caption=f"🎶 **{artist} — {title}**\n\n📌 @{bot.username} orqali topildi.",
                                thumbnail=URLInputFile(album_cover) if album_cover else None,
                                parse_mode="Markdown"
                            )
                            await status_message.delete()
                        else:
                            await status_message.edit_text("😔 Afsuski, qo'shiqning audio fayli topilmadi.")
                    else:
                        await status_message.edit_text("😔 Hech narsa topilmadi. Boshqa nom yozib ko'ring.")
                else:
                    await status_message.edit_text("❌ API serverda xatolik yuz berdi.")

    except Exception as e:
        print(f"Xatolik: {e}")
        await status_message.edit_text("❌ Qo'shiqni qidirishda texnik xatolik yuz berdi.")

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
    
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()