import os
from datetime import timedelta, datetime

from aiogram import types, Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import PAY_TOKEN
from database.queries import update_subscription, get_user_subscription

router = Router()
PAYMENTS_TOKEN = PAY_TOKEN


# Покупка подписки
@router.message(Command("buy"))
@router.callback_query(F.data == "buy")
async def buy_command(message: types.Message, command: CommandObject):
    """
    Команда покупки подписки.

    :param message:
    :param command:
    :return:
    """

    # Если это команда /donate ЧИСЛО,
    # тогда вытаскиваем число из текста команды
    if command.command != "buy":
        amount = int(command.command.split("_")[1])
    # В противном случае пытаемся парсить пользовательский ввод
    else:
        # Проверка на число и на его диапазон
        if (
                command.args is None
                or not command.args.isdigit()
                or not 1 <= int(command.args) <= 2500
        ):
            amount = 100
        else:
            amount = int(command.args)

    PRICE = LabeledPrice(label="Подписка на 1 месяц", amount=amount * 100)  # в копейках (руб)

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Оплатить {amount} рублей",
        pay=True
    )
    builder.button(
        text="Отменить покупку",
        callback_data="cancel"
    )
    builder.adjust(1)

    await message.reply_invoice(
        title="Подписка на бота",
        description="Активация подписки на бота на 1 месяц\nПозволяет добавлять больше товаров, поддерживать разработчика на новые функции и не только",
        provider_token=PAYMENTS_TOKEN,
        currency="rub",
        # TODO фото подписки добавить
        photo_url="https://static35.tgcnt.ru/posts/_0/a4/a4efcb9d0c3c4febd65362e692cd57fb.jpg",
        photo_width=640,
        photo_height=640,
        # photo_size=416,
        is_flexible=False,
        prices=[PRICE],
        start_parameter="one-month-subscription",
        payload="test-invoice-payload",
        reply_markup=builder.as_markup())


@router.pre_checkout_query()
async def on_pre_checkout_query(
        pre_checkout_query: types.PreCheckoutQuery,
):
    """
    Обработка пред оплаты - проверка на возможность оплаты

    :param pre_checkout_query:
    :return:
    """
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def on_successful_payment(
        callbackQuery: types.CallbackQuery
):
    """
    Обработчик успешной оплаты.

    :param callbackQuery: Объект сообщения.
    :return:
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"📊В товары",
        callback_data="list"
    )
    builder.button(
        text="🏠В начало",
        callback_data="start"
    )
    builder.adjust(1)

    try:
        telegram_id = callbackQuery.from_user.id
        now = datetime.now()

        # Получаем текущий статус подписки
        user_subscription = get_user_subscription(telegram_id)

        if not user_subscription:
            await callbackQuery.message.reply("Пользователь не найден в системе.")
            return

        subscription_status, subscription_expiry = user_subscription

        # Продлеваем или активируем подписку
        if subscription_status == 'active' and subscription_expiry:
            # Увеличиваем срок подписки
            expiry_date = datetime.strptime(subscription_expiry, '%Y-%m-%d %H:%M:%S') + timedelta(days=30)
        else:
            # Активируем новую подписку
            expiry_date = now + timedelta(days=30)

        update_subscription(telegram_id, 'active', expiry_date)

        # Отправляем сообщение пользователю
        await callbackQuery.message.reply(
            f"🎉 Благодарим за оплату!\n\n🔑 Ваша подписка действует до {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}.\n\nПриятного пользования!",
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        await callbackQuery.message.reply(f"Произошла ошибка: {e}")
