# bot_states.py
from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    waiting_for_code = State()

class AdminStates(StatesGroup):
    # Kino qo'shish jarayoni (Talab bo'yicha bosqichlar)
    waiting_for_movie_file = State()
    waiting_for_movie_name = State()
    waiting_for_movie_desc_text = State() 
    waiting_for_movie_year = State()
    waiting_for_movie_country = State()
    waiting_for_movie_lang = State()
    waiting_for_movie_code = State()
    
    # Kino o'chirish
    waiting_for_delete_code = State()
    
    # Admin qo'shish
    waiting_for_new_admin_id = State()
    
    # Reklama yuborish
    waiting_for_broadcast_content = State()
    
    # Kanallar
    waiting_for_channel_add = State()