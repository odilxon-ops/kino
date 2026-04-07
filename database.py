# database.py
import aiosqlite
import logging
from pathlib import Path
from datetime import datetime

DB_PATH = Path("kino_bot.db")

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_logs.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. users jadvali
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_new INTEGER DEFAULT 1,
            search_count INTEGER DEFAULT 0
        )''')

        # Robust Migration for users
        try:
            await db.execute("SELECT is_new FROM users LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE users ADD COLUMN is_new INTEGER DEFAULT 1")
        
        try:
            await db.execute("SELECT search_count FROM users LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE users ADD COLUMN search_count INTEGER DEFAULT 0")

        # 2. movies jadvali
        await db.execute('''CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL DEFAULT 'video',
            description TEXT,
            name TEXT,
            year TEXT,
            country TEXT,
            language TEXT,
            search_count INTEGER DEFAULT 0,
            search_count_weekly INTEGER DEFAULT 0,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            added_by INTEGER
        )''')

        # Robust Migration for movies
        try:
            await db.execute("SELECT search_count_weekly FROM movies LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE movies ADD COLUMN search_count_weekly INTEGER DEFAULT 0")
        
        try:
            await db.execute("SELECT name FROM movies LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE movies ADD COLUMN name TEXT")
            await db.execute("ALTER TABLE movies ADD COLUMN year TEXT")
            await db.execute("ALTER TABLE movies ADD COLUMN country TEXT")
            await db.execute("ALTER TABLE movies ADD COLUMN language TEXT")

        # 3. favorites jadvali
        await db.execute('''CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            movie_code TEXT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, movie_code)
        )''')

        # 4. channels jadvali
        await db.execute('''CREATE TABLE IF NOT EXISTS channels (
            channel TEXT PRIMARY KEY
        )''')

        # 5. admins jadvali
        await db.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            added_by INTEGER,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        try:
            await db.execute("SELECT added_by FROM admins LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE admins ADD COLUMN added_by INTEGER")

        # 6. admin_logs jadvali
        await db.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            performed_by INTEGER NOT NULL,
            action_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        await db.commit()
    logger.info("Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi.")

# ============ ADMIN FUNCTIONS ============

async def add_admin_to_db(user_id: int, added_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO admins (user_id, added_by) VALUES (?, ?)", (user_id, added_by))
        await db.execute("INSERT INTO admin_logs (admin_id, action_type, performed_by) VALUES (?, ?, ?)", 
                  (user_id, 'qo\'shildi', added_by))
        await db.commit()

async def remove_admin_from_db(user_id: int, performed_by: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.execute("INSERT INTO admin_logs (admin_id, action_type, performed_by) VALUES (?, ?, ?)", 
                  (user_id, 'o\'chirildi', performed_by))
        await db.commit()

async def get_admins_list():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM admins") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_all_admins():
    return await get_admins_list()

async def get_admin_logs_excel_data():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT l.admin_id, 
                   COALESCE(u1.first_name, 'No Name') || ' (' || COALESCE(u1.username, 'No User') || ')',
                   l.action_type, 
                   COALESCE(u2.first_name, 'No Name'),
                   l.action_at 
            FROM admin_logs l
            LEFT JOIN users u1 ON l.admin_id = u1.user_id
            LEFT JOIN users u2 ON l.performed_by = u2.user_id
            ORDER BY l.action_at DESC
        """) as cursor:
            return await cursor.fetchall()

# ============ USER FUNCTIONS ============

async def add_user(user_id, username, first_name, last_name=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name) 
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        await db.commit()

async def is_user_new(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_new FROM users WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            return res[0] == 1 if res else True

async def set_user_old(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_new = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_users_for_excel():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT username, first_name, user_id, joined_at, search_count FROM users") as cursor:
            return await cursor.fetchall()

async def get_all_users_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

# ============ MOVIE FUNCTIONS ============

async def add_movie_db(code, file_id, file_type, description, name, year, country, language, added_by):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO movies (code, file_id, file_type, description, name, year, country, language, added_by) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, file_id, file_type, description, name, year, country, language, added_by))
        await db.commit()

async def get_movie(code):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT file_id, file_type, description FROM movies WHERE code = ?", (code,)) as cursor:
            return await cursor.fetchone()

async def delete_movie(code) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("DELETE FROM movies WHERE code = ?", (code,)) as cursor:
            await db.commit()
            return cursor.rowcount > 0

async def get_next_code() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        # ORDER BY orqali eng oxirgi kodni topish (Professionalroq)
        async with db.execute("SELECT code FROM movies WHERE code GLOB '[0-9]*' ORDER BY CAST(code AS INTEGER) DESC LIMIT 1") as cursor:
            res = await cursor.fetchone()
            res_val = res[0] if res else None
            return (int(res_val) if res_val else 0) + 1

async def increment_movie_search(code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET search_count = search_count + 1, search_count_weekly = search_count_weekly + 1 WHERE code = ?", (code,))
        await db.commit()

async def increment_user_search(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET search_count = search_count + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_top_weekly_movies(limit=3):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code, description, search_count_weekly FROM movies ORDER BY search_count_weekly DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

async def get_random_movie():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code, file_id, file_type, description FROM movies ORDER BY RANDOM() LIMIT 1") as cursor:
            return await cursor.fetchone()

async def reset_weekly_searches():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET search_count_weekly = 0")
        await db.commit()
        logger.info("Haftalik statistika tozalandi.")

# ============ FAVORITES ============

async def add_favorite(user_id, movie_code):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO favorites (user_id, movie_code) VALUES (?, ?)", (user_id, movie_code))
            await db.commit()
            return True
        except: return False

async def remove_favorite(user_id, movie_code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM favorites WHERE user_id = ? AND movie_code = ?", (user_id, movie_code))
        await db.commit()

async def is_favorite(user_id, movie_code):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM favorites WHERE user_id = ? AND movie_code = ?", (user_id, movie_code)) as cursor:
            res = await cursor.fetchone()
            return res is not None

async def get_user_favorites(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT m.code, m.description FROM favorites f JOIN movies m ON f.movie_code = m.code WHERE f.user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

# ============ CHANNELS ============

async def add_channel(channel: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO channels (channel) VALUES (?)", (channel,))
        await db.commit()

async def remove_channel(channel: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE channel = ?", (channel,))
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT channel FROM channels") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_statistics():
    from bot_config import get_admin_ids
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM movies") as c2:
            total_movies = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM channels") as c3:
            total_channels = (await c3.fetchone())[0]
        
        return {
            "total_users": total_users,
            "total_movies": total_movies,
            "total_channels": total_channels,
            "total_admins": len(await get_admin_ids())
        }