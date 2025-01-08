import asyncio

from aiogram import Bot

import database.queries
from database.queries import get_all_products
from services.wildberries import get_product_price

async def update_all_prices(bot: Bot):
    try:
        products = get_all_products()  # Получаем список всех отслеживаемых товаров
        for product in products:
            user_id, product_id, product_name = product.user_id, product.product_id, product.product_name

            # Получаем текущую цену товара (используем вашу функцию запроса цены)
            current_price = get_product_price(product_id)

            # Получаем последнюю цену
            last_price = product.price

            if last_price is not None and abs(current_price - last_price) >= 1:
                # Если разница больше 1 рубля, отправляем сообщение пользователю
                text = f"На товар '{product_name}' изменена цена! Новая цена: {current_price} руб.\nСтарая цена: {last_price} руб."
                await bot.send_message(
                    chat_id=user_id,
                    text=text
                )
                print(f'Send!!{text}')

            # Добавляем новую цену в историю
            database.queries.update_price(product_id)
    except Exception as e:
        print(e)