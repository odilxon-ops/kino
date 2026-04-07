# bot_channels.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_channels


async def check_subscription(bot, user_id, channel):
    try:
        member = await bot.get_chat_member(channel, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


def channels_keyboard(channels):
    buttons = []
    for channel in channels:
        buttons.append([
            InlineKeyboardButton(text=channel, url=f"https://t.me/{channel[1:]}")
        ])
    buttons.append([
        InlineKeyboardButton(text="Tekshirish", callback_data="check_subs")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)