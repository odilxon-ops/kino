# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

from bot_config import BOT_TOKEN
from database import init_db, reset_weekly_searches
from start import start_router
from handlers_admin import admin_router
from handlers_user import user_router
from middlewares import MandatorySubMiddleware

async def main():
    # Bazani asinxron ishga tushirish
    await init_db()
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    # QAT'IY OUTER MIDDLEWARE (Filtrlardan ham oldin ishlaydi!)
    # Bu orqali foydalanuvchi obuna bo'lmasa, handlerlar umuman o'qilmaydi.
    dp.message.outer_middleware(MandatorySubMiddleware())
    dp.callback_query.outer_middleware(MandatorySubMiddleware())
    
    # Routerlarni qo'shish
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(user_router)
    
    # Haftalik statistika tozalash
    scheduler = AsyncIOScheduler(timezone=timezone('Asia/Tashkent'))
    scheduler.add_job(reset_weekly_searches, 'cron', day_of_week='mon', hour=0)
    scheduler.start()
    
    print("🚀 Bot MULTI-STRICT OUTER-MIDDLEWARE rejimida ishlayapti...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
