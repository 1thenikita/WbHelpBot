# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher

import utils.apscheduler
from config import TOKEN
from database.database import update_all_prices
from handlers import handlers, payment

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

def main():
    # Регистрируем обработчики команд
    dp.include_router(handlers.router)
    dp.include_router(payment.router)

    # Запускаем бота
    asyncio.run(start_bot())

async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    main()