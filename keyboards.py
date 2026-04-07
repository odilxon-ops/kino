# keyboards.py
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from constants import *

# ============ FOYDALANUVCHI KEYBOARDLARI ============

def user_initial_kb():
    """Faqat birinchi marta start berganda chiqadigan Inline menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=SEARCH_MOVIE, callback_data="search_movie")],
        [
            InlineKeyboardButton(text=POPULAR_MOVIES, callback_data="popular"),
            InlineKeyboardButton(text=RANDOM_MOVIE, callback_data="random")
        ],
        [
            InlineKeyboardButton(text=MY_FAVORITES, callback_data="favorites"),
            InlineKeyboardButton(text=CONTACT_ADMIN, callback_data="contact")
        ],
        [InlineKeyboardButton(text=AD_REQUEST, callback_data="user_ad_request")]
    ])

def user_persistent_kb():
    """Doimiy Keyboard (Matnli tugmalar)"""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=SEARCH_MOVIE), KeyboardButton(text=POPULAR_MOVIES)],
        [KeyboardButton(text=RANDOM_MOVIE), KeyboardButton(text=MY_FAVORITES)],
        [KeyboardButton(text=CONTACT_ADMIN), KeyboardButton(text=AD_REQUEST)]
    ], resize_keyboard=True)

# ============ ADMIN KEYBOARDLARI ============

def admin_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_MOVIE), KeyboardButton(text=DELETE_MOVIE)],
            [KeyboardButton(text=STATISTICS), KeyboardButton(text=EXCEL_USERS)],
            [KeyboardButton(text=MANAGE_ADMINS), KeyboardButton(text=BROADCAST_AD)],
            [KeyboardButton(text=MANAGE_CHANNELS), KeyboardButton(text=ADMIN_GUIDE)],
            [KeyboardButton(text=CLOSE_ADMIN)]
        ],
        resize_keyboard=True
    )

def admin_management_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add")],
        [InlineKeyboardButton(text="➖ Admin o'chirish", callback_data="admin_remove")],
        [InlineKeyboardButton(text="📂 Excel (Audit Log)", callback_data="admin_logs_excel")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back_to_main")]
    ])

def ad_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha", callback_data="ad_confirm_yes"),
         InlineKeyboardButton(text="❌ Yo'q", callback_data="ad_confirm_no")]
    ])

# ============ YORDAMCHI TUGMALAR ============

def cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=CANCEL_ACTION)]], resize_keyboard=True)

def channel_manage_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Qo'shish", callback_data="channel_add"),
         InlineKeyboardButton(text="➖ O'chirish", callback_data="channel_remove")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="channel_back")]
    ])

def subscription_check_kb(channels: list):
    btns = [[InlineKeyboardButton(text=f"➡️ {ch}", url=f"https://t.me/{ch.lstrip('@')}")] for ch in channels]
    btns.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def movie_action_kb(code: str, is_fav: bool):
    text = "💔 Sevimlilardan o'chirish" if is_fav else "❤️ Sevimlilarga qo'shish"
    data = f"fav_rem_{code}" if is_fav else f"fav_add_{code}"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data)]])

def favorites_list_kb(favs: list):
    btns = []
    for code, desc in favs:
        name = (desc or "Kino").split('\n')[0][:25]
        btns.append([
            InlineKeyboardButton(text=f"🎬 {name}", callback_data=f"show_m_{code}"),
            InlineKeyboardButton(text="🗑", callback_data=f"fav_rem_{code}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def popular_list_kb(movies: list):
    btns = []
    for code, desc, count in movies:
        name = (desc or "Kino").split('\n')[0][:25]
        btns.append([InlineKeyboardButton(text=f"{name} ({count} 🔍)", callback_data=f"show_m_{code}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)
