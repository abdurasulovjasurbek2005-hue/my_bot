import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update, URLInputFile
from aiogram.filters import CommandStart
from aiohttp import web, ClientSession

# --- SOZLAMALAR ---
# Tokenni kod ichiga yozmaymiz, uni Render muhitidan (Environment Variables) xavfsiz o'qib oladi
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Render taqdim etadigan tashqi URL manzil
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "") 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Deezer ochiq va bepul API manzili
DEEZER_API_URL = "https://api.deezer.com/search"

# /start buyrug'i uchun handler
@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        f"Salom {message.from_user.full_name}!\n"
        "Men ochiq API orqali ishlaydigan tezkor ashula botman. 🎶\n"
        "Menga qo'shiq nomi yoki ijrochini yozib yuboring, men uni topib beraman!"
    )

# Foydalanuvchi matn yuborganda API orqali ashula qidirish va yuborish
@dp.message(F.text)
async def search_and_send_music(message: Message):
    search_query = message.text
    status_message = await message.answer("🔍 Qo'shiq qidirilmoqda...")

    try:
        # aiohttp orqali Deezer API-ga asinxron so'rov yuboramiz
        async with ClientSession() as session:
            params = {"q": search_query, "limit": 1}  # Eng birinchi chiqqan eng mos natijani olamiz
            async with session.get(DEEZER_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Agar biror narsa topilsa
                    if data.get("data") and len(data["data"]) > 0:
                        track = data["data"][0]
                        
                        title = track.get("title")
                        artist = track.get("artist", {}).get("name")
                        audio_url = track.get("preview")  # Sifatli mp3 audio havola
                        album_cover = track.get("album", {}).get("cover_medium")

                        if audio_url:
                            await status_message.edit_text("🚀 Ashula topildi! Telegramga uzatilmoqda...")
                            
                            # Serverga yuklamasdan, to'g'ridan-to'g'ri havola (URL) orqali audio yuborish
                            audio = URLInputFile(audio_url, filename=f"{artist} - {title}.mp3")
                            
                            await message.answer_audio(
                                audio=audio,
                                caption=f"🎶 **{artist} — {title}**\n\n📌 @{bot.username} orqali topildi.",
                                thumbnail=URLInputFile(album_cover) if album_cover else None,
                                parse_mode="Markdown"
                            )
                            # Status xabarini o'chiramiz
                            await status_message.delete()
                        else:
                            await status_message.edit_text("😔 Afsuski, qo'shiqning audio fayli topilmadi.")
                    else:
                        await status_message.edit_text("😔 Hech narsa topilmadi. Boshqa nom yozib ko'ring.")
                else:
                    await status_message.edit_text("❌ API serverda xatolik yuz berdi. Birozdan so'ng urunib ko'ring.")

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await status_message.edit_text("❌ Qo'shiqni qidirishda texnik xatolik yuz berdi.")

# --- WEB SERVER QISMI (RENDER UCHUN WEBHOOK) ---
async def handle_webhook(request):
    try:
        json_data = await request.json()
        update = Update.model_validate(json_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"Webhook error: {e}")
    return web.Response()

async def on_startup(app):
    # Dastur ishga tushganda botning usernamesini yuklab olamiz
    bot_info = await bot.get_me()
    bot.username = bot_info.username
    
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
    
    # Render muhit taqdim etadigan PORT orqali ishlaydi
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()