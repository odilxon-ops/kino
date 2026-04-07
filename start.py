# start.py
from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from database import add_user, is_user_new, set_user_old
from keyboards import user_initial_kb, user_persistent_kb
from utils import check_all_subscriptions

start_router = Router(name="start")

@start_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user = message.from_user
    # Bazaga qo'shish (Majburiy)
    await add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Obuna tekshiruvi endi Middleware orqali avtomatik bajariladi!
    # Shuning uchun bu yerga kelgan foydalanuvchi allaqachon obuna bo'lgan.

    new_flag = await is_user_new(user.id)
    welcome_text = (
        f"🌟 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
        "🎬 <b>Professional Kino Qidiruv Botiga xush kelibsiz!</b>\n\n"
        "Siz bu yerda eng so'nggi filmlarni, mashhur seriallarni va eng sara "
        "kino asarlarini professional sifatda topishingiz mumkin.\n\n"
        "🚀 <b>Botdan qanday foydalanish mumkin?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔎 <b>Kino qidirish:</b> Menyu orqali kino kodini yuboring.\n"
        "🔥 <b>Trenddagilar:</b> Haftaning eng sara TOP 3 ta kinosini ko'ring.\n"
        "❤️ <b>Shaxsiy kutubxona:</b> Yoqqan kinolarni sevimlilarga qo'shing.\n\n"
        "👇 <i>Davom etish uchun quyidagi menyuni tanlang:</i>"
    )

    if new_flag:
        await message.answer(welcome_text, reply_markup=user_initial_kb())
    else:
        await message.answer(welcome_text, reply_markup=user_persistent_kb())

@start_router.callback_query(F.data == "check_subs")
async def check_subs(cb: CallbackQuery, bot: Bot):
    # Bu handler faqat "Obunani tekshirish" tugmasi bosilganda ishlaydi. 
    # Middleware bu eventni o'tkazib yuboradi, shuning uchun bu yerda tekshiramiz.
    if await check_all_subscriptions(bot, cb.from_user.id):
        await cb.message.delete()
        await cb.message.answer(
            f"✅ <b>Obuna tasdiqlandi!</b>\n\nFoydalanuvchi menyusi faollashtirildi. "
            f"Assalomu alaykum <b>{cb.from_user.first_name}</b>, bot xizmatlaridan to'liq foydalanishingiz mumkin!", 
            reply_markup=user_persistent_kb()
        )
        await set_user_old(cb.from_user.id)
    else:
        await cb.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)