# handlers.py
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from buttons.keyboards import main_menu_keyboard
from database.database import add_user, add_product, get_products, update_price, delete_product, get_product_details, \
    get_price_history
from services.wildberries import get_product_price, get_photo_image, get_product
from states import AddProductState
from utils.regex import extract_product_id

router = Router()


@router.message(Command('addlink'))
@router.message(AddProductState.waiting_for_product_name)
@router.message(F.text.lower() == "добавить товар")
async def add_product_command(message: types.Message, state: FSMContext):
    """
    Обработчик команды добавления товара

    :param message:
    :return:
    """
    try:
        text = message.text.split(maxsplit=1)

        # Получаем ссылку из сообщения
        if len(text) == 2:
            url = text[1]
        else:
            url = text[0]

        # Извлекаем product_id из ссылки
        product_id = extract_product_id(url)

        # Добавляем товар в базу данных
        user_id = message.from_user.id
        username = message.from_user.username
        add_user(user_id, username)  # Убедимся, что пользователь есть в БД

        product = get_product(product_id)
        priceStr = get_product_price(product_id)
        price = float(priceStr)
        add_product(user_id, product.get('name', "Товар с Wildberries"), product_id, price)

        # Проверяем текущую цену товара
        update_price(product_id)

        await state.clear()
        await message.answer("Товар успешно добавлен и проверен!")
    except IndexError:
        await state.set_state(AddProductState.waiting_for_product_name)
        await message.answer("Пожалуйста, отправьте ссылку на товар после команды.")
    except ValueError as e:
        await message.answer(str(e))
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


@router.message(Command("help"))
@router.callback_query(F.data == 'help')
@router.message(F.text.lower() == "помощь")
async def help_command(message: types.Message):
    await message.answer(
        "Этот бот позволяет смотреть изменения цен на товары Wildberries, и уведомлять, если цена слишком сильно изменилась.\n"
        "Это позволяет купить товар со скидкой, или, например, до сильного подорожания.\n"
        "Просто пришлите ссылку - и посмотрите, как это работает!"
    )


@router.message(Command('start'))
@router.callback_query(F.data == 'start')
@router.message(F.text.lower() == "старт")
async def start_command(message: types.Message):
    """
    Стартовая команда бота.

    :param message:
    :return:
    """
    # Добавляем пользователя в базу данных
    add_user(message.from_user.id, message.from_user.username)

    await message.reply(
        "Привет! Я бот для отслеживания цен на Wildberries. Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command('add'))
@router.callback_query(F.data == 'add')
@router.message(F.text.lower() == "добавить товар")
async def add_product_command(message: types.Message, state: FSMContext):
    """
    Команда добавления товара. Использует FSM

    :param message:
    :param state:
    :return:
    """
    await message.answer(
        "Введите название товара, который хотите отслеживать:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddProductState.waiting_for_product_name)


@router.message(Command('process'))
@router.callback_query(F.data == 'process')
async def process_product_name(message: types.Message, state: FSMContext):
    """
    Команда - обработчик работы с товаром.

    :param message:
    :param state:
    :return:
    """

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
    """
    Команда для отслеживания списка товаров.

    :param message:
    :return:
    """
    user_id = message.from_user.id
    products = get_products(user_id)

    if not products:
        await message.answer("У вас нет отслеживаемых товаров.")
    else:
        # Создаём кнопки
        keyboard = InlineKeyboardBuilder()

        response = "Ваши отслеживаемые товары:\n\n"
        for name, product_id, price in products:
            response += (
                f"📦 <b>{name}</b>\n"
                f"🔢 ID: {product_id}\n"
                f"💰 Текущая цена: {price} руб.\n\n"
            )

            keyboard.button(
                text=f"Просмотреть {name}",
                callback_data=f"view_item {product_id}"
            )

        await message.answer(response, reply_markup=keyboard.as_markup(), parse_mode='HTML')


@router.message(Command('view_item'))
@router.callback_query(F.data == 'view_item')
@router.message(F.text.lower() == "посмотреть товар")
async def view_item_command(message: types.Message):
    # Извлекаем идентификатор товара из сообщения
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Пожалуйста, укажите идентификатор товара. Пример: /view_item 123456")
        return

    product_id = args[1]

    # Получаем данные товара
    name, id = get_product_details(product_id)
    if not id:
        await message.reply("Товар с таким идентификатором не найден.")
        return

    # Извлекаем историю цен
    price_history = get_price_history(product_id)

    # Формируем сообщение
    history_text = "\n".join([f"{timestamp}: {price} руб." for timestamp, price in price_history])
    if not history_text:
        history_text = "История цен отсутствует."

    message_text = (
        f"📦 <b>{name}</b>\n"
        f"🔗 <a href='https://www.wildberries.ru/catalog/{id}/detail.aspx'>Ссылка на товар</a>\n\n"
        f"📊 <b>История цен:</b>\n{history_text}"
    )

    photoUrl = get_photo_image(product_id)

    if photoUrl is None:
        await message.reply(
            text=message_text,
            parse_mode="HTML"
        )

    else:
        # Отправляем изображение и сообщение
        await message.reply_photo(
            photo=photoUrl,
            caption=message_text,
            parse_mode="HTML"
        )


@router.message(Command('remove_item'))
@router.callback_query(F.data == 'remove_item')
@router.message(F.text.lower() == "удалить товар")
async def remove_item_command(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Пожалуйста, укажите идентификатор товара. Пример: /remove_item 123456")
        return

    product_id = args[1]

    # Удаляем товар из базы данных
    delete_product(message.from_user.id, product_id)

    await message.reply(f"Товар с идентификатором {product_id} был удалён из мониторинга.")
