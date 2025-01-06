# handlers.py
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from buttons.keyboards import main_menu_keyboard
from database.database import add_user, add_product, get_products
from states import AddProductState

router = Router()


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

    add_product(user_id, product_name, product_id)
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
        for name, product_id in products:
            response += f"• {name} (ID: {product_id})\n"
        await message.answer(response)
