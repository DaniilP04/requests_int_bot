import asyncio, os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from app.database import db
from app.handlers import router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    await db.connect()
    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("delete_webhook warn:", e)

    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())