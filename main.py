import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession

from handlers.users import users
from handlers.admin import admin
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))


async def main():
    dp = Dispatcher()
    dp.include_routers(admin, users)

    # Регистрируем middleware
    # users.message.middleware(StartupMiddleware())

    try:
        await dp.start_polling(bot)  # Запускаем polling напрямую
    except KeyboardInterrupt:
        print("Бот остановлен")
    finally:
        session: BaseSession = bot.session
        await session.close()  # Гарантируем закрытие сессии


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
