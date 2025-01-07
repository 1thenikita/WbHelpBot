import asyncio

from aiogram import Bot

from database.database import update_all_prices, get_products, get_last_price, add_price_history, get_all_products
from services.wildberries import get_product_price


async def update_all_prices(bot: Bot):
    products = get_all_products()  # Получаем список всех отслеживаемых товаров
    for product in products:
        user_id, product_id, product_name = product["user_id"], product["product_id"], product["product_name"]

        # Получаем текущую цену товара (используем вашу функцию запроса цены)
        current_price = get_product_price(product_id)

        # Получаем последнюю цену из истории
        last_price = get_last_price(product_id)

        if last_price is not None and abs(current_price - last_price) >= 1:
            # Если разница больше 1 рубля, отправляем сообщение пользователю
            text = f"На товар '{product_name}' изменена цена! Новая цена: {current_price} руб.\nСтарая цена: {last_price} руб."
            await bot.send_message(
                chat_id=user_id,
                text=text
            )
            print(f'Send!!{text}')

        # Добавляем новую цену в историю
        add_price_history(product_id, current_price)