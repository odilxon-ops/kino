# bot_config.py
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Haqiqiy Admin (Hech qachon o'chirilmaydi)
REAL_ADMIN_ID = int(os.getenv("REAL_ADMIN_ID", 7566796449))

# Kesh uchun o'zgaruvchilar
_admin_cache = set()
_last_cache_update = 0

async def get_admin_ids(force_update=False):
    """Barcha adminlarni kesh bilan qaytaradi"""
    global _admin_cache, _last_cache_update
    
    current_time = asyncio.get_event_loop().time()
    
    # 5 minutda bir marta yoki majburiy bo'lganda yangilash
    if force_update or not _admin_cache or (current_time - _last_cache_update > 300):
        from database import get_all_admins
        db_admins = await get_all_admins()
        
        all_admins = {REAL_ADMIN_ID}
        for aid in db_admins:
            all_admins.add(aid)
            
        env_admins = os.getenv("ADMIN_IDS", "")
        if env_admins:
            for i in env_admins.split(","):
                if i.strip():
                    all_admins.add(int(i.strip()))
        
        _admin_cache = all_admins
        _last_cache_update = current_time
                
    return list(_admin_cache)