# handlers_user.py
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    get_movie, get_top_weekly_movies, get_random_movie, get_user_favorites, 
    add_favorite, remove_favorite, is_favorite, increment_movie_search, 
    increment_user_search, set_user_old
)
from keyboards import (
    user_initial_kb, user_persistent_kb, movie_action_kb, 
    favorites_list_kb, popular_list_kb
)
from bot_states import UserStates
from constants import *

user_router = Router(name="user")

# ============ KINO QIDIRUV LOGIKASI ============

async def movie_search_engine(message: Message, bot: Bot, code: str):
    """Professional kino qidirish logikasi"""
    # 1. Tugmalar matnini qidiruvdan chiqarib tashlaymiz
    if code in ALL_BUTTON_TEXTS: return

    # OBUNA TEKSHIRUVI ENDI MIDDLEWARE-DA! BU YERGA KELGAN HAR BIR ODAM OBUNA BO'LGAN.

    movie = await get_movie(code)
    if movie:
        fid, ftype, desc = movie
        await increment_movie_search(code)
        await increment_user_search(message.from_user.id)
        
        is_fav = await is_favorite(message.from_user.id, code)
        caption = f"🎬 <b>KINO TOPILDI!</b>\n\n{desc}\n\n📀 <b>Kod:</b> <code>{code}</code>"
        
        try:
            if ftype == "video":
                await bot.send_video(message.chat.id, fid, caption=caption, reply_markup=movie_action_kb(code, is_fav))
            else:
                await bot.send_document(message.chat.id, fid, caption=caption, reply_markup=movie_action_kb(code, is_fav))
            await set_user_old(message.from_user.id)
        except Exception as e:
            import logging
            logging.error(f"Error sending movie {code}: {e}")
            await message.answer(f"⚠️ Texnik xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
    else:
        if len(code) < 15:
            await message.answer(f"😔 Kechirasiz, <b>{code}</b> kodli kino topilmadi.\n<i>Kodni to'g'ri kiritganingizni tekshiring.</i>")

# ============ FOYDALANUVCHI HANDLERLARI ============

@user_router.message(F.text == SEARCH_MOVIE)
@user_router.callback_query(F.data == "search_movie")
async def search_handler(event: Message | CallbackQuery, state: FSMContext):
    text = "🔍 <b>Kino kodini yuboring (Masalan: 121):</b>"
    if isinstance(event, Message): await event.answer(text)
    else: 
        await event.message.answer(text); 
        await event.answer()
    await state.set_state(UserStates.waiting_for_code)

@user_router.message(F.text == POPULAR_MOVIES)
@user_router.callback_query(F.data == "popular")
async def popular_handler(event: Message | CallbackQuery, bot: Bot):
    # OBUNA TEKSHIRUVI MIDDLEWARE-DA (Hamma handlerlar uchun)
    movies = await get_top_weekly_movies(3)
    if not movies:
        text = "🔥 Hozircha trendlar bo'sh. Kinolar ko'p qidirilsa, shu yerda chiqadi!"
        if isinstance(event, Message): await event.answer(text)
        else: await event.message.answer(text); await event.answer()
        return

    text = "🔥 <b>HAFTALIK TOP 3 MASHHUR KINOLAR:</b>"
    kb = popular_list_kb(movies)
    if isinstance(event, Message): await event.answer(text, reply_markup=kb)
    else: await event.message.answer(text, reply_markup=kb); await event.answer()

@user_router.message(F.text == RANDOM_MOVIE)
@user_router.callback_query(F.data == "random")
async def random_handler(event: Message | CallbackQuery, bot: Bot):
    m = await get_random_movie()
    if m:
        code, fid, ftype, desc = m
        is_fav = await is_favorite(event.from_user.id, code)
        caption = f"🎲 <b>TASODIFIY TANLOV:</b>\n\n{desc}\n\n📀 <b>Kod:</b> <code>{code}</code>"
        cid = event.chat.id if isinstance(event, Message) else event.message.chat.id
        if ftype == "video": await bot.send_video(cid, fid, caption=caption, reply_markup=movie_action_kb(code, is_fav))
        else: await bot.send_document(cid, fid, caption=caption, reply_markup=movie_action_kb(code, is_fav))
    if isinstance(event, CallbackQuery): await event.answer()

@user_router.message(F.text == MY_FAVORITES)
@user_router.callback_query(F.data == "favorites")
async def fav_handler(event: Message | CallbackQuery):
    favs = await get_user_favorites(event.from_user.id)
    if not favs:
        text = "❤️ Sizning sevimlilar ro'yxatingiz bo'sh."
        if isinstance(event, Message): await event.answer(text)
        else: await event.answer(text, show_alert=True)
        return
    text = "❤️ <b>SEVIMLILAR:</b>"
    kb = favorites_list_kb(favs)
    if isinstance(event, Message): await event.answer(text, reply_markup=kb)
    else: await event.message.answer(text, reply_markup=kb); await event.answer()

@user_router.message(F.text == CONTACT_ADMIN)
@user_router.callback_query(F.data == "contact")
async def contact_handler(event: Message | CallbackQuery):
    text = "📞 <b>Admin bilan bog'lanish:</b> @sunat_dev\n⚡️ Reklama va takliflar uchun ochiqmiz."
    if isinstance(event, Message): await event.answer(text)
    else: await event.message.answer(text); await event.answer()

# ============ REKLAMA (USER SIDE) ============

@user_router.message(F.text == AD_REQUEST)
@user_router.callback_query(F.data == "user_ad_request")
async def user_ad_request(event: Message | CallbackQuery):
    text = (
        "📢 <b>REKLAMA XIZMATI</b>\n\n"
        "O'z reklamangizni bizning botda joylashtirmoqchimisiz? "
        "Auditoriyamiz juda faol va reklamangizni minglab odamlar ko'radi.\n\n"
        "🤝 Bog'lanish: @sunat_dev"
    )
    if isinstance(event, Message): await event.answer(text)
    else: 
        await event.message.answer(text, reply_markup=user_persistent_kb())
        await set_user_old(event.from_user.id)
        await event.answer()

# ============ GLOBAL HANDLING ============

@user_router.message(UserStates.waiting_for_code)
async def state_code_handler(message: Message, state: FSMContext, bot: Bot):
    await movie_search_engine(message, bot, message.text.strip())
    await state.clear()

@user_router.message(F.text)
async def global_text_handler(message: Message, bot: Bot):
    if message.text.startswith('/'): return
    await movie_search_engine(message, bot, message.text.strip())

# ============ CALLBACK LOGIC ============

@user_router.callback_query(F.data.startswith("show_m_"))
async def show_movie_handler(cb: CallbackQuery, bot: Bot):
    code = cb.data.replace("show_m_", "")
    await movie_search_engine(cb.message, bot, code)
    await cb.answer()

@user_router.callback_query(F.data.startswith("fav_add_"))
async def add_fav_cb(cb: CallbackQuery):
    code = cb.data.replace("fav_add_", "")
    await add_favorite(cb.from_user.id, code)
    await cb.message.edit_reply_markup(reply_markup=movie_action_kb(code, True))
    await cb.answer("❤️ Sevimlilarga qo'shildi.")

@user_router.callback_query(F.data.startswith("fav_rem_"))
async def rem_fav_cb(cb: CallbackQuery):
    code = cb.data.replace("fav_rem_", "")
    await remove_favorite(cb.from_user.id, code)
    await cb.message.edit_reply_markup(reply_markup=movie_action_kb(code, False))
    await cb.answer("💔 O'chirildi.")
