# handlers_admin.py
import asyncio
import os
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, FSInputFile, 
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from openpyxl import Workbook

from bot_config import REAL_ADMIN_ID, get_admin_ids
from database import (
    add_movie_db, delete_movie, get_next_code, add_channel, 
    remove_channel, get_channels, get_statistics, 
    get_users_for_excel, add_admin_to_db, remove_admin_from_db, 
    get_admins_list, get_admin_logs_excel_data, get_all_users_ids
)
from keyboards import (
    admin_main_kb, cancel_kb, channel_manage_kb, 
    user_persistent_kb, admin_management_kb, ad_confirm_kb
)
from bot_states import AdminStates
from constants import *

admin_router = Router(name="admin")

async def is_admin(user_id):
    return user_id in await get_admin_ids()

# ============ 💎 PREMIUM ADMIN PANEL ============

@admin_router.message(Command("admin"))
async def admin_start(message: Message):
    if not await is_admin(message.from_user.id): return
    await message.answer(
        "💎 <b>PREMIUM ADMIN PANEL</b>\n\n"
        "Tizimni boshqarish uchun tugmalardan foydalaning. Ushbu panel orqali siz botning barcha "
        "imkoniyatlarini to'liq nazorat qilishingiz, adminlar tayinlashingiz, foydalanuvchilar "
        "statistikasini ko'rishingiz va reklama kampaniyalarini boshqarishingiz mumkin.", 
        reply_markup=admin_main_kb()
    )

@admin_router.message(F.text == ADMIN_GUIDE)
async def admin_guide(message: Message):
    if not await is_admin(message.from_user.id): return
    guide_text = (
        "📖 <b>ADMINISTRATORLAR UCHUN TO'LIQ QO'LLANMA</b>\n\n"
        "Xush kelibsiz! Bot boshqaruvini samarali tashkil etish uchun quyidagi ko'rsatmalarga amal qiling:\n\n"
        "🎥 <b>Kino qo'shish tizimi:</b>\n"
        "Kino qo'shish jarayoni to'liq avtomatlashtirilgan. Sizdan faqat video faylni yuborish "
        "va bot so'ragan ma'lumotlarni (Nomi, Tavsif, Yili, Davlati, Tili) kiritish talab etiladi. "
        "Bot ushbu ma'lumotlarni professional emojilar yordamida chizib, foydalanuvchiga yuboradi.\n\n"
        "🗑 <b>Kino o'chirish:</b>\n"
        "Agar biror kinoni o'chirmoqchi bo'lsangiz, shunchaki uning kodini yuboring. "
        "Ehtiyot bo'ling, o'chirilgan kinoni qayta tiklab bo'lmaydi!\n\n"
        "🛡 <b>Adminlar boshqaruvi:</b>\n"
        "Yangi admin qo'shish uchun uning user ID raqamini kiritishingiz kerak. "
        "<b>Super Admin</b> tizimning asosi bo'lib, u hech qachon o'chirilmaydi.\n\n"
        "📂 <b>Excel Audit va Userlar:</b>\n"
        "Bot barcha admin harakatlarini (Kim qachon kimi qo'shdi/o'chirdi) log qilib boradi. "
        "Excel Audit tugmasi orqali ushbu loglarni batafsil yuklab olishingiz mumkin.\n\n"
        "📢 <b>Reklama Tarqatish:</b>\n"
        "Reklama tugmasini bosganingizda, bot sizdan fayl turini va tasdiqlashingizni so'raydi. "
        "Yuborish yakunlangach, muvaffaqiyatli va xato yuborilgan xabarlar haqida batafsil hisobot olasiz."
    )
    await message.answer(guide_text)

@admin_router.message(F.text == CLOSE_ADMIN)
async def admin_close(message: Message):
    if not await is_admin(message.from_user.id): return
    await message.answer("🔐 Admin sessiyasi yopildi.", reply_markup=ReplyKeyboardRemove())
    await message.answer("🎬 Foydalanuvchi menyusi faollashtirildi.", reply_markup=user_persistent_kb())

@admin_router.message(F.text == CANCEL_ACTION)
async def cancel(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await state.clear()
    await message.answer("⚠️ Jarayon administrator tomonidan bekor qilindi.", reply_markup=admin_main_kb())

# ============ ADMINLARNI BOSHQARISH ============

@admin_router.message(F.text == MANAGE_ADMINS)
async def admin_manage_menu(message: Message):
    if not await is_admin(message.from_user.id): return
    await message.answer("👮 <b>Adminlarni boshqarish tizimi:</b>", reply_markup=admin_management_kb())

@admin_router.callback_query(F.data == "admin_back_to_main")
async def go_back_admin(cb: CallbackQuery):
    await cb.message.edit_text("💎 <b>PREMIUM ADMIN PANEL</b>")
    await cb.answer()

@admin_router.callback_query(F.data == "admin_add")
async def admin_add_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("➕ <b>Yangi adminning Telegram ID sini yuboring:</b>", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_for_new_admin_id)
    await cb.answer()

@admin_router.message(AdminStates.waiting_for_new_admin_id)
async def admin_add_process(message: Message, state: FSMContext):
    try:
        new_id = int(message.text.strip())
        await add_admin_to_db(new_id, message.from_user.id)
        await get_admin_ids(force_update=True)
        performer = message.from_user.username or message.from_user.first_name
        await message.answer(f"✅ ID: <code>{new_id}</code> admin etib tayinlandi!\n👤 [{performer}] tomonidan qo'shildi.", reply_markup=admin_main_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Xato! Iltimos, faqat raqamli ID yuboring.")

@admin_router.callback_query(F.data == "admin_remove")
async def admin_remove_start(cb: CallbackQuery):
    admins = await get_admins_list()
    btns = []
    for aid in admins:
        if aid == REAL_ADMIN_ID: continue
        btns.append([InlineKeyboardButton(text=f"👤 Admin ID: {aid}", callback_data=f"del_adm_{aid}")])
    
    if not btns:
        return await cb.answer("Bazadan o'chirilishi mumkin bo'lgan adminlar topilmadi.", show_alert=True)
        
    btns.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back_to_main")])
    await cb.message.edit_text("🗑 <b>O'chiriladigan administratorni tanlang:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
    await cb.answer()

@admin_router.callback_query(F.data.startswith("del_adm_"))
async def admin_remove_finish(cb: CallbackQuery):
    target_id = int(cb.data.replace("del_adm_", ""))
    if target_id == REAL_ADMIN_ID:
        return await cb.answer("Xatolik: Super Admin o'chirib bo'lmaydi!", show_alert=True)
    
    await remove_admin_from_db(target_id, cb.from_user.id)
    await get_admin_ids(force_update=True)
    
    admin_info = cb.from_user.username or cb.from_user.first_name
    await cb.message.edit_text(f"🚫 <b>{target_id}</b> id li admin o'chirildi\n👤 [{admin_info}] tomonidan.")
    await cb.answer("Admin muvaffaqiyatli o'chirildi.", show_alert=True)

@admin_router.callback_query(F.data == "admin_logs_excel")
async def admin_logs_excel(cb: CallbackQuery):
    await cb.answer("📂 Audit hisoboti tayyorlanmoqda...")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Admin Audit"
    ws.append(["Admin ID", "Admin Ismi/User", "Harakat", "Bajaruvchi", "Vaqt"])
    
    logs = await get_admin_logs_excel_data()
    for row in logs:
        ws.append(list(row))
        
    fname = f"Audit_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
    wb.save(fname)
    await cb.message.answer_document(FSInputFile(fname), caption="📁 <b>Admin qo'shish va o'chirish tarixi (Audit Log).</b>")
    os.remove(fname)

# ============ KINO QO'SHISH PROCESS ============

@admin_router.message(F.text == ADD_MOVIE)
async def add_movie_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("🎥 <b>Kino faylini yuboring (Video):</b>", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_for_movie_file)

@admin_router.message(AdminStates.waiting_for_movie_file)
async def process_movie_file(message: Message, state: FSMContext):
    fid = None
    ftype = "video"
    if message.video: fid = message.video.file_id
    elif message.document and "video" in (message.document.mime_type or ""): 
        fid = message.document.file_id
        ftype = "document"
    
    if not fid:
        return await message.answer("⚠️ Iltimos, faqat video fayl yuboring!")
        
    await state.update_data(fid=fid, ftype=ftype)
    await message.answer("🎬 <b>Kino nomini kiriting:</b>")
    await state.set_state(AdminStates.waiting_for_movie_name)

@admin_router.message(AdminStates.waiting_for_movie_name)
async def process_movie_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📝 <b>Kino tavsifini (matnli ma'lumot) kiriting:</b>")
    await state.set_state(AdminStates.waiting_for_movie_desc_text)

@admin_router.message(AdminStates.waiting_for_movie_desc_text)
async def process_movie_desc(message: Message, state: FSMContext):
    await state.update_data(movie_desc=message.text.strip())
    await message.answer("🎥 <b>Kino olingan yilini kiriting:</b>")
    await state.set_state(AdminStates.waiting_for_movie_year)

@admin_router.message(AdminStates.waiting_for_movie_year)
async def process_movie_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text.strip())
    await message.answer("🌐 <b>Olingan davlatini kiriting:</b>")
    await state.set_state(AdminStates.waiting_for_movie_country)

@admin_router.message(AdminStates.waiting_for_movie_country)
async def process_movie_country(message: Message, state: FSMContext):
    await state.update_data(country=message.text.strip())
    await message.answer("📺 <b>Kino tilini kiriting:</b>")
    await state.set_state(AdminStates.waiting_for_movie_lang)

@admin_router.message(AdminStates.waiting_for_movie_lang)
async def process_movie_lang(message: Message, state: FSMContext):
    await state.update_data(lang=message.text.strip())
    code = await get_next_code()
    await message.answer(f"🔢 <b>Kino uchun kod kiriting:</b>\n(Taklif: <code>{code}</code>)")
    await state.set_state(AdminStates.waiting_for_movie_code)

@admin_router.message(AdminStates.waiting_for_movie_code)
async def process_movie_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    code = message.text.strip()
    
    final_desc = (
        f"🎬 <b>{data['name']}</b>\n"
        f"📝 {data['movie_desc']}\n"
        f"🎥 {data['year']}\n"
        f"🌐 {data['country']}\n"
        f"📺 {data['lang']}"
    )
    
    await add_movie_db(code, data['fid'], data['ftype'], final_desc, data['name'], data['year'], data['country'], data['lang'], message.from_user.id)
    
    await message.answer(f"✅ <b>Kino saqlandi!</b>\n\n{final_desc}\n\n📀 Kod: <code>{code}</code>", reply_markup=admin_main_kb())
    await state.clear()

@admin_router.message(F.text == DELETE_MOVIE)
async def movie_delete_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("🗑 <b>O'chiriladigan kino kodini yuboring:</b>", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_for_delete_code)

@admin_router.message(AdminStates.waiting_for_delete_code)
async def movie_delete_process(message: Message, state: FSMContext):
    code = message.text.strip()
    if await delete_movie(code):
        await message.answer(f"✅ <b>{code}</b> kodli kino o'chirildi.", reply_markup=admin_main_kb())
    else:
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi.", reply_markup=admin_main_kb())
    await state.clear()

# ============ 📢 REKLAMA TARQATISH ============

@admin_router.message(F.text == BROADCAST_AD)
async def ad_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("❓ <b>Reklama uchun fayl (rasm/video) yoki matn yuboring:</b>", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_for_broadcast_content)

@admin_router.message(AdminStates.waiting_for_broadcast_content)
async def ad_content(message: Message, state: FSMContext):
    await state.update_data(mid=message.message_id, cid=message.chat.id)
    await message.answer("❓ <b>Yuborishni tasdiqlaysizmi?</b>", reply_markup=ad_confirm_kb())

@admin_router.callback_query(F.data == "ad_confirm_yes")
async def ad_yes(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    uids = await get_all_users_ids()
    
    total = len(uids)
    await cb.message.edit_text(f"⏳ <b>Taqsimot jarayoni bajarilmoqda...</b> (Jami: {total})")
    
    asyncio.create_task(send_broadcast(bot, cb.message, uids, data['cid'], data['mid']))
    await cb.answer("Reklama yuborish boshlandi!")
    await state.clear()

async def send_broadcast(bot: Bot, status_msg: Message, uids, from_chat_id, message_id):
    success, fail = 0, 0
    total = len(uids)
    
    for i, uid in enumerate(uids):
        try:
            await bot.copy_message(uid, from_chat_id, message_id)
            success += 1
        except Exception:
            fail += 1
        
        if (i+1) % 100 == 0:
            try: await status_msg.edit_text(f"⏳ Yuborilmoqda: {i+1}/{total}...")
            except: pass
            
        await asyncio.sleep(0.05)
            
    result_text = (
        "📢 <b>Reklama yuborish yakunlandi!</b>\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Muvaffaqiyatsiz: {fail}\n"
        f"📊 Jami: {total}"
    )
    await status_msg.answer(result_text, reply_markup=admin_main_kb())

@admin_router.callback_query(F.data == "ad_confirm_no")
async def ad_no(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Reklama bekor qilindi.")
    await state.clear()
    await cb.answer()

# ============ STATISTIKA & EXCEL ============

@admin_router.message(F.text == STATISTICS)
async def stats(message: Message):
    if not await is_admin(message.from_user.id): return
    s = await get_statistics()
    await message.answer(f"📊 <b>BOT STATISTIKASI:</b>\n\n👤 Userlar: {s['total_users']}\n🎬 Kinolar: {s['total_movies']}\n👮 Adminlar: {s['total_admins']}")

@admin_router.message(F.text == EXCEL_USERS)
async def excel_users(message: Message):
    if not await is_admin(message.from_user.id): return
    users = await get_users_for_excel()
    wb = Workbook(); ws = wb.active; ws.append(["Username", "Ism", "ID", "Vaqt", "Search"])
    for u in users: ws.append(list(u))
    fname = "users.xlsx"; wb.save(fname)
    await message.answer_document(FSInputFile(fname), caption="📂 Foydalanuvchilar ro'yxati."); os.remove(fname)

# ============ 📣 KANALLAR NAZORATI ============

@admin_router.message(F.text == MANAGE_CHANNELS)
async def channel_menu(message: Message):
    if not await is_admin(message.from_user.id): return
    channels = await get_channels()
    text = "📣 <b>MAJBURIY OBUNA KANALLARI:</b>\n\n"
    if channels:
        for i, ch in enumerate(channels, 1): text += f"{i}. {ch}\n"
    else: text += "Kanallar yo'q."
    await message.answer(text, reply_markup=channel_manage_kb())

@admin_router.callback_query(F.data == "channel_add")
async def channel_add_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("🔗 <b>Yangi kanalning username'ini yuboring (Masalan: @kanal_nomi):</b>", reply_markup=cancel_kb())
    await state.set_state(AdminStates.waiting_for_channel_add)
    await cb.answer()

@admin_router.message(AdminStates.waiting_for_channel_add)
async def channel_add_process(message: Message, state: FSMContext):
    ch = message.text.strip()
    if not ch.startswith("@"): ch = "@" + ch
    await add_channel(ch)
    await message.answer(f"✅ {ch} majburiy obuna ro'yxatiga qo'shildi.", reply_markup=admin_main_kb())
    await state.clear()

@admin_router.callback_query(F.data == "channel_remove")
async def channel_remove_start(cb: CallbackQuery):
    channels = await get_channels()
    if not channels:
        return await cb.answer("O'chirish uchun kanallar mavjud emas.", show_alert=True)
    
    btns = [[InlineKeyboardButton(text=f"❌ {ch}", callback_data=f"rm_ch_{ch}")] for ch in channels]
    btns.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="channel_back")])
    
    await cb.message.edit_text("🗑 <b>O'chirmoqchi bo'lgan kanalingizni tanlang:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
    await cb.answer()

@admin_router.callback_query(F.data.startswith("rm_ch_"))
async def channel_remove_finish(cb: CallbackQuery):
    channel = cb.data.replace("rm_ch_", "")
    await remove_channel(channel)
    await cb.answer(f"{channel} o'chirildi.", show_alert=True)
    
    # Reload menu
    channels = await get_channels()
    if channels:
        btns = [[InlineKeyboardButton(text=f"❌ {ch}", callback_data=f"rm_ch_{ch}")] for ch in channels]
        btns.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="channel_back")])
        await cb.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
    else:
        await cb.message.edit_text("📣 Kanallar ro'yxati bo'shatildi.")

@admin_router.callback_query(F.data == "channel_back")
async def channel_back(cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer()
