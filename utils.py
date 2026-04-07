# utils.py
import logging
from aiogram import Bot

from database import get_channels

logger = logging.getLogger(__name__)

async def check_all_subscriptions(bot: Bot, user_id: int) -> bool:
    """Barcha majburiy kanallarga obunani tekshirish"""
    channels = await get_channels()
    if not channels:
        return True

    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            # Faqat ushbu statusdagilar obuna bo'lgan hisoblanadi
            if member.status not in ["creator", "administrator", "member", "restricted"]:
                return False
        except Exception as e:
            # Agar bot kanal admini bo'lmasa yoki kanal topilmasa:
            logger.error(f"Subscription check critical error ({channel}): {e}")
            # Xavfsizlik uchun: agar bot tekshira olmasa, bu kanalni o'tkazib yubormaymiz (False qaytaramiz)
            # Ya'ni bot kanalga admin bo'lishi shart!
            return False
            
    return True