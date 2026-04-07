# send_messages.py
from database import get_all_users


async def send_to_all(message):
    """Barcha foydalanuvchilarga xabar yuborish"""
    users = get_all_users()
    for user_id in users:
        try:
            await message.copy_to(user_id)
        except Exception:
            pass