# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import utils.apscheduler
from config import TOKEN
from database.database import init_db
from handlers import handlers, payment

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()


async def set_bot_commands(bot: Bot):
    """
    Устанавливает команды для бота.

    :param bot: Экземпляр бота.
    """
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Показать список команд"),
        BotCommand(command="list", description="Список отслеживаемых товаров"),
        BotCommand(command="add", description="Добавить товар для отслеживания"),
        BotCommand(command="remove", description="Удалить товар из отслеживания"),
    ]
    await bot.set_my_commands(commands)

def main():
    # Регистрируем обработчики команд
    dp.include_router(handlers.router)
    dp.include_router(payment.router)

    # Запускаем бота
    asyncio.run(start_bot())


async def start_bot():
    """
    Тело запуска бота и важных функций.

    :return:
    """
    init_db()
    await set_bot_commands(bot)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(utils.apscheduler.update_all_prices, 'interval', hours=1, args=[bot])
    scheduler.start()  # Запуск Scheduler

    await bot.delete_webhook(drop_pending_updates=True)

    # Чтобы планировщик не завершался сразу
    try:
        # asyncio.get_event_loop().run_forever()
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
