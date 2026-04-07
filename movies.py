# handlers/movie.py
from aiogram import Router
from aiogram.types import Message

from database import get_movie

router = Router(name="movie")


@router.message()
async def handle_movie_code(message: Message):
    code = message.text.strip()

    movie = get_movie(code)

    if movie:
        link, description = movie
        text = description.strip() if description else "Kino topildi!"
        await message.answer(f"{text}\n\nLink: {link}")
    else:
        await message.answer("Bunday kod mavjud emas 😔")