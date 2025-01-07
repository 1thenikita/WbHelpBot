import os
from datetime import timedelta, datetime

from aiogram import types, Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import PAY_TOKEN
from database.database import update_subscription, get_user_subscription

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

    await message.answer_invoice(
        title="Подписка на бота",
        description="Активация подписки на бота на 1 месяц",
        provider_token=PAYMENTS_TOKEN,
        currency="rub",
        # TODO фото подписки добавить
        # photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
        # photo_width=416,
        # photo_height=234,
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
        message: types.Message
):
    """
    Обработчик успешной оплаты.

    :param message: Объект сообщения.
    :return:
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"📊В статистику",
        callback_data="stats"
    )
    builder.button(
        text="🏠В начало",
        callback_data="start"
    )
    builder.adjust(1)

    try:
        telegram_id = message.from_user.id
        now = datetime.utcnow()

        # Получаем текущий статус подписки
        user_subscription = get_user_subscription(telegram_id)

        if not user_subscription:
            await message.answer("Пользователь не найден в системе.")
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
        await message.reply(
            f"🎉 Благодарим за оплату!\n\n🔑 Ваша подписка действует до {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}.\n\nПриятного пользования!",
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
