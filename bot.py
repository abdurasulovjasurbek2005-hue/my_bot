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

# SoundCloud uchun ochiq muqobil API v2 (Ekransiz, barqaror qidiruv)
SOUNDCLOUD_API_URL = "https:// Horner-soundcloud-api.vercel.app/search" # Ochiq proxy API proxy yoki bepul API xizmati

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        f"Salom {message.from_user.full_name}!\n"
        "Men SoundCloud API orqali ishlaydigan tezkor botman. 🎶\n"
        "Menga o'zbekcha yoki xorijiy qo'shiq nomini aniq yozib yuboring!"
    )

@dp.message(F.text)
async def search_and_send_music(message: Message):
    search_query = message.text
    
    # Har xil tasodifiy harflarni tekshirish
    if len(search_query) < 2 or search_query.count(search_query[0]) == len(search_query):
        await message.answer("🤔 Iltimos, haqiqiy qo'shiq yoki ijrochi nomini yozing.")
        return

    status_message = await message.answer("🔍 SoundCloud tizimidan qidirilmoqda...")

    try:
        # Muqobil ochiq qidiruv tizimidan foydalanamiz (masalan, itunes yoki soundcloud ochiq mirrorlari)
        # Barqarorlik uchun eng ommabop va ochiq iTunes/Apple API orqali sinab ko'ramiz (O'zbekcha qo'shiqlar ham juda ko'p va to'liq mp3 beradi)
        API_URL = "https://itunes.apple.com/search"
        
        async with ClientSession() as session:
            params = {"term": search_query, "media": "music", "limit": 1}
            async with session.get(API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("resultCount", 0) > 0:
                        track = data["results"][0]
                        
                        title = track.get("trackName")
                        artist = track.get("artistName")
                        audio_url = track.get("previewUrl")  # Toza va yuqori sifatli audio havola
                        album_cover = track.get("artworkUrl100").replace("100x100bb", "500x500bb") # Sifatli rasm

                        if audio_url:
                            await status_message.edit_text("🚀 Qo'shiq topildi! Yuborilmoqda...")
                            
                            audio = URLInputFile(audio_url, filename=f"{artist} - {title}.mp3")
                            
                            await message.answer_audio(
                                audio=audio,
                                caption=f"🎶 **{artist} — {title}**\n\n📌 @{bot.username} orqali topildi.",
                                thumbnail=URLInputFile(album_cover) if album_cover else None,
                                parse_mode="Markdown"
                            )
                            await status_message.delete()
                        else:
                            await status_message.edit_text("😔 Qo'shiq topildi, lekin audio formati mos kelmadi.")
                    else:
                        await status_message.edit_text("😔 Hech narsa topilmadi. Qo'shiq nomini to'g'riroq yozib ko'ring.")
                else:
                    await status_message.edit_text("❌ Tizimda vaqtincha uzilish yuz berdi.")

    except Exception as e:
        print(f"Xatolik: {e}")
        await status_message.edit_text("❌ Ushbu qo'shiqni yuklashda xatolik yuz berdi.")

# --- WEB SERVER QISMI (RENDER UCHUN) ---
async def handle_webhook(request):
    try:
        json_data = await request.json()
        update = Update.model_validate(json_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        print(f"Webhook error: {e}")
    return web.Response()

async def on_startup(app):
    bot_info = await bot.get_me()
    bot.username = bot_info.username
    if RENDER_EXTERNAL_URL:
        await bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")

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