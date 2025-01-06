# handlers.py
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from buttons.keyboards import main_menu_keyboard
from database.database import add_user, add_product, get_products, update_price
from services.wildberries import get_product_price
from states import AddProductState
from utils.regex import extract_product_id

router = Router()


# Обработчик команды добавления товара
@router.message(Command('addlink'))
async def add_product_command(message: types.Message):
    try:
        # Получаем ссылку из сообщения
        url = message.text.split(maxsplit=1)[1]

        # Извлекаем product_id из ссылки
        product_id = extract_product_id(url)

        # Добавляем товар в базу данных
        user_id = message.from_user.id
        username = message.from_user.username
        add_user(user_id, username)  # Убедимся, что пользователь есть в БД

        priceStr = get_product_price(product_id)
        price = float(priceStr)
        add_product(user_id, "Товар с Wildberries", product_id, price)

        # Проверяем текущую цену товара
        update_price(product_id)

        await message.answer("Товар успешно добавлен и проверен!")
    except IndexError:
        await message.answer("Пожалуйста, отправьте ссылку на товар после команды.")
    except ValueError as e:
        await message.answer(str(e))
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


@router.message(Command('start'))
@router.callback_query(F.data == 'start')
async def start_command(message: types.Message):
    # Добавляем пользователя в базу данных
    add_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "Привет! Я бот для отслеживания цен на Wildberries. Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command('add'))
@router.callback_query(F.data == 'add')
@router.message(F.text.lower() == "добавить товар")
async def add_product_command(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название товара, который хотите отслеживать:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddProductState.waiting_for_product_name)


@router.message(Command('process'))
@router.callback_query(F.data == 'process')
async def process_product_name(message: types.Message, state: FSMContext):
    product_name = message.text
    user_id = message.from_user.id

    # Для упрощения используем фиктивный ID товара
    product_id = hash(product_name) % 1000000

    add_product(user_id, product_name, product_id, 1000)
    await message.answer(
        f"Товар '{product_name}' добавлен в отслеживаемые.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


@router.message(Command('list'))
@router.callback_query(F.data == 'list')
@router.message(F.text.lower() == "список отслеживаемых")
async def list_products_command(message: types.Message):
    user_id = message.from_user.id
    products = get_products(user_id)

    if not products:
        await message.answer("У вас нет отслеживаемых товаров.")
    else:
        response = "Ваши отслеживаемые товары:\n\n"
        for name, product_id, price in products:
            response += f"• {name} (ID: {product_id}), стоимость сейчас - {price} рублей\n"
        await message.answer(response)
