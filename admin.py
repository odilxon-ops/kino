# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import add_movie, get_next_code, add_channel, get_channels
from keyboards import admin_main_kb
from states import AdminStates

router = Router(name="admin")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Sizda ruxsat yo'q")
        return

    await message.answer("Admin panel", reply_markup=admin_main_kb())


@router.message(F.text == "🎥 Kino qo'shish")
async def start_add_movie(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    next_code = get_next_code()
    await message.answer(f"Kino linkini yuboring\n\nTavsiya etilgan kod: {next_code}")
    await state.set_state(AdminStates.waiting_for_movie_link)


@router.message(AdminStates.waiting_for_movie_link)
async def process_movie_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    await message.answer("Kino kodini kiriting:")
    await state.set_state(AdminStates.waiting_for_movie_code)


@router.message(AdminStates.waiting_for_movie_code)
async def process_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()

    # Kod mavjudligini tekshirish
    if get_movie(code):
        await message.answer("Bu kod allaqachon ishlatilgan! Boshqa kod kiriting.")
        return

    await state.update_data(code=code)
    await message.answer("Kino tavsifini yuboring (nomi, yili, davlat, til va h.k.):")
    await state.set_state(AdminStates.waiting_for_movie_desc)


@router.message(AdminStates.waiting_for_movie_desc)
async def save_movie(message: Message, state: FSMContext):
    data = await state.get_data()
    add_movie(
        code=data["code"],
        link=data["link"],
        description=message.text.strip(),
        added_by=message.from_user.id
    )
    await message.answer("Kino muvaffaqiyatli qo'shildi! ✅")
    await state.clear()


@router.message(F.text == "📣 Majburiy kanallar")
async def manage_channels(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    current = "\n".join(get_channels()) or "Hozircha kanal qo'shilmagan"
    await message.answer(
        f"Hozirgi majburiy kanallar:\n{current}\n\n"
        "Yangi kanal qo'shish uchun @username formatida yuboring:"
    )
    await state.set_state(AdminStates.waiting_for_channel)


@router.message(AdminStates.waiting_for_channel)
async def add_new_channel(message: Message, state: FSMContext):
    channel = message.text.strip()
    if not channel.startswith("@"):
        await message.answer("Kanal @username formatida bo'lishi kerak")
        return

    add_channel(channel)
    await message.answer(f"Kanal qo'shildi: {channel}")
    await state.clear()

    # handlers/admin.py (qo'shimcha kodlar)

    @router.message(F.text == "📢 Reklama yuborish")
    async def start_broadcast(message: Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return

        await message.answer(
            "Reklama sifatida yubormoqchi bo'lgan xabarni yuboring\n"
            "(matn, rasm, video, hujjat, forward xabari bo'lishi mumkin)"
        )
        await state.set_state(AdminStates.waiting_for_broadcast_content)

    @router.message(AdminStates.waiting_for_broadcast_content)
    async def receive_broadcast_content(message: Message, state: FSMContext):
        # Xabarni saqlab qo'yamiz (copy qilish uchun)
        await state.update_data(
            broadcast_message_id=message.message_id,
            broadcast_chat_id=message.chat.id,
            content_type=message.content_type
        )

        preview_text = "Reklama namunasi quyidagicha bo'ladi:\n\n"

        if message.text:
            preview_text += message.text
        elif message.caption:
            preview_text += message.caption
        else:
            preview_text += f"[{message.content_type}] (matn yo'q)"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ Barchaga yuborish", callback_data="broadcast_confirm_yes"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data="broadcast_confirm_no")
            ]
        ])

        await message.answer(
            preview_text + "\n\nYuqoridagi xabarni hammaga yuborishni xohlaysizmi?",
            reply_markup=kb
        )
        await state.set_state(AdminStates.waiting_for_broadcast_confirm)

    @router.callback_query(F.data.startswith("broadcast_confirm_"))
    async def process_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
        action = callback.data.split("_")[-1]

        if action == "no":
            await callback.message.edit_text("Reklama yuborish bekor qilindi.")
            await state.clear()
            await callback.answer()
            return

        if action != "yes":
            await callback.answer()
            return

        await callback.message.edit_text("Reklama yuborilmoqda... Bu biroz vaqt olishi mumkin.")
        await callback.answer()

        data = await state.get_data()
        msg_id = data["broadcast_message_id"]
        chat_id = data["broadcast_chat_id"]

        # Barcha foydalanuvchilarni olish
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users")
            users = [row[0] for row in c.fetchall()]

        success_count = 0
        fail_count = 0

        for user_id in users:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=chat_id,
                    message_id=msg_id
                )
                success_count += 1
            except Exception as e:
                # Bot bloklangan yoki o'chirilgan bo'lsa
                fail_count += 1
                # Xohlasangiz bu user_id ni bazadan o'chirish mumkin
                # c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

        result_text = (
            f"Reklama yuborish yakunlandi!\n\n"
            f"Muvaffaqiyatli: {success_count}\n"
            f"Muvaffaqiyatsiz: {fail_count}\n"
            f"Jami: {len(users)}"
        )

        await callback.message.edit_text(result_text)
        await state.clear()

        @router.message(F.text == "📊 Statistika")
        async def show_statistics(message: Message):
            if message.from_user.id not in ADMIN_IDS:
                await message.answer("Sizda ruxsat yo'q")
                return

            stats = get_statistics()

            text = (
                "📊 <b>Bot statistikasi</b>\n\n"
                f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
                f"🆕 Oxirgi 7 kun: <b>+{stats['new_week']}</b>\n"
                f"🆕 Oxirgi 30 kun: <b>+{stats['new_month']}</b>\n\n"
                f"🎬 Bazadagi kinolar soni: <b>{stats['total_movies']}</b>\n"
                f"📣 Majburiy kanallar: <b>{stats['total_channels']}</b>\n"
                f"🛡 Adminlar soni: <b>{stats['total_admins']}</b>\n"
            )

            await message.answer(text, parse_mode="HTML")