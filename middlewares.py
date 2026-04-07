# middlewares.py
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from utils import check_all_subscriptions
from database import get_channels
from keyboards import subscription_check_kb
from bot_config import get_admin_ids

class MandatorySubMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        bot = data['bot']
        
        # 1. Adminlarni tekshiruvdan o'tkazib yuboramiz
        admin_ids = await get_admin_ids()
        if user_id in admin_ids:
            return await handler(event, data)
        
        # 2. Keyfiyatni buzmaslik uchun ba'zi holatlarni o'tkazib yuboramiz
        # Masalan: "check_subs" tugmasini bosganda tekshiruv o'zi ishlaydi
        if isinstance(event, CallbackQuery) and event.data == "check_subs":
            return await handler(event, data)
            
        # 3. Obunani tekshirish
        if not await check_all_subscriptions(bot, user_id):
            text = "🛑 <b>DIQQAT!</b> Botdan foydalanish uchun rasmiy kanallarimizga obuna bo'ling:"
            channels = await get_channels()
            kb = subscription_check_kb(channels)
            
            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb)
            else:
                await event.message.answer(text, reply_markup=kb)
                await event.answer()
            return # Handler ishga tushmaydi!
            
        # 4. Agar obuna bo'lgan bo'lsa, handlerga yo'l beramiz
        return await handler(event, data)
